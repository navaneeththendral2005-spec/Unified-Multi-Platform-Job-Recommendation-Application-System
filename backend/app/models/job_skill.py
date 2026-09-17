from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class JobSkill(Base):
    __tablename__ = "job_skills"

    __table_args__ = (
        UniqueConstraint(
            "job_id",
            "skill_id",
            name="uq_job_skill"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        index=True
    )

    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id"),
        nullable=False,
        index=True
    )

    job = relationship(
        "Job",
        back_populates="job_skills"
    )

    skill = relationship(
        "Skill",
        back_populates="job_skills"
    )