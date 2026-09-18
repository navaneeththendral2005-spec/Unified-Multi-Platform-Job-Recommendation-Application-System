"""Durable notification delivery records."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ApplicationNotification(Base):
    __tablename__ = "application_notifications"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "channel",
            name="uq_application_notification_event_channel",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("application_events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    channel: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    notification_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    recipient: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    subject: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    delivery_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    failed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
    DateTime,
    nullable=True,
    index=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    read_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User")
    application = relationship("Application")
    event = relationship("ApplicationEvent")
