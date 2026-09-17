from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class UserSkill(Base):
    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # ========================================================
    # TEMPORARY LEGACY FIELD
    # ========================================================

    skill_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    # ========================================================
    # CENTRAL SKILL REGISTRY CONNECTION
    # ========================================================

    skill_id: Mapped[int | None] = mapped_column(
        ForeignKey("skills.id"),
        nullable=True,
        index=True
    )

    # ========================================================
    # RESUME PROVENANCE
    # ========================================================

    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id"),
        nullable=True,
        index=True
    )

    # ========================================================
    # SKILL SOURCE
    # ========================================================

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="resume",
        index=True
    )

    # ========================================================
    # CREATED AT
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    user = relationship(
        "User",
        back_populates="skills"
    )

    skill = relationship(
        "Skill",
        back_populates="user_skills"
    )

    resume = relationship(
        "Resume",
        back_populates="user_skills"
    )