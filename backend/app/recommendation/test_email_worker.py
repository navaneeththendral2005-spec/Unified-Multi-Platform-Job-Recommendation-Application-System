import pytest

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