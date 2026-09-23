import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database.base import Base
from app.models.application_notification import ApplicationNotification
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate
from app.services.application_notification_service import (
    get_user_notifications,
    mark_notification_read,
)
from app.services.application_service import (
    create_application,
    update_application_status,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    user = User(
        name="Notification User",
        email="notification-test@example.com",
        password_hash="test-hash",
    )
    job = Job(
        title="Notification Test Job",
        company="Test Company",
        description="Notification engine test job.",
    )
    session.add_all([user, job])
    session.commit()

    try:
        yield session, user, job
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_application_creation_creates_pending_email_notification(db):
    session, user, job = db

    application = create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id, source_platform="internal"),
    )

    notifications = get_user_notifications(session, user_id=user.id)

    assert len(notifications) == 1
    notification = notifications[0]
    assert notification.application_id == application.id
    assert notification.channel == "email"
    assert notification.notification_type == "application_created"
    assert notification.delivery_status == "pending"
    assert notification.recipient == user.email
    assert job.title in notification.subject


def test_status_change_creates_second_notification(db):
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

    notifications = get_user_notifications(session, user_id=user.id)

    assert len(notifications) == 2
    assert {item.notification_type for item in notifications} == {
        "application_created",
        "status_changed",
    }


def test_notifications_are_user_scoped(db):
    session, user, job = db

    other = User(
        name="Other User",
        email="other-notification@example.com",
        password_hash="test-hash",
    )
    session.add(other)
    session.commit()

    create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id),
    )

    assert get_user_notifications(session, user_id=other.id) == []


def test_mark_notification_read_is_idempotent(db):
    session, user, job = db

    create_application(
        session,
        user.id,
        ApplicationCreate(job_id=job.id),
    )

    notification = (
        session.query(ApplicationNotification)
        .filter(ApplicationNotification.user_id == user.id)
        .one()
    )

    first = mark_notification_read(
        session,
        user_id=user.id,
        notification_id=notification.id,
    )
    first_read_at = first.read_at

    second = mark_notification_read(
        session,
        user_id=user.id,
        notification_id=notification.id,
    )

    assert first_read_at is not None
    assert second.read_at == first_read_at
