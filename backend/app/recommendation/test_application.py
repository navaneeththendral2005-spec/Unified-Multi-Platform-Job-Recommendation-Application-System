from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401 - registers all models with Base
from app.database.base import Base
from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.job import Job
from app.models.user import User
from app.models.application_event import ApplicationEvent
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate
from app.services.application_lifecycle import (
    APPLICATION_STATUSES,
    get_allowed_next_statuses,
    normalize_status,
    validate_status_transition,
)
from app.services.application_service import (
    create_application,
    get_application_history,
    get_user_applications,
    update_application_status,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    user = User(
        name="Test User",
        email="application-test@example.com",
        password_hash="test-hash",
    )
    job = Job(
        title="Backend Developer",
        company="Test Company",
        description="Build backend services.",
    )
    session.add_all([user, job])
    session.commit()

    try:
        yield session, user, job
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_lifecycle_contains_professional_status_set():
    assert APPLICATION_STATUSES == (
        "applied",
        "application_viewed",
        "screening",
        "shortlisted",
        "assessment",
        "interview_scheduled",
        "interview_completed",
        "offer",
        "selected",
        "rejected",
        "withdrawn",
        "expired",
    )


def test_normalize_status_accepts_case_spaces_and_legacy_alias():
    assert normalize_status("  INTERVIEW ") == "interview_scheduled"
    assert normalize_status("Interview Scheduled") == "interview_scheduled"


def test_normalize_status_rejects_unknown_status():
    with pytest.raises(ValueError):
        normalize_status("unknown")


def test_valid_status_transition_is_allowed():
    assert validate_status_transition("applied", "screening") == (
        "applied",
        "screening",
    )


def test_invalid_status_transition_is_rejected():
    with pytest.raises(ValueError, match="Invalid application status transition"):
        validate_status_transition("applied", "selected")


def test_terminal_status_cannot_move_forward():
    with pytest.raises(ValueError, match="Invalid application status transition"):
        validate_status_transition("selected", "offer")


def test_create_application_starts_as_applied_and_creates_history(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(
            job_id=job.id,
            source_platform="LinkedIn",
            application_url="https://example.com/apply",
            notes="Submitted resume",
        ),
    )

    assert application.status == "applied"
    assert application.user_id == user.id
    assert application.job_id == job.id
    assert application.applied_at is not None

    history = (
        session.query(ApplicationStatusHistory)
        .filter(ApplicationStatusHistory.application_id == application.id)
        .all()
    )

    assert len(history) == 1
    assert history[0].old_status is None
    assert history[0].new_status == "applied"
    assert history[0].source == "LinkedIn"


def test_duplicate_application_is_rejected(db):
    session, user, job = db
    payload = ApplicationCreate(job_id=job.id)

    create_application(session, user.id, payload)

    with pytest.raises(ValueError, match="already applied"):
        create_application(session, user.id, payload)


def test_update_status_creates_history_entry(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id),
    )
    old_changed_at = application.last_status_changed_at

    updated = update_application_status(
        session,
        user.id,
        application.id,
        ApplicationStatusUpdate(
            status="screening",
            notes="Application entered screening",
        ),
    )

    assert updated is not None
    assert updated.status == "screening"
    assert updated.last_status_changed_at >= old_changed_at

    history = get_application_history(
        session,
        user.id,
        application.id,
    )

    assert history is not None
    assert len(history) == 2
    assert history[-1].old_status == "applied"
    assert history[-1].new_status == "screening"
    assert history[-1].notes == "Application entered screening"


def test_full_forward_lifecycle_can_progress(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id),
    )

    progression = [
        "screening",
        "shortlisted",
        "assessment",
        "interview_scheduled",
        "interview_completed",
        "offer",
        "selected",
    ]

    for next_status in progression:
        application = update_application_status(
            session,
            user.id,
            application.id,
            ApplicationStatusUpdate(status=next_status),
        )
        assert application.status == next_status

    history = get_application_history(session, user.id, application.id)
    assert history is not None
    assert len(history) == len(progression) + 1


def test_get_user_applications_is_user_scoped(db):
    session, user, job = db

    other_user = User(
        name="Other User",
        email="other@example.com",
        password_hash="test-hash",
    )
    session.add(other_user)
    session.commit()

    create_application(session, user.id, ApplicationCreate(job_id=job.id))

    assert len(get_user_applications(session, user.id)) == 1
    assert get_user_applications(session, other_user.id) == []

def test_create_application_creates_application_created_event(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(
            job_id=job.id,
            source_platform="LinkedIn",
            application_url="https://example.com/apply",
        ),
    )

    events = (
        session.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application.id)
        .order_by(ApplicationEvent.id.asc())
        .all()
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_type == "application_created"
    assert event.application_id == application.id
    assert event.user_id == user.id
    assert event.old_status is None
    assert event.new_status == "applied"
    assert event.source == "LinkedIn"
    assert event.event_metadata["job_id"] == job.id
    assert event.event_metadata["application_url"] == (
        "https://example.com/apply"
    )


def test_status_change_creates_status_changed_event(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id),
    )

    update_application_status(
        session,
        user.id,
        application.id,
        ApplicationStatusUpdate(
            status="screening",
            notes="Entered screening",
        ),
    )

    events = (
        session.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application.id)
        .order_by(ApplicationEvent.id.asc())
        .all()
    )

    assert len(events) == 2

    created_event = events[0]
    status_event = events[1]

    assert created_event.event_type == "application_created"

    assert status_event.event_type == "status_changed"
    assert status_event.old_status == "applied"
    assert status_event.new_status == "screening"
    assert status_event.source == "user"
    assert status_event.event_metadata["job_id"] == job.id
    assert status_event.event_metadata["notes"] == "Entered screening"


def test_invalid_status_change_creates_no_event(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id),
    )

    with pytest.raises(
        ValueError,
        match="Invalid application status transition",
    ):
        update_application_status(
            session,
            user.id,
            application.id,
            ApplicationStatusUpdate(
                status="selected",
            ),
        )

    events = (
        session.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application.id)
        .all()
    )

    assert len(events) == 1
    assert events[0].event_type == "application_created"
