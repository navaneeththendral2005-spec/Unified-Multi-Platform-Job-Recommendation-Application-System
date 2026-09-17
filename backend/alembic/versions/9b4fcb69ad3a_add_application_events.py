"""add application events

Revision ID: 9b4fcb69ad3a
Revises: f3dedb308719
Create Date: 2026-09-17 16:12:58.717312

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b4fcb69ad3a"
down_revision: Union[str, Sequence[str], None] = "f3dedb308719"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the application events table."""

    op.create_table(
        "application_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),

        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_application_events_application_id",
        "application_events",
        ["application_id"],
        unique=False,
    )

    op.create_index(
        "ix_application_events_event_type",
        "application_events",
        ["event_type"],
        unique=False,
    )

    op.create_index(
        "ix_application_events_id",
        "application_events",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_application_events_occurred_at",
        "application_events",
        ["occurred_at"],
        unique=False,
    )

    op.create_index(
        "ix_application_events_source",
        "application_events",
        ["source"],
        unique=False,
    )

    op.create_index(
        "ix_application_events_user_id",
        "application_events",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the application events table."""

    op.drop_index(
        "ix_application_events_user_id",
        table_name="application_events",
    )

    op.drop_index(
        "ix_application_events_source",
        table_name="application_events",
    )

    op.drop_index(
        "ix_application_events_occurred_at",
        table_name="application_events",
    )

    op.drop_index(
        "ix_application_events_id",
        table_name="application_events",
    )

    op.drop_index(
        "ix_application_events_event_type",
        table_name="application_events",
    )

    op.drop_index(
        "ix_application_events_application_id",
        table_name="application_events",
    )

    op.drop_table("application_events")