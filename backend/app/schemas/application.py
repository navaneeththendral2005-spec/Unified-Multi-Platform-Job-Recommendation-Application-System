from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    job_id: int = Field(gt=0)
    source_platform: str | None = Field(default=None, max_length=100)
    external_application_id: str | None = Field(default=None, max_length=255)
    application_url: str | None = Field(default=None, max_length=1000)
    notes: str | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(min_length=1, max_length=50)
    notes: str | None = None


class JobSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str | None
    job_type: str | None
    experience_required: str | None
    application_link: str | None


class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    job_id: int
    job: JobSummaryResponse
    status: str
    source_platform: str | None
    external_application_id: str | None
    application_url: str | None
    notes: str | None
    applied_at: datetime
    last_status_changed_at: datetime
    created_at: datetime
    updated_at: datetime


class ApplicationStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    old_status: str | None
    new_status: str
    changed_at: datetime
    source: str | None
    notes: str | None
    notification_sent: bool


class ApplicationLifecycleStatus(BaseModel):
    status: str
    label: str
    terminal: bool
    allowed_next_statuses: list[str]


class ApplicationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    user_id: int
    event_type: str
    old_status: str | None
    new_status: str | None
    source: str | None
    occurred_at: datetime
    metadata: dict | None = Field(
        default=None,
        validation_alias="event_metadata",
    )


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ApplicationStatusCount(BaseModel):
    status: str
    count: int


class ApplicationSummaryResponse(BaseModel):
    total: int
    by_status: list[ApplicationStatusCount]
    active: int
    terminal: int


class ApplicationTimelineResponse(BaseModel):
    application: ApplicationResponse
    history: list[ApplicationStatusHistoryResponse]
    events: list[ApplicationEventResponse]
