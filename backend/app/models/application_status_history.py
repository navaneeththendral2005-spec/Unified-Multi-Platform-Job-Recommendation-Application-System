from app.utils.time import utc_now
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey(
            "applications.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    old_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    new_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
    )

    changed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False,
        index=True
    )

    # Where did this status update originate?
    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Email/notification processing state.
    notification_sent: Mapped[bool] = mapped_column(
        default=False,
        nullable=False
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    application = relationship(
        "Application",
        back_populates="status_history"
    )