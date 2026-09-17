from typing import List

from pydantic import BaseModel


class ResumeStructuredData(BaseModel):
    skills: List[str] = []
    education: List[str] = []
    experience: List[str] = []
    projects: List[str] = []


class ResumeParseResponse(BaseModel):
    resume_id: int
    structured_data: ResumeStructuredData