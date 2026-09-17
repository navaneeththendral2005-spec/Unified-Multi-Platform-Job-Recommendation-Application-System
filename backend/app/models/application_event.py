from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey(
            "applications.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # Normalized event name.
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Lifecycle state before the event, when applicable.
    old_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Lifecycle state after the event, when applicable.
    new_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Origin of the event:
    # user, LinkedIn, Naukri, Internshala, internal, etc.
    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Flexible event-specific information.
    # Mapped to the database column named "metadata".
    event_metadata: Mapped[dict | None] = mapped_column(
        "metadata",
        JSON,
        nullable=True,
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    application = relationship(
        "Application",
        back_populates="events",
    )

    user = relationship(
        "User",
    )
