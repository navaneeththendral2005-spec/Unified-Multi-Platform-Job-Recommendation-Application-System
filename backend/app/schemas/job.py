from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobBase(BaseModel):
    title: str
    company: str
    description: str
    required_skills: Optional[str] = None
    location: Optional[str] = None
    job_type: Optional[str] = None
    experience_required: Optional[str] = None
    application_link: Optional[str] = None


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True