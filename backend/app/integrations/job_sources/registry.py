from collections.abc import Iterable

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.linkedin import LinkedInAdapter
from app.integrations.job_sources.naukri import NaukriAdapter
from app.integrations.job_sources.internshala import InternshalaAdapter
from app.integrations.job_sources.indeed import IndeedAdapter
from app.integrations.job_sources.wellfound import WellfoundAdapter


class JobSourceRegistry:
    """
    Runtime registry for all supported external job platforms.
    """

    def __init__(self) -> None:
        self._adapters: dict[str, JobSourceAdapter] = {}

    def register(self, adapter: JobSourceAdapter) -> None:
        source_name = adapter.source_name.strip().lower()

        if not source_name:
            raise ValueError(
                "Job source name cannot be empty."
            )

        if source_name in self._adapters:
            raise ValueError(
                f"Job source '{source_name}' is already registered."
            )

        self._adapters[source_name] = adapter

    def get(
        self,
        source_name: str,
    ) -> JobSourceAdapter | None:
        return self._adapters.get(
            source_name.strip().lower()
        )

    def has(
        self,
        source_name: str,
    ) -> bool:
        return source_name.strip().lower() in self._adapters

    def list_sources(self) -> list[str]:
        return list(self._adapters.keys())

    def all(self) -> Iterable[JobSourceAdapter]:
        return self._adapters.values()


job_source_registry = JobSourceRegistry()


# ------------------------------------------------------------------
# Supported platform registrations
# ------------------------------------------------------------------

job_source_registry.register(
    LinkedInAdapter()
)

job_source_registry.register(
    NaukriAdapter()
)

job_source_registry.register(
    InternshalaAdapter()
)

job_source_registry.register(
    IndeedAdapter()
)

job_source_registry.register(
    WellfoundAdapter()
)