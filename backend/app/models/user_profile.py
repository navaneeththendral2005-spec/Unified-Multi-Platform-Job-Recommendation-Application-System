from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    experience_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    education: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    preferred_job_role: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    preferred_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

