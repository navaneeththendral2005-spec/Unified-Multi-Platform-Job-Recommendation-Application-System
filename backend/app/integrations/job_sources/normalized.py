from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NormalizedJob(BaseModel):
    """
    Standardized representation of a job returned by any
    external job platform.

    Every platform adapter must convert its platform-specific
    response into this structure before the job enters the
    recommendation and canonicalization pipeline.
    """

    source_name: str = Field(
        ...,
        description="Internal identifier of the job source.",
    )

    external_job_id: str = Field(
        ...,
        description="Unique job identifier assigned by the source.",
    )

    title: str = Field(
        ...,
        description="Normalized job title.",
    )

    company_name: str = Field(
        ...,
        description="Company name associated with the job.",
    )

    description: str | None = Field(
        default=None,
        description="Normalized job description.",
    )

    location: str | None = Field(
        default=None,
        description="Job location.",
    )

    job_type: str | None = Field(
        default=None,
        description="Employment type such as full-time, internship, etc.",
    )

    experience_required: str | None = Field(
        default=None,
        description="Required experience level.",
    )

    application_url: str | None = Field(
        default=None,
        description="Original application/job URL.",
    )

    posted_at: datetime | None = Field(
        default=None,
        description="Original posting timestamp when available.",
    )

    skills: list[str] = Field(
        default_factory=list,
        description="Skills extracted or provided by the source.",
    )

    raw_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Original source payload for traceability/debugging.",
    )