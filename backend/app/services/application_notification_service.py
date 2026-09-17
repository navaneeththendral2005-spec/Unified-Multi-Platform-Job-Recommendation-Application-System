"""Notification orchestration for durable application events.

This layer creates channel-specific notification records from application
events. It intentionally does not send email itself; a future Email Engine
will consume pending email notifications and own delivery/retry concerns.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.models.application_notification import ApplicationNotification
from app.models.job import Job
from app.models.user import User


EMAIL_CHANNEL = "email"
PENDING_STATUS = "pending"


def _build_notification_content(
    event: ApplicationEvent,
    *,
    job: Job | None,
) -> tuple[str, str]:
    job_label = (
        f"{job.title} at {job.company}"
        if job is not None
        else f"application #{event.application_id}"
    )

    if event.event_type == "application_created":
        return (
            f"Application submitted — {job_label}",
            f"Your application for {job_label} has been recorded successfully.",
        )

    if event.event_type == "status_changed":
        old_label = event.old_status or "unknown"
        new_label = event.new_status or "unknown"
        return (
            f"Application status updated — {job_label}",
            f"Your application for {job_label} moved from "
            f"{old_label} to {new_label}.",
        )

    return (
        f"Application update — {job_label}",
        f"There is a new update for your {job_label}.",
    )


def create_notification_for_event(
    db: Session,
    event: ApplicationEvent,
) -> ApplicationNotification:
    """Create the default email notification for one application event.

    The caller owns the transaction. A unique event/channel constraint makes
    this operation safe against duplicate delivery scheduling.
    """

    existing = (
        db.query(ApplicationNotification)
        .filter(
            ApplicationNotification.event_id == event.id,
            ApplicationNotification.channel == EMAIL_CHANNEL,
        )
        .first()
    )
    if existing:
        return existing

    user = db.query(User).filter(User.id == event.user_id).first()
    if not user:
        raise LookupError("Notification recipient not found")

    application = (
        db.query(Application)
        .filter(Application.id == event.application_id)
        .first()
    )
    job = db.query(Job).filter(Job.id == application.job_id).first() if application else None

    subject, body = _build_notification_content(event, job=job)

    notification = ApplicationNotification(
        user_id=event.user_id,
        application_id=event.application_id,
        event_id=event.id,
        channel=EMAIL_CHANNEL,
        notification_type=event.event_type,
        recipient=user.email,
        subject=subject,
        body=body,
        delivery_status=PENDING_STATUS,
        attempts=0,
        created_at=event.occurred_at,
        updated_at=event.occurred_at,
    )

    db.add(notification)
    db.flush()
    return notification


def get_user_notifications(
    db: Session,
    *,
    user_id: int,
    unread_only: bool = False,
) -> list[ApplicationNotification]:
    query = (
        db.query(ApplicationNotification)
        .filter(ApplicationNotification.user_id == user_id)
        .order_by(
            ApplicationNotification.created_at.desc(),
            ApplicationNotification.id.desc(),
        )
    )

    if unread_only:
        query = query.filter(ApplicationNotification.read_at.is_(None))

    return query.all()


def mark_notification_read(
    db: Session,
    *,
    user_id: int,
    notification_id: int,
) -> ApplicationNotification | None:
    notification = (
        db.query(ApplicationNotification)
        .filter(
            ApplicationNotification.id == notification_id,
            ApplicationNotification.user_id == user_id,
        )
        .first()
    )

    if not notification:
        return None

    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)

    return notification
