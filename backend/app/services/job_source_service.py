from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.job_source import JobSource

from app.services.job_source_catalog import JOB_SOURCE_CATALOG
from app.utils.time import utc_now


class JobSourceService:
    """
    Central service for managing external job-source configuration,
    capabilities, activation state, and health information.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Source lookup
    # ------------------------------------------------------------------

    def get_source(
        self,
        source_name: str,
    ) -> JobSource | None:
        """
        Retrieve a job source by its normalized name.
        """

        normalized_name = self._normalize_name(source_name)

        return self.db.scalar(
            select(JobSource).where(
                JobSource.name == normalized_name
            )
        )

    def get_active_sources(self) -> list[JobSource]:
        """
        Return all currently active job sources.
        """

        return list(
            self.db.scalars(
                select(JobSource)
                .where(JobSource.is_active.is_(True))
                .order_by(JobSource.name)
            ).all()
        )

    def get_all_sources(self) -> list[JobSource]:
        """
        Return all registered job sources.
        """

        return list(
            self.db.scalars(
                select(JobSource)
                .order_by(JobSource.name)
            ).all()
        )

    # ------------------------------------------------------------------
    # Source creation / registration
    # ------------------------------------------------------------------

    def get_or_create_source(
        self,
        *,
        name: str,
        display_name: str | None = None,
        source_type: str = "EXTERNAL",
        base_url: str | None = None,
        notes: str | None = None,
    ) -> JobSource:
        """
        Resolve an existing source or create a new source definition.
        """

        normalized_name = self._normalize_name(name)

        source = self.get_source(normalized_name)

        if source:
            return source

        source = JobSource(
            name=normalized_name,
            display_name=(
                display_name.strip()
                if display_name
                else normalized_name.title()
            ),
            source_type=source_type,
            base_url=base_url,
            notes=notes,
            is_active=True,
            health_status="UNKNOWN",
        )

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        return source

    # ------------------------------------------------------------------
    # Source activation
    # ------------------------------------------------------------------

    def activate_source(
        self,
        source_name: str,
    ) -> JobSource:
        """
        Activate a registered source.
        """

        source = self._require_source(source_name)

        source.is_active = True

        self.db.commit()
        self.db.refresh(source)

        return source

    def deactivate_source(
        self,
        source_name: str,
    ) -> JobSource:
        """
        Deactivate a registered source.

        Deactivation does not delete historical listings or jobs.
        """

        source = self._require_source(source_name)

        source.is_active = False

        self.db.commit()
        self.db.refresh(source)

        return source

    # ------------------------------------------------------------------
    # Capability management
    # ------------------------------------------------------------------

    def update_capabilities(
        self,
        source_name: str,
        *,
        search_supported: bool | None = None,
        job_details_supported: bool | None = None,
        direct_apply_supported: bool | None = None,
        application_status_sync_supported: bool | None = None,
        webhook_supported: bool | None = None,
    ) -> JobSource:
        """
        Update the capabilities supported by a source.

        Only explicitly provided values are changed.
        """

        source = self._require_source(source_name)

        if search_supported is not None:
            source.search_supported = search_supported

        if job_details_supported is not None:
            source.job_details_supported = job_details_supported

        if direct_apply_supported is not None:
            source.direct_apply_supported = (
                direct_apply_supported
            )

        if application_status_sync_supported is not None:
            source.application_status_sync_supported = (
                application_status_sync_supported
            )

        if webhook_supported is not None:
            source.webhook_supported = webhook_supported

        self.db.commit()
        self.db.refresh(source)

        return source

    # ------------------------------------------------------------------
    # Health management
    # ------------------------------------------------------------------

    def update_health(
        self,
        source_name: str,
        *,
        health_status: str,
        last_sync_at: datetime | None = None,
    ) -> JobSource:
        """
        Update source health information.

        Typical health values can include:

        - UNKNOWN
        - HEALTHY
        - DEGRADED
        - UNAVAILABLE
        - AUTHORIZATION_REQUIRED
        """

        source = self._require_source(source_name)

        source.health_status = health_status.strip().upper()

        if last_sync_at is not None:
            source.last_sync_at = last_sync_at

        self.db.commit()
        self.db.refresh(source)

        return source

    def mark_sync_success(
        self,
        source_name: str,
        *,
        synced_at: datetime | None = None,
    ) -> JobSource:
        """
        Mark a source as healthy after a successful synchronization.
        """

        return self.update_health(
            source_name,
            health_status="HEALTHY",
            last_sync_at=synced_at or utc_now(),
        )

    def mark_sync_unavailable(
        self,
        source_name: str,
    ) -> JobSource:
        """
        Mark a source as unavailable.
        """

        return self.update_health(
            source_name,
            health_status="UNAVAILABLE",
        )

    def mark_authorization_required(
        self,
        source_name: str,
    ) -> JobSource:
        """
        Mark a source as requiring provider authorization or credentials.
        """

        return self.update_health(
            source_name,
            health_status="AUTHORIZATION_REQUIRED",
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_source(
        self,
        source_name: str,
    ) -> JobSource:
        source = self.get_source(source_name)

        if source is None:
            raise ValueError(
                f"Job source '{source_name}' is not registered."
            )

        return source

    @staticmethod
    def _normalize_name(
        source_name: str,
    ) -> str:
        normalized = source_name.strip().lower()

        if not normalized:
            raise ValueError(
                "Job source name cannot be empty."
            )

        return normalized
    
    def initialize_catalog(self) -> list[JobSource]:
        """
        Initialize or update the configured external job sources.

        Existing source records are updated rather than duplicated.
        """

        sources: list[JobSource] = []

        for config in JOB_SOURCE_CATALOG:
            source = self.get_source(config["name"])

            if source is None:
                source = JobSource(
                    name=config["name"],
                    display_name=config["display_name"],
                    source_type=config["source_type"],
                    base_url=config["base_url"],
                    search_supported=config["search_supported"],
                    job_details_supported=config[
                        "job_details_supported"
                    ],
                    direct_apply_supported=config[
                        "direct_apply_supported"
                    ],
                    application_status_sync_supported=config[
                        "application_status_sync_supported"
                    ],
                    webhook_supported=config[
                        "webhook_supported"
                    ],
                    is_active=config["is_active"],
                    health_status=config["health_status"],
                    notes=config["notes"],
                )

                self.db.add(source)

            else:
                source.display_name = config["display_name"]
                source.source_type = config["source_type"]
                source.base_url = config["base_url"]
                source.search_supported = config[
                    "search_supported"
                ]
                source.job_details_supported = config[
                    "job_details_supported"
                ]
                source.direct_apply_supported = config[
                    "direct_apply_supported"
                ]
                source.application_status_sync_supported = config[
                    "application_status_sync_supported"
                ]
                source.webhook_supported = config[
                    "webhook_supported"
                ]
                source.is_active = config["is_active"]
                source.health_status = config["health_status"]
                source.notes = config["notes"]

            sources.append(source)

        self.db.commit()

        for source in sources:
            self.db.refresh(source)

        return sources

    