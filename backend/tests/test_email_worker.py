from app.models.application_notification import ApplicationNotification
from app.workers.email_worker import run_once


def test_worker_run_once_processes_pending_notifications(monkeypatch):
    calls = []

    def fake_deliver_pending_notifications(db, limit):
        calls.append(limit)
        return ["notification-1", "notification-2"]

    monkeypatch.setattr(
        "app.workers.email_worker.deliver_pending_notifications",
        fake_deliver_pending_notifications,
    )

    result = run_once(batch_size=5)

    assert result == 2
    assert calls == [5]


def test_worker_run_once_handles_delivery_failure(monkeypatch):
    def fake_deliver_pending_notifications(db, limit):
        raise RuntimeError("SMTP temporarily unavailable")

    monkeypatch.setattr(
        "app.workers.email_worker.deliver_pending_notifications",
        fake_deliver_pending_notifications,
    )

    result = run_once(batch_size=5)

    assert result == 0


def test_worker_processes_retryable_failed_notification(monkeypatch):
    calls = []

    def fake_deliver_pending_notifications(db, limit):
        calls.append(limit)
        return [
            ApplicationNotification(
                id=101,
                delivery_status="sent",
                attempts=2,
            )
        ]

    monkeypatch.setattr(
        "app.workers.email_worker.deliver_pending_notifications",
        fake_deliver_pending_notifications,
    )

    result = run_once(batch_size=5)

    assert result == 1
    assert calls == [5]


def test_worker_handles_no_eligible_notifications(monkeypatch):
    calls = []

    def fake_deliver_pending_notifications(db, limit):
        calls.append(limit)
        return []

    monkeypatch.setattr(
        "app.workers.email_worker.deliver_pending_notifications",
        fake_deliver_pending_notifications,
    )

    result = run_once(batch_size=5)

    assert result == 0
    assert calls == [5]


def test_worker_processes_recovered_stale_notification(monkeypatch):
    calls = []

    def fake_deliver_pending_notifications(db, limit):
        calls.append(limit)
        return [
            ApplicationNotification(
                id=102,
                delivery_status="sent",
                attempts=2,
            )
        ]

    monkeypatch.setattr(
        "app.workers.email_worker.deliver_pending_notifications",
        fake_deliver_pending_notifications,
    )

    result = run_once(batch_size=10)

    assert result == 1
    assert calls == [10]


def test_worker_run_once_respects_batch_size(monkeypatch):
    batch_sizes = []

    def fake_deliver_pending_notifications(db, limit):
        batch_sizes.append(limit)
        return []

    monkeypatch.setattr(
        "app.workers.email_worker.deliver_pending_notifications",
        fake_deliver_pending_notifications,
    )

    result = run_once(batch_size=25)

    assert result == 0
    assert batch_sizes == [25]