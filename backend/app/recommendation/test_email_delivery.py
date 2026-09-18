from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.database.base import Base
from app.models.application_notification import ApplicationNotification
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate
from app.services.application_service import create_application
from app.services.email_delivery_service import (
    deliver_pending_notifications,
    get_pending_notifications,
    send_notification,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    user = User(
        name="Email Delivery User",
        email="email-delivery-test@example.com",
        password_hash="test-hash",
    )

    job = Job(
        title="Email Delivery Test Job",
        company="Test Company",
        description="Email delivery engine test job.",
    )

    session.add_all([user, job])
    session.commit()

    try:
        yield session, user, job
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _create_pending_notification(session, user, job):
    application = create_application(
        session,
        user.id,
        ApplicationCreate(
            job_id=job.id,
            source_platform="internal",
        ),
    )

    notification = (
        session.query(ApplicationNotification)
        .filter(
            ApplicationNotification.application_id == application.id,
            ApplicationNotification.channel == "email",
        )
        .one()
    )

    return notification


def _utc_now_naive():
    """Return UTC time matching the database's naive DateTime representation."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def test_pending_notifications_are_selected(db):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    pending = get_pending_notifications(session)

    assert len(pending) == 1
    assert pending[0].id == notification.id
    assert pending[0].delivery_status == "pending"


def test_successful_email_delivery_marks_notification_sent(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    sent_emails = []

    def fake_send_email(*, recipient, subject, body):
        sent_emails.append(
            {
                "recipient": recipient,
                "subject": subject,
                "body": body,
            }
        )

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    result = send_notification(
        session,
        notification_id=notification.id,
    )

    assert result.delivery_status == "sent"
    assert result.attempts == 1
    assert result.sent_at is not None
    assert result.failed_at is None
    assert result.error_message is None
    assert result.next_attempt_at is None

    assert len(sent_emails) == 1
    assert sent_emails[0]["recipient"] == user.email
    assert job.title in sent_emails[0]["subject"]


def test_already_sent_notification_is_not_sent_again(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    send_count = 0

    def fake_send_email(*, recipient, subject, body):
        nonlocal send_count
        send_count += 1

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    first = send_notification(
        session,
        notification_id=notification.id,
    )

    second = send_notification(
        session,
        notification_id=notification.id,
    )

    assert first.delivery_status == "sent"
    assert second.delivery_status == "sent"
    assert send_count == 1
    assert second.attempts == 1


def test_failed_delivery_records_error_attempt_and_retry_schedule(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    def fake_send_email(*, recipient, subject, body):
        raise RuntimeError("SMTP connection failed")

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    result = send_notification(
        session,
        notification_id=notification.id,
    )

    assert result.delivery_status == "failed"
    assert result.attempts == 1
    assert result.sent_at is None
    assert result.failed_at is not None
    assert result.error_message == "SMTP connection failed"
    assert result.next_attempt_at is not None

    assert result.next_attempt_at > result.failed_at


def test_failed_notification_cannot_be_retried_before_next_attempt_time(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    send_count = 0

    def fake_send_email(*, recipient, subject, body):
        nonlocal send_count
        send_count += 1
        raise RuntimeError("Temporary SMTP failure")

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    first = send_notification(
        session,
        notification_id=notification.id,
    )

    assert first.delivery_status == "failed"
    assert first.attempts == 1
    assert first.next_attempt_at is not None

    second = send_notification(
        session,
        notification_id=notification.id,
    )

    assert second.delivery_status == "failed"
    assert second.attempts == 1
    assert send_count == 1


def test_failed_notification_can_be_retried_after_scheduled_time(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    attempts = 0

    def fake_send_email(*, recipient, subject, body):
        nonlocal attempts
        attempts += 1

        if attempts == 1:
            raise RuntimeError("Temporary SMTP failure")

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    first = send_notification(
        session,
        notification_id=notification.id,
    )

    assert first.delivery_status == "failed"
    assert first.attempts == 1
    assert first.next_attempt_at is not None

    notification.next_attempt_at = _utc_now_naive() - timedelta(seconds=1)
    session.commit()
    session.refresh(notification)

    second = send_notification(
        session,
        notification_id=notification.id,
    )

    assert second.delivery_status == "sent"
    assert second.attempts == 2
    assert second.sent_at is not None
    assert second.failed_at is None
    assert second.error_message is None
    assert second.next_attempt_at is None
    assert attempts == 2


def test_retry_uses_exponential_backoff(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    def fake_send_email(*, recipient, subject, body):
        raise RuntimeError("Temporary SMTP failure")

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    first = send_notification(
        session,
        notification_id=notification.id,
    )

    assert first.delivery_status == "failed"
    assert first.attempts == 1
    assert first.next_attempt_at is not None

    first_retry_time = first.next_attempt_at

    notification.next_attempt_at = _utc_now_naive() - timedelta(seconds=1)
    session.commit()
    session.refresh(notification)

    second = send_notification(
        session,
        notification_id=notification.id,
    )

    assert second.delivery_status == "failed"
    assert second.attempts == 2
    assert second.next_attempt_at is not None

    first_delay = first_retry_time - first.failed_at
    second_delay = second.next_attempt_at - second.failed_at

    assert second_delay > first_delay


def test_notification_stops_after_maximum_attempts(
    db,
    monkeypatch,
):
    session, user, job = db

    notification = _create_pending_notification(
        session,
        user,
        job,
    )

    send_count = 0

    def fake_send_email(*, recipient, subject, body):
        nonlocal send_count
        send_count += 1
        raise RuntimeError("Permanent SMTP failure")

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    first = send_notification(
        session,
        notification_id=notification.id,
    )

    assert first.delivery_status == "failed"
    assert first.attempts == 1
    assert first.next_attempt_at is not None

    notification.next_attempt_at = _utc_now_naive() - timedelta(seconds=1)
    session.commit()
    session.refresh(notification)

    second = send_notification(
        session,
        notification_id=notification.id,
    )

    assert second.delivery_status == "failed"
    assert second.attempts == 2
    assert second.next_attempt_at is not None

    notification.next_attempt_at = _utc_now_naive() - timedelta(seconds=1)
    session.commit()
    session.refresh(notification)

    third = send_notification(
        session,
        notification_id=notification.id,
    )

    assert third.delivery_status == "failed"
    assert third.attempts == 3
    assert third.next_attempt_at is None

    notification.next_attempt_at = _utc_now_naive() - timedelta(seconds=1)
    session.commit()
    session.refresh(notification)

    fourth = send_notification(
        session,
        notification_id=notification.id,
    )

    assert fourth.delivery_status == "failed"
    assert fourth.attempts == 3
    assert send_count == 3


def test_batch_delivery_processes_pending_notifications(
    db,
    monkeypatch,
):
    session, user, job = db

    first = _create_pending_notification(
        session,
        user,
        job,
    )

    second_user = User(
        name="Second Email User",
        email="second-email-test@example.com",
        password_hash="test-hash",
    )

    session.add(second_user)
    session.commit()

    second = _create_pending_notification(
        session,
        second_user,
        job,
    )

    sent = []

    def fake_send_email(*, recipient, subject, body):
        sent.append(recipient)

    monkeypatch.setattr(
        "app.services.email_delivery_service._send_email",
        fake_send_email,
    )

    results = deliver_pending_notifications(
        session,
        limit=10,
    )

    assert len(results) == 2
    assert {item.id for item in results} == {
        first.id,
        second.id,
    }

    assert all(item.delivery_status == "sent" for item in results)
    assert all(item.attempts == 1 for item in results)
    assert len(sent) == 2