from app.utils.time import utc_now
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class JobSourceListing(Base):
    __tablename__ = "job_source_listings"

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_job_id",
            name="uq_job_source_external_job"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    source_id: Mapped[int] = mapped_column(
        ForeignKey("job_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    external_job_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    original_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    source_title: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    source_company_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    raw_description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    raw_payload: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
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

    job = relationship(
        "Job",
        back_populates="source_listings"
    )

    source = relationship(
        "JobSource",
        back_populates="listings"
    )
