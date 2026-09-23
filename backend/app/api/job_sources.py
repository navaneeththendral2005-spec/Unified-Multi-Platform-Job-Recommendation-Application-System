from typing import Any
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.integrations.auth import (
    auth_provider_registry,
    register_auth_providers,
)

from app.integrations.auth.provider_configuration import (
    provider_configuration_manager,
)

from app.integrations.job_sources.registry import (
    job_source_registry,
)

from app.services.provider_capability_service import public_capability_report
from app.integrations.job_sources.capabilities import (
    capabilities_to_public_dict,
)

from app.services.job_source_health_service import (
    JobSourceHealthService,
)

from app.services.job_source_service import (
    JobSourceService,
)

from app.services.job_source_sync_service import (
    JobSourceSyncService,
)


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/job-sources",
    tags=["Job Sources"],
)


# ------------------------------------------------------------------
# Authentication helpers
# ------------------------------------------------------------------


def _ensure_auth_registry() -> None:
    """
    Ensure authentication providers are initialized before the API
    attempts to inspect their authorization state.
    """

    if not auth_provider_registry.list_providers():
        register_auth_providers()


async def _get_auth_status(
    source_name: str,
) -> dict[str, Any]:
    """
    Return authentication state for one provider.
    """

    _ensure_auth_registry()

    provider = auth_provider_registry.get(
        source_name
    )

    if provider is None:
        return {
            "status": "NOT_CONFIGURED",
            "authorized": False,
            "message": (
                "No authentication provider is configured "
                "for this source."
            ),
        }

    status = await provider.get_auth_status()

    return {
        "status": status.status,
        "authorized": status.authorized,
        "message": status.message,
    }


# ------------------------------------------------------------------
# Response helpers
# ------------------------------------------------------------------


def _serialize_source(
    source: Any,
    *,
    authentication: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Convert a JobSource SQLAlchemy object into a JSON-safe response.
    """

    return {
        "id": source.id,
        "name": source.name,
        "display_name": source.display_name,
        "source_type": source.source_type,
        "base_url": source.base_url,
        "search_supported": source.search_supported,
        "job_details_supported": (
            source.job_details_supported
        ),
        "direct_apply_supported": (
            source.direct_apply_supported
        ),
        "application_status_sync_supported": (
            source.application_status_sync_supported
        ),
        "webhook_supported": (
            source.webhook_supported
        ),
        "is_active": source.is_active,
        "health_status": source.health_status,
        "last_sync_at": source.last_sync_at,
        "notes": source.notes,
        "authentication": authentication,
    }


def _ensure_registered_sources(
    service: JobSourceService,
) -> list[Any]:
    """
    Ensure every registered adapter has a corresponding JobSource
    database record.
    """

    sources = []

    for source_name in job_source_registry.list_sources():
        adapter = job_source_registry.get(
            source_name
        )

        if adapter is None:
            continue

        source = service.get_or_create_source(
            name=adapter.source_name,
            display_name=adapter.source_name.title(),
        )

        sources.append(source)

    return sources


# ------------------------------------------------------------------
# List all sources
# ------------------------------------------------------------------


@router.get("")
async def list_job_sources(
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Return all supported job platforms together with their
    current integration and authentication state.
    """

    service = JobSourceService(db)

    sources = _ensure_registered_sources(
        service
    )

    results: list[dict[str, Any]] = []

    for source in sources:
        authentication = await _get_auth_status(
            source.name
        )

        results.append(
            _serialize_source(
                source,
                authentication=authentication,
            )
        )

    return results


# ------------------------------------------------------------------
# Provider onboarding information
# ------------------------------------------------------------------


@router.get("/onboarding")
def get_job_source_onboarding(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Return deployment and onboarding requirements for every
    registered job platform.

    This endpoint intentionally exposes configuration metadata only.
    It never exposes credential values or OAuth tokens.
    """

    results: list[dict[str, Any]] = []

    for metadata in (
        provider_configuration_manager
        .list_onboarding_metadata()
    ):
        configuration = (
            provider_configuration_manager.inspect(
                metadata.provider_name
            )
        )

        onboarding = (
            provider_configuration_manager
            .onboarding_to_public_dict(
                metadata
            )
        )

        results.append(
            {
                "provider": metadata.provider_name,
                "display_name": metadata.display_name,

                "configuration": {
                    "status": (
                        configuration.status.value
                    ),
                    "configured": (
                        configuration.configured
                    ),
                    "partially_configured": (
                        configuration.partially_configured
                    ),
                    "required_environment_variables": (
                        list(
                            configuration
                            .required_environment_variables
                        )
                    ),
                    "missing_environment_variables": (
                        list(
                            configuration
                            .missing_environment_variables
                        )
                    ),
                    "message": (
                        configuration.message
                    ),
                },

                "onboarding": onboarding,
            }
        )

    return {
        "providers": results,
        "total": len(results),
    }


# ------------------------------------------------------------------
# Provider capabilities
# ------------------------------------------------------------------


@router.get("/capabilities")
def get_job_source_capabilities() -> dict[str, Any]:
    """
    Return declared integration capabilities for every registered
    job platform.

    This endpoint exposes capability metadata only. It never exposes
    provider credentials, OAuth tokens, or other secrets.
    """

    source_names = job_source_registry.list_sources()

    return {
        "providers": {
            source_name: capabilities_to_public_dict(
                source_name
            )
            for source_name in source_names
        },
        "total": len(source_names),
    }


# ------------------------------------------------------------------
# Initialize source catalog
# ------------------------------------------------------------------


@router.post("/initialize")
def initialize_job_sources(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Initialize all configured job sources in the database.
    """

    service = JobSourceService(db)

    sources = service.initialize_catalog()

    return {
        "message": (
            "Job source catalog initialized successfully."
        ),
        "sources": [
            _serialize_source(source)
            for source in sources
        ],
        "total": len(sources),
    }


# ------------------------------------------------------------------
# Get one source
# ------------------------------------------------------------------


@router.get("/{source_name}")
async def get_job_source(
    source_name: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Return information about one registered job platform,
    including authentication state.
    """

    if not job_source_registry.has(
        source_name
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Job source '{source_name}' "
                "is not registered."
            ),
        )

    service = JobSourceService(db)

    source = service.get_or_create_source(
        name=source_name,
        display_name=source_name.title(),
    )

    authentication = await _get_auth_status(
        source.name
    )

    return _serialize_source(
        source,
        authentication=authentication,
    )


# ------------------------------------------------------------------
# Check one source health
# ------------------------------------------------------------------


@router.get("/{source_name}/health")
async def check_job_source_health(
    source_name: str,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Run the adapter health check for one platform and return
    authentication state alongside the result.
    """

    if not job_source_registry.has(
        source_name
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Job source '{source_name}' "
                "is not registered."
            ),
        )

    health_service = JobSourceHealthService(
        db
    )

    health_result = (
        await health_service.check_source(
            source_name
        )
    )

    authentication = await _get_auth_status(
        source_name
    )

    health_result["authentication"] = (
        authentication
    )

    return health_result


# ------------------------------------------------------------------
# Check all source health
# ------------------------------------------------------------------


@router.post("/health-check")
async def check_all_job_sources_health(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Run health checks for every registered platform and include
    authentication state for each platform.
    """

    health_service = JobSourceHealthService(
        db
    )

    results = (
        await health_service.check_all_sources()
    )

    for result in results:
        result["authentication"] = (
            await _get_auth_status(
                result["source"]
            )
        )

    return {
        "sources": results,
        "total": len(results),
    }


# ------------------------------------------------------------------
# Synchronize all sources
# ------------------------------------------------------------------


@router.post("/sync-all")
async def sync_all_job_sources(
    query: str | None = Query(
        default=None,
        description="Job search query.",
    ),
    location: str | None = Query(
        default=None,
        description="Preferred job location.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of jobs to retrieve per provider.",
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Synchronize every registered provider independently.

    Providers without an authorized integration are reported rather
    than causing the entire aggregation operation to fail.
    """
    service = JobSourceSyncService(db)

    results = await service.sync_all_sources(
        query=query,
        location=location,
        limit=limit,
    )

    return {
        "query": query,
        "location": location,
        "limit": limit,
        "sources": results,
        "total": len(results),
    }


# ------------------------------------------------------------------
# Synchronize one source
# ------------------------------------------------------------------


@router.post("/{source_name}/sync")
async def sync_job_source(
    source_name: str,
    query: str | None = Query(
        default=None,
        description="Job search query.",
    ),
    location: str | None = Query(
        default=None,
        description="Preferred job location.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of jobs to retrieve.",
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Synchronize jobs from one registered platform.
    """

    if not job_source_registry.has(
        source_name
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Job source '{source_name}' "
                "is not registered."
            ),
        )

    service = JobSourceSyncService(db)

    try:
        jobs = await service.sync_source(
            source_name,
            query=query,
            location=location,
            limit=limit,
        )

    except NotImplementedError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        logger.exception(
            "Job synchronization failed for provider '%s'.",
            source_name,
        )
        raise HTTPException(
            status_code=502,
            detail=(
                f"Failed to synchronize '{source_name}'. "
                "Check server logs for details."
            ),
        )

    return {
        "source": source_name.strip().lower(),
        "query": query,
        "location": location,
        "limit": limit,
        "jobs_ingested": len(jobs),
        "job_ids": [
            job.id
            for job in jobs
            if job.id is not None
        ],
    }

@router.get("/{source_name}/capabilities")
def get_source_capabilities(source_name: str) -> dict[str, Any]:
    """Return the provider's declared capabilities and authorization state."""
    normalized = source_name.strip().lower()

    if not job_source_registry.has(normalized):
        raise HTTPException(
            status_code=404,
            detail=f"Job source '{normalized}' is not registered.",
        )

    return public_capability_report(normalized)
