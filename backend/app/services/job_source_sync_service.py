from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Awaitable, Callable

from sqlalchemy.orm import Session

from app.integrations.job_sources.registry import job_source_registry
from app.models.job import Job
from app.services.job_ingestion_service import JobIngestionService
from app.services.provider_sync_policy import (
    SYNC_STATUS_SYNCED,
    classify_provider_exception,
)


logger = logging.getLogger(__name__)


SleepFunc = Callable[[float], Awaitable[None]]


class JobSourceSyncService:
    """
    Production synchronization orchestrator for external job providers.

    Providers are isolated from one another. Transient failures are retried
    with bounded exponential backoff, while authorization/configuration and
    invalid-request failures are returned immediately.
    """

    def __init__(
        self,
        db: Session,
        *,
        sleep_func: SleepFunc = asyncio.sleep,
    ) -> None:
        self.db = db
        self.ingestion_service = JobIngestionService(db)
        self.sleep_func = sleep_func

        self.max_attempts = self._env_int(
            "JOB_SYNC_MAX_ATTEMPTS",
            3,
            minimum=1,
            maximum=10,
        )

        self.initial_delay_seconds = self._env_float(
            "JOB_SYNC_INITIAL_DELAY_SECONDS",
            1.0,
            minimum=0.0,
            maximum=60.0,
        )

        self.max_delay_seconds = self._env_float(
            "JOB_SYNC_MAX_DELAY_SECONDS",
            8.0,
            minimum=0.0,
            maximum=300.0,
        )

        self.backoff_multiplier = self._env_float(
            "JOB_SYNC_BACKOFF_MULTIPLIER",
            2.0,
            minimum=1.0,
            maximum=10.0,
        )

    @staticmethod
    def _env_int(
        name: str,
        default: int,
        *,
        minimum: int,
        maximum: int,
    ) -> int:
        try:
            value = int(os.getenv(name, str(default)))
        except (TypeError, ValueError):
            return default

        return max(minimum, min(value, maximum))

    @staticmethod
    def _env_float(
        name: str,
        default: float,
        *,
        minimum: float,
        maximum: float,
    ) -> float:
        try:
            value = float(os.getenv(name, str(default)))
        except (TypeError, ValueError):
            return default

        return max(minimum, min(value, maximum))

    async def sync_source(
        self,
        source_name: str,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> list[Job]:
        adapter = job_source_registry.get(source_name)

        if adapter is None:
            raise ValueError(
                f"Job source '{source_name}' is not registered."
            )

        if limit < 1 or limit > 200:
            raise ValueError("limit must be between 1 and 200.")

        normalized_jobs = await adapter.search_jobs(
            query=query,
            location=location,
            limit=limit,
            **kwargs,
        )

        jobs: list[Job] = []

        for normalized_job in normalized_jobs:
            jobs.append(
                self.ingestion_service.ingest(normalized_job)
            )

        return jobs

    async def _sync_with_retry(
        self,
        source_name: str,
        *,
        query: str | None,
        location: str | None,
        limit: int,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Synchronize one provider using bounded retry logic.

        Non-retryable failures stop immediately.

        Retryable failures continue until max_attempts is reached.

        The final failure response preserves the actual classified provider
        status instead of falling back to a generic PROVIDER_ERROR.
        """
        attempts = 0
        delay = self.initial_delay_seconds

        last_status = "PROVIDER_ERROR"
        last_retryable = False
        last_message = "Provider synchronization failed."

        while attempts < self.max_attempts:
            attempts += 1

            try:
                jobs = await self.sync_source(
                    source_name,
                    query=query,
                    location=location,
                    limit=limit,
                    **kwargs,
                )

                return {
                    "status": SYNC_STATUS_SYNCED,
                    "jobs_ingested": len(jobs),
                    "job_ids": [
                        job.id
                        for job in jobs
                        if job.id is not None
                    ],
                    "attempts": attempts,
                    "retryable": False,
                }

            except Exception as exc:
                failure = classify_provider_exception(exc)

                last_status = failure.status
                last_retryable = failure.retryable
                last_message = failure.message

                logger.warning(
                    "Provider sync attempt %s/%s failed for '%s': "
                    "status=%s retryable=%s",
                    attempts,
                    self.max_attempts,
                    source_name,
                    failure.status,
                    failure.retryable,
                )

                # Non-retryable failures such as authorization,
                # configuration, invalid requests, etc. must stop
                # immediately.
                if not failure.retryable:
                    logger.exception(
                        "Provider synchronization failed for '%s' "
                        "after %s attempt(s): status=%s retryable=%s",
                        source_name,
                        attempts,
                        failure.status,
                        failure.retryable,
                    )
                    break

                # Retryable failure, but no attempts remain.
                if attempts >= self.max_attempts:
                    logger.exception(
                        "Provider synchronization failed for '%s' "
                        "after %s attempt(s): status=%s retryable=%s",
                        source_name,
                        attempts,
                        failure.status,
                        failure.retryable,
                    )
                    break

                # Wait before the next retry using bounded exponential
                # backoff.
                if delay > 0:
                    await self.sleep_func(delay)

                    delay = min(
                        self.max_delay_seconds,
                        delay * self.backoff_multiplier,
                    )

        # Preserve the actual provider failure classification.
        return {
            "status": last_status,
            "jobs_ingested": 0,
            "attempts": attempts,
            "retryable": last_retryable,
            "message": last_message,
        }

    async def sync_source_with_retry(
        self,
        source_name: str,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Synchronize one provider with the production retry policy."""
        return await self._sync_with_retry(
            source_name,
            query=query,
            location=location,
            limit=limit,
            **kwargs,
        )

    async def sync_all_sources(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Synchronize every registered provider independently.

        A failure in one provider does not prevent the remaining providers
        from being synchronized.
        """
        results: dict[str, Any] = {}

        for source_name in job_source_registry.list_sources():
            results[source_name] = await self.sync_source_with_retry(
                source_name,
                query=query,
                location=location,
                limit=limit,
                **kwargs,
            )

        return results
