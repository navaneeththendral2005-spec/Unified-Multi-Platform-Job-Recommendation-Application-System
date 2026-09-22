from datetime import datetime

from sqlalchemy.orm import Session

from app.integrations.auth.provider_configuration import (
    provider_configuration_manager,
)
from app.integrations.auth.provider_readiness import (
    provider_readiness_service,
)
from app.integrations.job_sources.registry import job_source_registry
from app.services.job_source_service import JobSourceService
from app.utils.time import utc_now


class JobSourceHealthService:
    """
    Runs health checks for registered job-source adapters and
    synchronizes their health state with JobSource records.

    Provider configuration and readiness are evaluated before and
    during adapter health checks so every provider is handled
    independently.

    One provider failing must never prevent another provider from
    being evaluated.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.source_service = JobSourceService(db)

    # ------------------------------------------------------------------
    # Check one source
    # ------------------------------------------------------------------

    async def check_source(
        self,
        source_name: str,
    ) -> dict:
        """
        Check one registered job source.

        The check is performed in three stages:

        1. Validate provider configuration.
        2. Run the provider adapter health check.
        3. Calculate the unified provider readiness state.
        """

        normalized_name = source_name.strip().lower()

        # --------------------------------------------------------------
        # Provider adapter
        # --------------------------------------------------------------

        adapter = job_source_registry.get(
            normalized_name
        )

        if adapter is None:
            raise ValueError(
                f"Job source '{normalized_name}' is not registered."
            )

        # --------------------------------------------------------------
        # Database source record
        # --------------------------------------------------------------

        source = self.source_service.get_source(
            normalized_name
        )

        if source is None:
            source = self.source_service.get_or_create_source(
                name=adapter.source_name,
                display_name=adapter.source_name.title(),
            )

        # --------------------------------------------------------------
        # Provider configuration
        # --------------------------------------------------------------

        configuration = (
            provider_configuration_manager.inspect(
                normalized_name
            )
        )

        configuration_public = (
            provider_configuration_manager.to_public_dict(
                configuration
            )
        )

        # --------------------------------------------------------------
        # Credentials are missing/incomplete
        # --------------------------------------------------------------

        if configuration.status.value in {
            "NOT_CONFIGURED",
            "PARTIALLY_CONFIGURED",
        }:

            self.source_service.update_health(
                normalized_name,
                health_status="CONFIGURATION_REQUIRED",
            )

            readiness = provider_readiness_service.inspect(
                normalized_name,
                authorized=False,
            )

            return {
                "source": source.name,
                "status": "CONFIGURATION_REQUIRED",
                "healthy": False,
                "configuration": configuration_public,
                "readiness": (
                    provider_readiness_service.to_public_dict(
                        readiness
                    )
                ),
            }

        # --------------------------------------------------------------
        # Provider credentials exist.
        #
        # Now determine whether the actual provider adapter is
        # authorized/available.
        # --------------------------------------------------------------

        try:
            is_healthy = await adapter.health_check()

            # ----------------------------------------------------------
            # Provider is available and authorized
            # ----------------------------------------------------------

            if is_healthy:

                source = self.source_service.mark_sync_success(
                    normalized_name,
                    synced_at=utc_now(),
                )

                readiness = provider_readiness_service.inspect(
                    normalized_name,
                    authorized=True,
                )

                return {
                    "source": source.name,
                    "status": "HEALTHY",
                    "healthy": True,
                    "configuration": configuration_public,
                    "readiness": (
                        provider_readiness_service.to_public_dict(
                            readiness
                        )
                    ),
                }

            # ----------------------------------------------------------
            # Credentials exist, but provider authorization is not
            # currently confirmed.
            # ----------------------------------------------------------

            source = (
                self.source_service
                .mark_authorization_required(
                    normalized_name
                )
            )

            readiness = provider_readiness_service.inspect(
                normalized_name,
                authorized=False,
            )

            return {
                "source": source.name,
                "status": "AUTHORIZATION_REQUIRED",
                "healthy": False,
                "configuration": configuration_public,
                "readiness": (
                    provider_readiness_service.to_public_dict(
                        readiness
                    )
                ),
            }

        # --------------------------------------------------------------
        # Adapter exists but its real provider integration has not
        # been implemented/authorized yet.
        # --------------------------------------------------------------

        except NotImplementedError:

            source = (
                self.source_service
                .mark_authorization_required(
                    normalized_name
                )
            )

            readiness = provider_readiness_service.inspect(
                normalized_name,
                authorized=False,
            )

            return {
                "source": source.name,
                "status": "AUTHORIZATION_REQUIRED",
                "healthy": False,
                "configuration": configuration_public,
                "readiness": (
                    provider_readiness_service.to_public_dict(
                        readiness
                    )
                ),
            }

        # --------------------------------------------------------------
        # Unexpected provider error
        # --------------------------------------------------------------

        except Exception as exc:

            source = self.source_service.update_health(
                normalized_name,
                health_status="UNAVAILABLE",
            )

            readiness = provider_readiness_service.inspect(
                normalized_name,
                authorized=False,
                unavailable=True,
            )

            return {
                "source": source.name,
                "status": "UNAVAILABLE",
                "healthy": False,
                "error": str(exc),
                "configuration": configuration_public,
                "readiness": (
                    provider_readiness_service.to_public_dict(
                        readiness
                    )
                ),
            }

    # ------------------------------------------------------------------
    # Check every source
    # ------------------------------------------------------------------

    async def check_all_sources(self) -> list[dict]:
        """
        Check every registered job-source adapter.

        Each provider is evaluated independently.

        If one provider fails, the remaining providers continue to
        be checked.
        """

        results: list[dict] = []

        for source_name in job_source_registry.list_sources():

            try:
                result = await self.check_source(
                    source_name
                )

            except Exception as exc:

                # ------------------------------------------------------
                # Last-resort provider isolation.
                # ------------------------------------------------------

                result = {
                    "source": source_name,
                    "status": "UNAVAILABLE",
                    "healthy": False,
                    "error": str(exc),
                    "readiness": {
                        "provider": source_name,
                        "configuration": "UNKNOWN",
                        "authentication": (
                            "NOT_AUTHORIZED"
                        ),
                        "readiness": "UNAVAILABLE",
                        "configured": False,
                        "authorized": False,
                        "ready": False,
                        "auth_type": None,
                        "message": (
                            "Provider health check failed "
                            "unexpectedly."
                        ),
                    },
                }

            results.append(result)

        return results