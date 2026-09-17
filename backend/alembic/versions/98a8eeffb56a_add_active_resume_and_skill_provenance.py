"""add active resume and skill provenance

Revision ID: 98a8eeffb56a
Revises: f9db7deeb1cb
Create Date: 2026-09-15 11:51:59.283412

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "98a8eeffb56a"
down_revision: Union[str, Sequence[str], None] = "f9db7deeb1cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add active resume tracking and user-skill resume provenance."""

    # ========================================================
    # 1. ADD RESUME ACTIVE FLAG
    # ========================================================

    op.add_column(
        "resumes",
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )

    # ========================================================
    # 2. ADD RESUME PROVENANCE TO USER SKILLS
    # ========================================================

    op.add_column(
        "user_skills",
        sa.Column(
            "resume_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    # ========================================================
    # 3. ADD FOREIGN KEY
    # ========================================================

    op.create_foreign_key(
        "fk_user_skills_resume_id",
        "user_skills",
        "resumes",
        ["resume_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ========================================================
    # 4. INDEX USER SKILL RESUME PROVENANCE
    # ========================================================

    op.create_index(
        "ix_user_skills_resume_id",
        "user_skills",
        ["resume_id"],
        unique=False,
    )

    # ========================================================
    # 5. MARK ALL EXISTING RESUMES INACTIVE
    # ========================================================

    op.execute(
        """
        UPDATE resumes
        SET is_active = FALSE
        """
    )

    # ========================================================
    # 6. MARK LATEST RESUME FOR EACH USER AS ACTIVE
    # ========================================================

    op.execute(
        """
        UPDATE resumes
        SET is_active = TRUE
        WHERE id IN (
            SELECT DISTINCT ON (user_id) id
            FROM resumes
            ORDER BY user_id, uploaded_at DESC, id DESC
        )
        """
    )

    # ========================================================
    # 7. CONNECT EXISTING RESUME-SOURCED SKILLS
    #    TO THE RESUME THAT PRODUCED THEM
    #
    #    The current application creates UserSkill records
    #    immediately before the Resume record is flushed.
    #    Therefore we use a small timestamp window.
    #
    #    Existing legacy records remain resume_id = NULL.
    # ========================================================

    op.execute(
        """
        UPDATE user_skills us
        SET resume_id = r.id
        FROM resumes r
        WHERE us.source = 'resume'
          AND us.user_id = r.user_id
          AND us.created_at >= r.uploaded_at - INTERVAL '1 minute'
          AND us.created_at <= r.uploaded_at + INTERVAL '1 minute'
        """
    )

    # ========================================================
    # 8. REMOVE TEMPORARY SERVER DEFAULT
    # ========================================================

    op.alter_column(
        "resumes",
        "is_active",
        server_default=None,
    )

    # ========================================================
    # 9. DATABASE-LEVEL PROTECTION:
    #    ONLY ONE ACTIVE RESUME PER USER
    # ========================================================

    op.create_index(
        "uq_resumes_one_active_per_user",
        "resumes",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )


def downgrade() -> None:
    """Remove active resume tracking and skill provenance."""

    # ========================================================
    # 1. REMOVE UNIQUE ACTIVE-RESUME INDEX
    # ========================================================

    op.drop_index(
        "uq_resumes_one_active_per_user",
        table_name="resumes",
    )

    # ========================================================
    # 2. REMOVE USER-SKILL RESUME INDEX
    # ========================================================

    op.drop_index(
        "ix_user_skills_resume_id",
        table_name="user_skills",
    )

    # ========================================================
    # 3. REMOVE FOREIGN KEY
    # ========================================================

    op.drop_constraint(
        "fk_user_skills_resume_id",
        "user_skills",
        type_="foreignkey",
    )

    # ========================================================
    # 4. REMOVE RESUME PROVENANCE
    # ========================================================

    op.drop_column(
        "user_skills",
        "resume_id",
    )

    # ========================================================
    # 5. REMOVE ACTIVE FLAG
    # ========================================================

    op.drop_column(
        "resumes",
        "is_active",
    )