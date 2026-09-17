from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
        default=datetime.utcnow
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
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