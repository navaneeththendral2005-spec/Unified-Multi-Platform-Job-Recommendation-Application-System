"""initial database schema

Revision ID: 66451c8c138e
Revises:
Create Date: 2026-09-14 13:00:11.301055
"""

from typing import Sequence, Union

from alembic import op


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "66451c8c138e"

down_revision: Union[str, Sequence[str], None] = None

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================

def upgrade() -> None:
    """
    Upgrade database schema.
    """

    # ========================================================
    # UPDATE SKILL ALIAS FOREIGN KEY
    # ========================================================

    # Remove the existing foreign key
    op.drop_constraint(
        "skill_aliases_skill_id_fkey",
        "skill_aliases",
        type_="foreignkey"
    )

    # Recreate the foreign key with CASCADE behavior
    op.create_foreign_key(
        "fk_skill_aliases_skill_id_skills",
        "skill_aliases",
        "skills",
        ["skill_id"],
        ["id"],
        ondelete="CASCADE"
    )

    # ========================================================
    # SKILLS CATEGORY INDEX
    # ========================================================

    op.create_index(
        "ix_skills_category",
        "skills",
        ["category"],
        unique=False
    )

    # ========================================================
    # SKILLS NAME UNIQUE INDEX
    # ========================================================

    op.create_index(
        "ix_skills_name",
        "skills",
        ["name"],
        unique=True
    )


# ============================================================
# DOWNGRADE
# ============================================================

def downgrade() -> None:
    """
    Downgrade database schema.
    """

    # ========================================================
    # REMOVE SKILL NAME INDEX
    # ========================================================

    op.drop_index(
        "ix_skills_name",
        table_name="skills"
    )

    # ========================================================
    # REMOVE SKILL CATEGORY INDEX
    # ========================================================

    op.drop_index(
        "ix_skills_category",
        table_name="skills"
    )

    # ========================================================
    # RESTORE ORIGINAL FOREIGN KEY
    # ========================================================

    # Remove the CASCADE foreign key
    op.drop_constraint(
        "fk_skill_aliases_skill_id_skills",
        "skill_aliases",
        type_="foreignkey"
    )

    # Restore the original foreign key
    op.create_foreign_key(
        "skill_aliases_skill_id_fkey",
        "skill_aliases",
        "skills",
        ["skill_id"],
        ["id"]
    )