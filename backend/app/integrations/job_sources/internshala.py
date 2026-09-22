from typing import Any

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.normalized import NormalizedJob


class InternshalaAdapter(JobSourceAdapter):
    """
    Internshala integration boundary.

    Provider-specific authentication and job retrieval will be
    implemented once an authorized integration is available.
    """

    source_name = "internshala"

    async def search_jobs(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> list[NormalizedJob]:
        raise NotImplementedError(
            "Internshala job search requires an authorized "
            "Internshala integration."
        )

    async def get_job(
        self,
        external_job_id: str,
    ) -> dict[str, Any] | None:
        raise NotImplementedError(
            "Internshala job retrieval requires an authorized "
            "Internshala integration."
        )

    async def health_check(self) -> bool:
        return False