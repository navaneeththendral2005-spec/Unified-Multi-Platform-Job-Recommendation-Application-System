from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SkillAlias(Base):
    """
    Alternative names that map to a canonical Skill.
    """

    __tablename__ = "skill_aliases"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    # ========================================================
    # ORIGINAL ALIAS
    # ========================================================

    alias: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # ========================================================
    # NORMALIZED ALIAS
    # ========================================================

    normalized_alias: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True
    )

    # ========================================================
    # MASTER SKILL
    # ========================================================

    skill_id: Mapped[int] = mapped_column(
        ForeignKey(
            "skills.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ========================================================
    # TIMESTAMP
    # ========================================================

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ========================================================
    # RELATIONSHIP
    # ========================================================

    skill = relationship(
        "Skill",
        back_populates="aliases"
    )