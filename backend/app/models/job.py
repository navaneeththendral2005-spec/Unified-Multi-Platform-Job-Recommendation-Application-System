from app.utils.time import utc_now
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text

from app.database.base import Base


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    company_id: Mapped[int | None] = mapped_column(
    ForeignKey("companies.id", ondelete="SET NULL"),
    nullable=True,
    index=True
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    required_skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    job_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    experience_required: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    application_link: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    posted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )

    job_skills = relationship(
        "JobSkill",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    applications = relationship(
        "Application",
        back_populates="job",
        cascade="all, delete-orphan"
    )

    source_listings = relationship(
    "JobSourceListing",
    back_populates="job",
    cascade="all, delete-orphan"
    )

    company_entity = relationship(
    "Company",
    back_populates="jobs"
    )