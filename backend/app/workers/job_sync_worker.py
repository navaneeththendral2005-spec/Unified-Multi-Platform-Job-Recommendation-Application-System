"""Background worker for multi-platform job synchronization."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from typing import Any

from app.database.connection import SessionLocal
from app.integrations.job_sources.registry import job_source_registry
from app.services.job_source_sync_service import JobSourceSyncService


logger = logging.getLogger(__name__)


def _env_positive_int(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default

    return max(1, value)


DEFAULT_BATCH_LIMIT = _env_positive_int(
    "JOB_SYNC_WORKER_BATCH_LIMIT",
    50,
)

DEFAULT_POLL_INTERVAL = _env_positive_int(
    "JOB_SYNC_WORKER_INTERVAL_SECONDS",
    900,
)


def _validate_limit(limit: int) -> None:
    if limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200.")


def _validate_source(source_name: str | None) -> None:
    if source_name is None:
        return

    if not job_source_registry.has(source_name):
        raise ValueError(
            f"Job source '{source_name}' is not registered."
        )


async def _run_once_async(
    *,
    query: str | None = None,
    location: str | None = None,
    limit: int = DEFAULT_BATCH_LIMIT,
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Run one isolated provider synchronization cycle.

    Provider-level failures are handled by JobSourceSyncService.
    This function is responsible only for worker orchestration.
    """
    _validate_limit(limit)
    _validate_source(source_name)

    db = SessionLocal()

    try:
        service = JobSourceSyncService(db)

        if source_name is not None:
            result = await service.sync_source_with_retry(
                source_name,
                query=query,
                location=location,
                limit=limit,
            )

            results = {
                source_name: result,
            }

        else:
            results = await service.sync_all_sources(
                query=query,
                location=location,
                limit=limit,
            )

        return {
            "sources": results,
            "total": len(results),
        }

    finally:
        db.close()


def run_once(
    *,
    query: str | None = None,
    location: str | None = None,
    limit: int = DEFAULT_BATCH_LIMIT,
    source_name: str | None = None,
) -> dict[str, Any]:
    """
    Synchronous entry point for one worker cycle.

    This is useful for CLI execution, testing, and scheduled jobs.
    """
    try:
        return asyncio.run(
            _run_once_async(
                query=query,
                location=location,
                limit=limit,
                source_name=source_name,
            )
        )

    except Exception:
        logger.exception(
            "Job synchronization worker batch failed."
        )

        return {
            "sources": {},
            "total": 0,
            "status": "WORKER_ERROR",
        }


async def run_forever_async(
    *,
    query: str | None = None,
    location: str | None = None,
    limit: int = DEFAULT_BATCH_LIMIT,
    source_name: str | None = None,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> None:
    """
    Continuously execute synchronization cycles.

    Uses one asyncio event loop for the lifetime of the worker.
    """
    _validate_limit(limit)
    _validate_source(source_name)

    if poll_interval < 1:
        raise ValueError(
            "poll_interval must be at least 1 second."
        )

    logger.info(
        "Job sync worker started | "
        "source=%s | query=%s | location=%s | interval=%ss",
        source_name or "all",
        query,
        location,
        poll_interval,
    )

    try:
        while True:
            try:
                result = await _run_once_async(
                    query=query,
                    location=location,
                    limit=limit,
                    source_name=source_name,
                )

                logger.info(
                    "Job synchronization cycle completed | "
                    "sources=%s",
                    result.get("total", 0),
                )

            except Exception:
                logger.exception(
                    "Job synchronization cycle failed."
                )

            await asyncio.sleep(poll_interval)

    except asyncio.CancelledError:
        logger.info(
            "Job sync worker cancellation received."
        )
        raise

    finally:
        logger.info(
            "Job sync worker stopped."
        )


def run_forever(
    *,
    query: str | None = None,
    location: str | None = None,
    limit: int = DEFAULT_BATCH_LIMIT,
    source_name: str | None = None,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
) -> None:
    """Synchronous entry point for the continuous worker."""
    try:
        asyncio.run(
            run_forever_async(
                query=query,
                location=location,
                limit=limit,
                source_name=source_name,
                poll_interval=poll_interval,
            )
        )

    except KeyboardInterrupt:
        logger.info(
            "Job sync worker stopped gracefully."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Multi-platform job synchronization worker."
        )
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help=(
            "Run one synchronization cycle and exit."
        ),
    )

    parser.add_argument(
        "--source",
        default=None,
        help=(
            "Optional provider name; defaults to all providers."
        ),
    )

    parser.add_argument(
        "--query",
        default=None,
        help="Optional job search query.",
    )

    parser.add_argument(
        "--location",
        default=None,
        help="Optional preferred job location.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_BATCH_LIMIT,
        help="Maximum jobs per provider.",
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        help="Polling interval in seconds.",
    )

    args = parser.parse_args()

    if args.limit < 1 or args.limit > 200:
        parser.error(
            "--limit must be between 1 and 200"
        )

    if args.interval < 1:
        parser.error(
            "--interval must be at least 1 second"
        )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    if args.once:
        result = run_once(
            query=args.query,
            location=args.location,
            limit=args.limit,
            source_name=args.source,
        )

        logger.info(
            "One-shot job synchronization completed: %s",
            result,
        )

        return

    run_forever(
        query=args.query,
        location=args.location,
        limit=args.limit,
        source_name=args.source,
        poll_interval=args.interval,
    )


if __name__ == "__main__":
    main()