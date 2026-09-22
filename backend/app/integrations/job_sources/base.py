from abc import ABC, abstractmethod
from typing import ClassVar

from app.integrations.job_sources.normalized import NormalizedJob


class JobSourceAdapter(ABC):
    """
    Base contract for every external job platform.
    """

    source_name: ClassVar[str]

    @abstractmethod
    async def search_jobs(
        self,
        *,
        query: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 20,
        **filters: object,
    ) -> list[NormalizedJob]:
        """Search for jobs on the external platform."""
        raise NotImplementedError

    @abstractmethod
    async def get_job(
        self,
        external_job_id: str,
    ) -> NormalizedJob | None:
        """Fetch a single job from the external platform."""
        raise NotImplementedError

    async def health_check(self) -> bool:
        """Check whether the external source is reachable."""
        return True

    async def close(self) -> None:
        """Release adapter resources."""
        return None