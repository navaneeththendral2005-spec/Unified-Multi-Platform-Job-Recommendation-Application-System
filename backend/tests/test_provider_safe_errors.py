import asyncio

from app.services.job_source_health_service import JobSourceHealthService
from app.services.job_source_sync_service import JobSourceSyncService


class SecretBearingError(Exception):
    pass


async def _raise_secret(*args, **kwargs):
    raise SecretBearingError(
        "https://provider.example/token Authorization=super-secret-token"
    )



def test_sync_result_does_not_expose_raw_provider_exception(monkeypatch, db_session):
    service = JobSourceSyncService(db_session, sleep_func=lambda _: asyncio.sleep(0))
    monkeypatch.setattr(service, "sync_source", _raise_secret)
    monkeypatch.setattr(service, "max_attempts", 1)

    result = asyncio.run(
        service.sync_source_with_retry(
            "linkedin",
            query="python",
            location="Chennai",
            limit=10,
        )
    )

    assert "super-secret-token" not in result["message"]
    assert result["message"] == "Provider synchronization failed. Check server logs for details."
