"""add skill source to user skills

Revision ID: f9db7deeb1cb
Revises: 66451c8c138e
Create Date: 2026-09-14 22:50:31.520980

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9db7deeb1cb'
down_revision: Union[str, Sequence[str], None] = '66451c8c138e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # --------------------------------------------------------
    # STEP 1: ADD COLUMN TEMPORARILY AS NULLABLE
    # --------------------------------------------------------

    op.add_column(
        "user_skills",
        sa.Column(
            "source",
            sa.String(length=20),
            nullable=True
        )
    )

    # --------------------------------------------------------
    # STEP 2: UPDATE EXISTING RECORDS
    # --------------------------------------------------------

    op.execute(
        """
        UPDATE user_skills
        SET source = 'legacy'
        WHERE source IS NULL
        """
    )

    # --------------------------------------------------------
    # STEP 3: MAKE COLUMN REQUIRED
    # --------------------------------------------------------

    op.alter_column(
        "user_skills",
        "source",
        existing_type=sa.String(length=20),
        nullable=False
    )
