"""Email delivery engine for pending application notifications.

This service owns SMTP delivery and delivery-state updates.
Application, lifecycle, event, and notification creation remain separate
from actual email delivery.
"""

from __future__ import annotations

import os
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from dotenv import load_dotenv
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


def send_notification(
    db: Session,
    *,
    notification_id: int,
) -> ApplicationNotification:
    """Send one pending email notification.

    Delivery-state changes are committed independently from the application
    and notification creation transaction.
    """

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

    if notification.delivery_status not in {
        PENDING_STATUS,
        FAILED_STATUS,
    }:
        raise ValueError(
            f"Notification cannot be sent from status "
            f"'{notification.delivery_status}'"
        )

    notification.delivery_status = SENDING_STATUS
    notification.attempts += 1
    notification.last_attempt_at = datetime.now(timezone.utc)
    notification.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    try:
        _send_email(
            recipient=notification.recipient,
            subject=notification.subject,
            body=notification.body,
        )

    except Exception as error:
        notification.delivery_status = FAILED_STATUS
        notification.failed_at = datetime.now(timezone.utc)
        notification.error_message = str(error)
        notification.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(notification)

        return notification

    notification.delivery_status = SENT_STATUS
    notification.sent_at = datetime.now(timezone.utc)
    notification.failed_at = None
    notification.error_message = None
    notification.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(notification)

    return notification


def get_pending_notifications(
    db: Session,
    *,
    limit: int = 10,
) -> list[ApplicationNotification]:
    """Return pending email notifications ready for delivery."""

    return (
        db.query(ApplicationNotification)
        .filter(
            ApplicationNotification.channel == EMAIL_CHANNEL,
            ApplicationNotification.delivery_status == PENDING_STATUS,
        )
        .order_by(
            ApplicationNotification.created_at.asc(),
            ApplicationNotification.id.asc(),
        )
        .limit(limit)
        .all()
    )


def deliver_pending_notifications(
    db: Session,
    *,
    limit: int = 10,
) -> list[ApplicationNotification]:
    """Attempt delivery of a batch of pending email notifications."""

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