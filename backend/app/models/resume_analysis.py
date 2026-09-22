from app.utils.time import utc_now
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    resume_id: Mapped[int] = mapped_column(
        ForeignKey("resumes.id"),
        nullable=False,
        unique=True,
        index=True
    )

    # ========================================================
    # EDUCATION
    # ========================================================

    education: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # EXPERIENCE
    # ========================================================

    experience: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # PROJECTS
    # ========================================================

    projects: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # CERTIFICATIONS
    # ========================================================

    certifications: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # ACHIEVEMENTS
    # ========================================================

    achievements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # KEY STRENGTHS
    # ========================================================

    key_strengths: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # LANGUAGES
    # ========================================================

    languages: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # SUGGESTED JOB ROLES
    # ========================================================

    suggested_roles: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # ========================================================
    # ANALYSIS TIMESTAMP
    # ========================================================

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now
    )

        # ========================================================
    # RELATIONSHIPS
    # ========================================================

    resume = relationship(
        "Resume",
        back_populates="analyses"
    )