from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    skills: str | None = Field(
        default=None,
        examples=["Python, FastAPI, SQL, Machine Learning"]
    )

    experience_years: int | None = Field(
        default=None,
        ge=0,
        le=50,
        examples=[2]
    )

    education: str | None = Field(
        default=None,
        examples=["Bachelor of Technology in Computer Science"]
    )

    preferred_job_role: str | None = Field(
        default=None,
        examples=["Machine Learning Engineer"]
    )

    preferred_location: str | None = Field(
        default=None,
        examples=["Bangalore"]
    )


class ProfileUpdate(ProfileCreate):
    pass


class ProfileResponse(BaseModel):
    id: int
    user_id: int

    skills: str | None
    experience_years: int | None
    education: str | None
    preferred_job_role: str | None
    preferred_location: str | None

    class Config:
        from_attributes = True