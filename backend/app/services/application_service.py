from datetime import datetime
from math import ceil

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Session

from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.job import Job
from app.utils.time import utc_now
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate
from app.services.application_lifecycle import (
    APPLICATION_STATUSES,
    get_allowed_next_statuses,
    is_terminal_status,
    normalize_status,
    validate_status_transition,
)
from app.services.application_event_service import (
    record_application_created_event,
    record_status_changed_event,
)


def _normalize_source(source: str | None) -> str:
    """Normalize and validate an application/event source before persistence."""
    normalized = (source or "user").strip()
    if not normalized:
        return "user"
    if len(normalized) > 100:
        raise ValueError("Application source must be 100 characters or fewer")
    return normalized


def create_application(
    db: Session,
    user_id: int,
    application: ApplicationCreate,
) -> Application:
    job = db.query(Job).filter(Job.id == application.job_id).first()

    if not job:
        raise LookupError("Job not found")

    existing = (
        db.query(Application)
        .filter(
            Application.user_id == user_id,
            Application.job_id == application.job_id,
        )
        .first()
    )

    if existing:
        raise ValueError("You have already applied to this job")

    now = utc_now()
    source = _normalize_source(application.source_platform)

    new_application = Application(
        user_id=user_id,
        job_id=application.job_id,
        status="applied",
        source_platform=source,
        external_application_id=application.external_application_id,
        application_url=application.application_url,
        notes=application.notes,
        applied_at=now,
        last_status_changed_at=now,
        created_at=now,
        updated_at=now,
    )

    db.add(new_application)
    db.flush()

    db.add(
        ApplicationStatusHistory(
            application_id=new_application.id,
            old_status=None,
            new_status="applied",
            changed_at=now,
            source=source,
            notes=application.notes,
            notification_sent=False,
        )
    )

    record_application_created_event(
        db,
        application=new_application,
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("You have already applied to this job")

    db.refresh(new_application)
    return new_application


def _base_user_applications_query(db: Session, user_id: int) -> Query:
    return (
        db.query(Application)
        .join(Job, Job.id == Application.job_id)
        .filter(Application.user_id == user_id)
    )


def _apply_application_filters(
    query: Query,
    *,
    status_filter: str | None = None,
    source_platform: str | None = None,
    company: str | None = None,
    applied_from: datetime | None = None,
    applied_to: datetime | None = None,
) -> Query:
    if status_filter is not None:
        query = query.filter(Application.status == normalize_status(status_filter))

    if source_platform is not None:
        query = query.filter(Application.source_platform.ilike(source_platform.strip()))

    if company is not None:
        query = query.filter(Job.company.ilike(f"%{company.strip()}%"))

    if applied_from is not None:
        query = query.filter(Application.applied_at >= applied_from)

    if applied_to is not None:
        query = query.filter(Application.applied_at <= applied_to)

    return query


def get_user_applications_paginated(
    db: Session,
    user_id: int,
    *,
    status_filter: str | None = None,
    source_platform: str | None = None,
    company: str | None = None,
    applied_from: datetime | None = None,
    applied_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Application], int]:
    if page < 1:
        raise ValueError("Page must be greater than or equal to 1")
    if page_size < 1 or page_size > 100:
        raise ValueError("Page size must be between 1 and 100")
    if applied_from and applied_to and applied_from > applied_to:
        raise ValueError("applied_from cannot be later than applied_to")

    query = _apply_application_filters(
        _base_user_applications_query(db, user_id),
        status_filter=status_filter,
        source_platform=source_platform,
        company=company,
        applied_from=applied_from,
        applied_to=applied_to,
    )

    total = query.with_entities(func.count(Application.id)).scalar() or 0

    items = (
        query.order_by(
            Application.applied_at.desc(),
            Application.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total


def get_user_applications(
    db: Session,
    user_id: int,
) -> list[Application]:
    """Backward-compatible unpaginated application lookup.

    Existing internal callers/tests can continue to use the original
    service contract while API consumers use the production paginated
    endpoint through ``get_user_applications_paginated``.
    """
    items, _ = get_user_applications_paginated(
        db=db,
        user_id=user_id,
        page=1,
        page_size=100,
    )
    return items


def get_application_summary(
    db: Session,
    user_id: int,
    *,
    source_platform: str | None = None,
    company: str | None = None,
    applied_from: datetime | None = None,
    applied_to: datetime | None = None,
) -> dict:
    if applied_from and applied_to and applied_from > applied_to:
        raise ValueError("applied_from cannot be later than applied_to")

    query = _apply_application_filters(
        _base_user_applications_query(db, user_id),
        source_platform=source_platform,
        company=company,
        applied_from=applied_from,
        applied_to=applied_to,
    )

    grouped = (
        query.with_entities(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )
    counts = {status: count for status, count in grouped}
    total = sum(counts.values())
    terminal = sum(counts.get(status, 0) for status in APPLICATION_STATUSES if is_terminal_status(status))

    return {
        "total": total,
        "by_status": [
            {"status": status, "count": counts.get(status, 0)}
            for status in APPLICATION_STATUSES
        ],
        "active": total - terminal,
        "terminal": terminal,
    }


def get_user_application(
    db: Session,
    user_id: int,
    application_id: int,
) -> Application | None:
    return (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.user_id == user_id,
        )
        .first()
    )


def update_application_status(
    db: Session,
    user_id: int,
    application_id: int,
    update: ApplicationStatusUpdate,
    *,
    source: str = "user",
    metadata: dict | None = None,
) -> Application | None:
    # Lock the application row for the entire lifecycle transition.
    # PostgreSQL row locking prevents concurrent workers/platform syncs
    # from validating against the same stale status.
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.user_id == user_id,
        )
        .with_for_update()
        .first()
    )

    if not application:
        return None

    normalized_source = _normalize_source(source)

    old_status, new_status = validate_status_transition(
        application.status,
        update.status,
    )

    if new_status == old_status:
        if update.notes is not None:
            application.notes = update.notes
        db.commit()
        db.refresh(application)
        return application

    now = utc_now()

    application.status = new_status
    application.last_status_changed_at = now

    if update.notes is not None:
        application.notes = update.notes

    db.add(
        ApplicationStatusHistory(
            application_id=application.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=now,
            source=normalized_source,
            notes=update.notes,
            notification_sent=False,
        )
    )

    record_status_changed_event(
        db,
        application=application,
        old_status=old_status,
        new_status=new_status,
        source=normalized_source,
        occurred_at=now,
        metadata={
            **(metadata or {}),
            "notes": update.notes,
        },
    )

    db.commit()
    db.refresh(application)
    return application


def get_application_history(
    db: Session,
    user_id: int,
    application_id: int,
) -> list[ApplicationStatusHistory] | None:
    application = get_user_application(db, user_id, application_id)

    if not application:
        return None

    return (
        db.query(ApplicationStatusHistory)
        .filter(ApplicationStatusHistory.application_id == application_id)
        .order_by(
            ApplicationStatusHistory.changed_at.asc(),
            ApplicationStatusHistory.id.asc(),
        )
        .all()
    )


def get_application_lifecycle() -> list[dict]:
    """Expose lifecycle metadata for Swagger/UI clients without hard-coding it."""

    labels = {
        "applied": "Applied",
        "application_viewed": "Application Viewed",
        "screening": "Screening",
        "shortlisted": "Shortlisted",
        "assessment": "Assessment",
        "interview_scheduled": "Interview Scheduled",
        "interview_completed": "Interview Completed",
        "offer": "Offer",
        "selected": "Selected",
        "rejected": "Rejected",
        "withdrawn": "Withdrawn",
        "expired": "Expired",
    }

    return [
        {
            "status": status,
            "label": labels[status],
            "terminal": is_terminal_status(status),
            "allowed_next_statuses": get_allowed_next_statuses(status),
        }
        for status in APPLICATION_STATUSES
    ]
