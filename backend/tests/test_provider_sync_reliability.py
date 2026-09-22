import asyncio

import pytest

from app.services.job_source_sync_service import JobSourceSyncService
from app.services.provider_sync_policy import (
    SYNC_STATUS_AUTHORIZATION_REQUIRED,
    SYNC_STATUS_INVALID_REQUEST,
    SYNC_STATUS_PROVIDER_UNAVAILABLE,
    SYNC_STATUS_RATE_LIMITED,
    SYNC_STATUS_TIMEOUT,
    classify_provider_exception,
)


def test_classifies_authorization_failure_without_retry():
    result = classify_provider_exception(PermissionError("denied"))

    assert result.status == SYNC_STATUS_AUTHORIZATION_REQUIRED
    assert result.retryable is False


def test_classifies_not_implemented_as_authorization_required():
    result = classify_provider_exception(
        NotImplementedError("authorized integration required")
    )

    assert result.status == SYNC_STATUS_AUTHORIZATION_REQUIRED
    assert result.retryable is False


def test_classifies_invalid_request_without_retry():
    result = classify_provider_exception(ValueError("bad request"))

    assert result.status == SYNC_STATUS_INVALID_REQUEST
    assert result.retryable is False


def test_classifies_timeout_as_retryable():
    result = classify_provider_exception(TimeoutError())

    assert result.status == SYNC_STATUS_TIMEOUT
    assert result.retryable is True


def test_classifies_connection_error_as_retryable():
    result = classify_provider_exception(ConnectionError())

    assert result.status == SYNC_STATUS_PROVIDER_UNAVAILABLE
    assert result.retryable is True


def test_classifies_rate_limit_from_status_code():
    class RateLimitError(Exception):
        status_code = 429

    result = classify_provider_exception(RateLimitError())

    assert result.status == SYNC_STATUS_RATE_LIMITED
    assert result.retryable is True


def test_transient_failure_is_retried(monkeypatch, db_session):
    service = JobSourceSyncService(
        db_session,
        sleep_func=_no_sleep,
    )

    calls = 0

    async def flaky_sync(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls < 3:
            raise TimeoutError("temporary timeout")
        return []

    monkeypatch.setattr(service, "sync_source", flaky_sync)

    result = asyncio.run(service._sync_with_retry(
        "linkedin",
        query="python developer",
        location="Chennai",
        limit=20,
    ))

    assert calls == 3
    assert result["status"] == "SYNCED"
    assert result["attempts"] == 3
    assert result["jobs_ingested"] == 0


def test_authorization_failure_is_not_retried(monkeypatch, db_session):
    service = JobSourceSyncService(
        db_session,
        sleep_func=_no_sleep,
    )

    calls = 0

    async def unauthorized_sync(*args, **kwargs):
        nonlocal calls
        calls += 1
        raise PermissionError("unauthorized")

    monkeypatch.setattr(service, "sync_source", unauthorized_sync)

    result = asyncio.run(service._sync_with_retry(
        "linkedin",
        query="python developer",
        location="Chennai",
        limit=20,
    ))

    assert calls == 1
    assert result["status"] == SYNC_STATUS_AUTHORIZATION_REQUIRED
    assert result["attempts"] == 1
    assert result["retryable"] is False


def test_multi_provider_sync_isolates_failures(monkeypatch, db_session):
    service = JobSourceSyncService(
        db_session,
        sleep_func=_no_sleep,
    )

    async def fake_sync(source_name, **kwargs):
        if source_name == "linkedin":
            raise TimeoutError("temporary")
        return []

    monkeypatch.setattr(service, "sync_source", fake_sync)
    monkeypatch.setattr(service, "max_attempts", 1)

    result = asyncio.run(service.sync_all_sources(
        query="python developer",
        location="Chennai",
        limit=20,
    ))

    assert set(result) == {
        "linkedin",
        "naukri",
        "internshala",
        "indeed",
        "wellfound",
    }
    assert result["linkedin"]["status"] == SYNC_STATUS_TIMEOUT
    assert result["naukri"]["status"] == "SYNCED"


async def _no_sleep(_: float) -> None:
    await asyncio.sleep(0)
