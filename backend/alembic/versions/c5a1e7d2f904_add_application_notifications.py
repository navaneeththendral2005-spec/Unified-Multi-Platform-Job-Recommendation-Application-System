"""add application notifications

Revision ID: c5a1e7d2f904
Revises: 9b4fcb69ad3a
Create Date: 2026-09-17 18:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c5a1e7d2f904"
down_revision: Union[str, None] = "9b4fcb69ad3a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("notification_type", sa.String(length=100), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("delivery_status", sa.String(length=30), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("failed_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["application_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id",
            "channel",
            name="uq_application_notification_event_channel",
        ),
    )

    op.create_index(
        "ix_application_notifications_id",
        "application_notifications",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_user_id",
        "application_notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_application_id",
        "application_notifications",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_event_id",
        "application_notifications",
        ["event_id"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_channel",
        "application_notifications",
        ["channel"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_notification_type",
        "application_notifications",
        ["notification_type"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_delivery_status",
        "application_notifications",
        ["delivery_status"],
        unique=False,
    )
    op.create_index(
        "ix_application_notifications_created_at",
        "application_notifications",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_application_notifications_created_at",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_delivery_status",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_notification_type",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_channel",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_event_id",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_application_id",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_user_id",
        table_name="application_notifications",
    )
    op.drop_index(
        "ix_application_notifications_id",
        table_name="application_notifications",
    )
    op.drop_table("application_notifications")
