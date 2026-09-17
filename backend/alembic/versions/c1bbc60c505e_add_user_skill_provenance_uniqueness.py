"""add user skill provenance uniqueness

Revision ID: c1bbc60c505e
Revises: seed_skill_registry_01
Create Date: 2026-09-15 22:11:36.294305

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1bbc60c505e"
down_revision: Union[str, Sequence[str], None] = "seed_skill_registry_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce user skill uniqueness based on provenance.

    Resume-derived skills:
        One skill can exist once per user per resume.

    Profile/manual/legacy skills:
        One skill can exist once per user when it has no resume provenance.
    """

    # ---------------------------------------------------------
    # 1. Resume-derived skill uniqueness
    # ---------------------------------------------------------
    #
    # Prevents duplicate records such as:
    #
    # user_id=7, skill_id=11, resume_id=35
    # user_id=7, skill_id=11, resume_id=35
    #
    # But allows the same skill to appear in different resumes:
    #
    # user_id=7, skill_id=11, resume_id=34
    # user_id=7, skill_id=11, resume_id=35
    #
    op.create_index(
        "uq_user_skills_resume_provenance",
        "user_skills",
        ["user_id", "skill_id", "resume_id"],
        unique=True,
        postgresql_where=sa.text("resume_id IS NOT NULL"),
    )

    # ---------------------------------------------------------
    # 2. Profile/manual/legacy skill uniqueness
    # ---------------------------------------------------------
    #
    # resume_id IS NULL means the skill has no resume provenance.
    #
    # This prevents:
    #
    # user_id=7, skill_id=11, resume_id=NULL
    # user_id=7, skill_id=11, resume_id=NULL
    #
    # while still allowing the same skill to exist on separate
    # resumes through the index above.
    #
    op.create_index(
        "uq_user_skills_profile_skill",
        "user_skills",
        ["user_id", "skill_id"],
        unique=True,
        postgresql_where=sa.text("resume_id IS NULL"),
    )


def downgrade() -> None:
    """Remove user skill provenance uniqueness constraints."""

    op.drop_index(
        "uq_user_skills_profile_skill",
        table_name="user_skills",
    )

    op.drop_index(
        "uq_user_skills_resume_provenance",
        table_name="user_skills",
    )