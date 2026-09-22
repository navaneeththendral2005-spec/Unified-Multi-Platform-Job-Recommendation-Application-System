from typing import Any

from app.integrations.job_sources.base import JobSourceAdapter
from app.integrations.job_sources.normalized import NormalizedJob


class LinkedInAdapter(JobSourceAdapter):
    """
    LinkedIn job-source adapter.

    This adapter defines our LinkedIn integration boundary.
    Actual API communication will be added once an authorized
    LinkedIn API integration is available.

    No scraping, browser automation, credential simulation,
    or undocumented endpoints are used here.
    """

    source_name = "linkedin"

    async def search_jobs(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        limit: int = 50,
        **kwargs: Any,
    ) -> list[NormalizedJob]:
        """
        Search LinkedIn jobs through an authorized integration.

        The actual LinkedIn API implementation will be connected
        here later.
        """

        raise NotImplementedError(
            "LinkedIn job search requires an authorized "
            "LinkedIn integration."
        )

    async def get_job(
        self,
        external_job_id: str,
    ) -> dict[str, Any] | None:
        """
        Fetch one LinkedIn job through an authorized integration.
        """

        raise NotImplementedError(
            "LinkedIn job retrieval requires an authorized "
            "LinkedIn integration."
        )

    async def health_check(self) -> bool:
        """
        Check whether the configured LinkedIn integration is usable.
        """

        return False