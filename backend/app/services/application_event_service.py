from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_event import ApplicationEvent
from app.services.application_notification_service import (
    create_notification_for_event,
)

APPLICATION_CREATED = "application_created"
STATUS_CHANGED = "status_changed"


def record_application_event(
    db: Session,
    *,
    application: Application,
    event_type: str,
    old_status: str | None = None,
    new_status: str | None = None,
    source: str | None = None,
    occurred_at: datetime | None = None,
    metadata: dict | None = None,
) -> ApplicationEvent:
    """
    Record an application event.

    This function deliberately does not commit the transaction.
    The caller owns the transaction so that event creation can remain
    atomic with the application/lifecycle change.
    """

    event = ApplicationEvent(
        application_id=application.id,
        user_id=application.user_id,
        event_type=event_type,
        old_status=old_status,
        new_status=new_status,
        source=source,
        occurred_at=occurred_at or datetime.utcnow(),
        event_metadata=metadata,
    )

    db.add(event)
    db.flush()

    create_notification_for_event(db, event)

    return event


def record_application_created_event(
    db: Session,
    *,
    application: Application,
) -> ApplicationEvent:
    """Record the initial application-created event."""

    return record_application_event(
        db,
        application=application,
        event_type=APPLICATION_CREATED,
        old_status=None,
        new_status=application.status,
        source=application.source_platform or "user",
        occurred_at=application.created_at,
        metadata={
            "job_id": application.job_id,
            "application_url": application.application_url,
        },
    )


def record_status_changed_event(
    db: Session,
    *,
    application: Application,
    old_status: str,
    new_status: str,
    source: str = "user",
    occurred_at: datetime | None = None,
    metadata: dict | None = None,
) -> ApplicationEvent:
    """Record a lifecycle status change event."""

    event_metadata = dict(metadata or {})

    if application.job_id is not None:
        event_metadata.setdefault("job_id", application.job_id)

    return record_application_event(
        db,
        application=application,
        event_type=STATUS_CHANGED,
        old_status=old_status,
        new_status=new_status,
        source=source,
        occurred_at=occurred_at,
        metadata=event_metadata or None,
    )


def get_application_events(
    db: Session,
    *,
    user_id: int,
    application_id: int,
) -> list[ApplicationEvent] | None:
    """
    Return events for an application owned by the user.

    Returns None when the application does not belong to the user.
    """

    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.user_id == user_id,
        )
        .first()
    )

    if not application:
        return None

    return (
        db.query(ApplicationEvent)
        .filter(
            ApplicationEvent.application_id == application_id,
            ApplicationEvent.user_id == user_id,
        )
        .order_by(
            ApplicationEvent.occurred_at.asc(),
            ApplicationEvent.id.asc(),
        )
        .all()
    )