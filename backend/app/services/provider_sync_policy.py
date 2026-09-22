from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SYNC_STATUS_SYNCED = "SYNCED"
SYNC_STATUS_AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
SYNC_STATUS_INVALID_REQUEST = "INVALID_REQUEST"
SYNC_STATUS_RATE_LIMITED = "RATE_LIMITED"
SYNC_STATUS_TIMEOUT = "TIMEOUT"
SYNC_STATUS_PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
SYNC_STATUS_PROVIDER_ERROR = "PROVIDER_ERROR"
SYNC_STATUS_CONFIGURATION_REQUIRED = "CONFIGURATION_REQUIRED"


@dataclass(frozen=True, slots=True)
class ProviderSyncFailure:
    status: str
    message: str
    retryable: bool


def _status_code_from_exception(exc: BaseException) -> int | None:
    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)

    if isinstance(status_code, int):
        return status_code

    status_code = getattr(exc, "status_code", None)
    if isinstance(status_code, int):
        return status_code

    return None


def classify_provider_exception(exc: BaseException) -> ProviderSyncFailure:
    """Classify an adapter failure without exposing provider secrets."""

    if isinstance(exc, NotImplementedError):
        return ProviderSyncFailure(
            status=SYNC_STATUS_AUTHORIZATION_REQUIRED,
            message=str(exc) or "Provider authorization or integration is required.",
            retryable=False,
        )

    if isinstance(exc, PermissionError):
        return ProviderSyncFailure(
            status=SYNC_STATUS_AUTHORIZATION_REQUIRED,
            message="Provider authorization is required or has expired.",
            retryable=False,
        )

    if isinstance(exc, ValueError):
        return ProviderSyncFailure(
            status=SYNC_STATUS_INVALID_REQUEST,
            message=str(exc) or "The provider request is invalid.",
            retryable=False,
        )

    status_code = _status_code_from_exception(exc)

    if status_code in {401, 403}:
        return ProviderSyncFailure(
            status=SYNC_STATUS_AUTHORIZATION_REQUIRED,
            message="Provider authorization is required or has expired.",
            retryable=False,
        )

    if status_code == 429:
        return ProviderSyncFailure(
            status=SYNC_STATUS_RATE_LIMITED,
            message="Provider rate limit reached; the synchronization can be retried later.",
            retryable=True,
        )

    if status_code in {408, 504} or isinstance(exc, TimeoutError):
        return ProviderSyncFailure(
            status=SYNC_STATUS_TIMEOUT,
            message="Provider request timed out; a retry may succeed.",
            retryable=True,
        )

    if status_code in {500, 502, 503} or isinstance(exc, ConnectionError):
        return ProviderSyncFailure(
            status=SYNC_STATUS_PROVIDER_UNAVAILABLE,
            message="Provider is temporarily unavailable; a retry may succeed.",
            retryable=True,
        )

    return ProviderSyncFailure(
        status=SYNC_STATUS_PROVIDER_ERROR,
        message="Provider synchronization failed. Check server logs for details.",
        retryable=False,
    )


def public_failure_payload(
    failure: ProviderSyncFailure,
    *,
    attempts: int,
) -> dict[str, Any]:
    return {
        "status": failure.status,
        "jobs_ingested": 0,
        "attempts": attempts,
        "retryable": failure.retryable,
        "message": failure.message,
    }
