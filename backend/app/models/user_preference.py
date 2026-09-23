from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    preferred_roles: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    preferred_locations: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    willing_to_relocate: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    experience_level: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    email_application_updates: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    email_recommendations: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
