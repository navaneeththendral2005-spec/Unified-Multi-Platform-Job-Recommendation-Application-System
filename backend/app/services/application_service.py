from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.job import Job
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

    now = datetime.utcnow()

    new_application = Application(
        user_id=user_id,
        job_id=application.job_id,
        status="applied",
        source_platform=application.source_platform,
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
            source=application.source_platform or "user",
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


def get_user_applications(
    db: Session,
    user_id: int,
) -> list[Application]:
    return (
        db.query(Application)
        .filter(Application.user_id == user_id)
        .order_by(Application.applied_at.desc())
        .all()
    )


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
) -> Application | None:
    application = get_user_application(db, user_id, application_id)

    if not application:
        return None

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

    now = datetime.utcnow()

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
            source="user",
            notes=update.notes,
            notification_sent=False,
        )
    )

    record_status_changed_event(
        db,
        application=application,
        old_status=old_status,
        new_status=new_status,
        source="user",
        occurred_at=now,
        metadata={
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
        .order_by(ApplicationStatusHistory.changed_at.asc())
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
