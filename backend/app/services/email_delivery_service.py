"""Email delivery engine for application notifications.

This service owns SMTP delivery, retry scheduling, stale-delivery recovery,
and delivery-state updates. Application, lifecycle, event, and notification
creation remain separate from actual email delivery.
"""

from __future__ import annotations

import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.application_notification import ApplicationNotification


# Load backend/.env using the same project convention as database/connection.py.
BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
load_dotenv(os.path.join(BASE_DIR, ".env"))


EMAIL_CHANNEL = "email"

PENDING_STATUS = "pending"
SENDING_STATUS = "sending"
SENT_STATUS = "sent"
FAILED_STATUS = "failed"

DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 60
DEFAULT_SENDING_TIMEOUT = 300


def _get_smtp_settings() -> dict:
    """Load and validate SMTP configuration from environment variables."""

    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL") or username
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    missing = []

    if not host:
        missing.append("SMTP_HOST")

    if not username:
        missing.append("SMTP_USERNAME")

    if not password:
        missing.append("SMTP_PASSWORD")

    if not from_email:
        missing.append("SMTP_FROM_EMAIL")

    if missing:
        raise ValueError(
            "Missing SMTP configuration: " + ", ".join(missing)
        )

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "use_tls": use_tls,
    }


def _get_retry_settings() -> dict:
    """Load and validate email retry configuration."""

    max_attempts = int(
        os.getenv(
            "EMAIL_MAX_ATTEMPTS",
            str(DEFAULT_MAX_ATTEMPTS),
        )
    )

    retry_delay = int(
        os.getenv(
            "EMAIL_RETRY_DELAY",
            str(DEFAULT_RETRY_DELAY),
        )
    )

    sending_timeout = int(
        os.getenv(
            "EMAIL_SENDING_TIMEOUT",
            str(DEFAULT_SENDING_TIMEOUT),
        )
    )

    if max_attempts < 1:
        raise ValueError(
            "EMAIL_MAX_ATTEMPTS must be at least 1"
        )

    if retry_delay < 1:
        raise ValueError(
            "EMAIL_RETRY_DELAY must be at least 1 second"
        )

    if sending_timeout < 1:
        raise ValueError(
            "EMAIL_SENDING_TIMEOUT must be at least 1 second"
        )

    return {
        "max_attempts": max_attempts,
        "retry_delay": retry_delay,
        "sending_timeout": sending_timeout,
    }


def _utc_now() -> datetime:
    """Return current UTC time in the database's naive datetime format."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def _calculate_retry_time(
    *,
    attempts: int,
    retry_delay: int,
) -> datetime:
    """Calculate the next retry time using exponential backoff."""

    delay_seconds = retry_delay * (2 ** max(attempts - 1, 0))

    return _utc_now() + timedelta(
        seconds=delay_seconds,
    )


def _send_email(
    *,
    recipient: str,
    subject: str,
    body: str,
) -> None:
    """Send one email through the configured SMTP server."""

    settings = _get_smtp_settings()

    message = EmailMessage()
    message["From"] = settings["from_email"]
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(
        settings["host"],
        settings["port"],
        timeout=30,
    ) as smtp:
        if settings["use_tls"]:
            smtp.starttls()

        smtp.login(
            settings["username"],
            settings["password"],
        )

        smtp.send_message(message)


def _recover_stale_sending_notifications(
    db: Session,
    *,
    timeout_seconds: int,
) -> int:
    """Recover notifications stuck in the sending state.

    A worker crash or process termination can leave a notification in
    ``sending`` indefinitely. Notifications that have exceeded the configured
    sending timeout are returned to the pending state so they can be retried.
    """

    cutoff_time = _utc_now() - timedelta(
        seconds=timeout_seconds,
    )

    stale_notifications = (
        db.query(ApplicationNotification)
        .filter(
            ApplicationNotification.channel == EMAIL_CHANNEL,
            ApplicationNotification.delivery_status == SENDING_STATUS,
            or_(
                ApplicationNotification.last_attempt_at.is_(None),
                ApplicationNotification.last_attempt_at <= cutoff_time,
            ),
        )
        .all()
    )

    if not stale_notifications:
        return 0

    for notification in stale_notifications:
        notification.delivery_status = PENDING_STATUS
        notification.next_attempt_at = None
        notification.updated_at = _utc_now()

    db.commit()

    return len(stale_notifications)


def send_notification(
    db: Session,
    *,
    notification_id: int,
) -> ApplicationNotification:
    """Send one eligible email notification with retry handling.

    Delivery-state changes are committed independently from the application
    and notification creation transaction.
    """

    retry_settings = _get_retry_settings()

    notification = (
        db.query(ApplicationNotification)
        .filter(
            ApplicationNotification.id == notification_id,
            ApplicationNotification.channel == EMAIL_CHANNEL,
        )
        .first()
    )

    if not notification:
        raise LookupError("Notification not found")

    if notification.delivery_status == SENT_STATUS:
        return notification

    now = _utc_now()

    if (
        notification.delivery_status == FAILED_STATUS
        and notification.next_attempt_at is not None
        and notification.next_attempt_at > now
    ):
        return notification

    if notification.delivery_status not in {
        PENDING_STATUS,
        FAILED_STATUS,
    }:
        raise ValueError(
            f"Notification cannot be sent from status "
            f"'{notification.delivery_status}'"
        )

    if notification.attempts >= retry_settings["max_attempts"]:
        return notification

    notification.delivery_status = SENDING_STATUS
    notification.attempts += 1
    notification.last_attempt_at = now
    notification.next_attempt_at = None
    notification.updated_at = now

    db.commit()
    db.refresh(notification)

    try:
        _send_email(
            recipient=notification.recipient,
            subject=notification.subject,
            body=notification.body,
        )

    except Exception as error:
        failure_time = _utc_now()

        notification.delivery_status = FAILED_STATUS
        notification.failed_at = failure_time
        notification.error_message = str(error)
        notification.updated_at = failure_time

        if notification.attempts < retry_settings["max_attempts"]:
            notification.next_attempt_at = _calculate_retry_time(
                attempts=notification.attempts,
                retry_delay=retry_settings["retry_delay"],
            )
        else:
            notification.next_attempt_at = None

        db.commit()
        db.refresh(notification)

        return notification

    success_time = _utc_now()

    notification.delivery_status = SENT_STATUS
    notification.sent_at = success_time
    notification.failed_at = None
    notification.error_message = None
    notification.next_attempt_at = None
    notification.updated_at = success_time

    db.commit()
    db.refresh(notification)

    return notification


def get_pending_notifications(
    db: Session,
    *,
    limit: int = 10,
) -> list[ApplicationNotification]:
    """Return email notifications currently eligible for delivery.

    Eligible notifications include:

    - newly created pending notifications
    - failed notifications whose retry time has arrived
    - failed notifications without a retry timestamp

    Stale ``sending`` notifications are first recovered to ``pending`` so a
    worker crash cannot permanently block delivery.
    """

    retry_settings = _get_retry_settings()
    now = _utc_now()

    _recover_stale_sending_notifications(
        db,
        timeout_seconds=retry_settings["sending_timeout"],
    )

    eligible_notifications = (
        db.query(ApplicationNotification)
        .filter(
            ApplicationNotification.channel == EMAIL_CHANNEL,
            ApplicationNotification.attempts
            < retry_settings["max_attempts"],
            or_(
                ApplicationNotification.delivery_status == PENDING_STATUS,
                and_(
                    ApplicationNotification.delivery_status
                    == FAILED_STATUS,
                    or_(
                        ApplicationNotification.next_attempt_at.is_(None),
                        ApplicationNotification.next_attempt_at <= now,
                    ),
                ),
            ),
        )
        .order_by(
            ApplicationNotification.created_at.asc(),
            ApplicationNotification.id.asc(),
        )
        .limit(limit)
        .all()
    )

    return eligible_notifications


def deliver_pending_notifications(
    db: Session,
    *,
    limit: int = 10,
) -> list[ApplicationNotification]:
    """Attempt delivery of a batch of eligible email notifications."""

    notifications = get_pending_notifications(
        db,
        limit=limit,
    )

    results = []

    for notification in notifications:
        result = send_notification(
            db,
            notification_id=notification.id,
        )
        results.append(result)

    return results