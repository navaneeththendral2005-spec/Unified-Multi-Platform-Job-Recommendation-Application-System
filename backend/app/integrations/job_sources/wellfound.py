from typing import Any

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.normalized import NormalizedJob


class WellfoundAdapter(JobSourceAdapter):
    """
    Wellfound integration boundary.

    Provider-specific authentication and job retrieval will be
    implemented once an authorized integration is available.
    """

    source_name = "wellfound"

    async def search_jobs(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> list[NormalizedJob]:
        raise NotImplementedError(
            "Wellfound job search requires an authorized Wellfound integration."
        )

    async def get_job(
        self,
        external_job_id: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError(
            "Wellfound job retrieval requires an authorized Wellfound integration."
        )

    async def health_check(self) -> bool:
        return False