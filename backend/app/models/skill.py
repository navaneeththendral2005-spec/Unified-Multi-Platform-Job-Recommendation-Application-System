from app.utils.time import utc_now
from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Skill(Base):
    """
    Master registry for canonical technical and professional skills.
    """

    __tablename__ = "skills"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # DISPLAY NAME
    # ========================================================

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # ========================================================
    # CANONICAL NORMALIZED NAME
    # ========================================================

    normalized_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # ========================================================
    # SKILL CATEGORY
    # ========================================================

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    # Jobs that require this skill
    job_skills = relationship(
        "JobSkill",
        back_populates="skill"
    )

    # Users that possess this skill
    user_skills = relationship(
        "UserSkill",
        back_populates="skill"
    )

    # Alternative names for this skill
    aliases = relationship(
        "SkillAlias",
        back_populates="skill",
        cascade="all, delete-orphan"
    )