"""add notification retry scheduling

Revision ID: 83a0c41d571c
Revises: c5a1e7d2f904
Create Date: 2026-09-18 23:57:40.642090

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "83a0c41d571c"
down_revision: Union[str, Sequence[str], None] = "c5a1e7d2f904"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add retry scheduling support to application notifications."""

    op.add_column(
        "application_notifications",
        sa.Column(
            "next_attempt_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_application_notifications_next_attempt_at",
        "application_notifications",
        ["next_attempt_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove retry scheduling support."""

    op.drop_index(
        "ix_application_notifications_next_attempt_at",
        table_name="application_notifications",
    )

    op.drop_column(
        "application_notifications",
        "next_attempt_at",
    )