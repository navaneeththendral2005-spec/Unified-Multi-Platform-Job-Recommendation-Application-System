from app.utils.time import utc_now
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class JobSource(Base):
    __tablename__ = "job_sources"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="EXTERNAL"
    )

    base_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # Integration capability flags.
    search_supported: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    job_details_supported: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    direct_apply_supported: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    application_status_sync_supported: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    webhook_supported: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    health_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UNKNOWN"
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    listings = relationship(
        "JobSourceListing",
        back_populates="source",
        cascade="all, delete-orphan"
    )
