from typing import Any

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.normalized import NormalizedJob


class NaukriAdapter(JobSourceAdapter):
    """
    Naukri integration boundary.

    Provider-specific authentication and job retrieval will be
    implemented once an authorized integration is available.
    """

    source_name = "naukri"

    async def search_jobs(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> list[NormalizedJob]:
        raise NotImplementedError(
            "Naukri job search requires an authorized Naukri integration."
        )

    async def get_job(
        self,
        external_job_id: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError(
            "Naukri job retrieval requires an authorized Naukri integration."
        )

    async def health_check(self) -> bool:
        return False