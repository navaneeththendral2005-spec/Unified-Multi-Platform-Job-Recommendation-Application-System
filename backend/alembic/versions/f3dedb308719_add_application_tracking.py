"""add application tracking

Revision ID: f3dedb308719
Revises: c1bbc60c505e
Create Date: 2026-09-17 11:24:04.143463

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f3dedb308719"
down_revision: Union[str, Sequence[str], None] = "c1bbc60c505e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("source_platform", sa.String(length=100), nullable=True),
        sa.Column("external_application_id", sa.String(length=255), nullable=True),
        sa.Column("application_url", sa.String(length=1000), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(), nullable=False),
        sa.Column("last_status_changed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),
    )

    op.create_index(
        op.f("ix_applications_applied_at"),
        "applications",
        ["applied_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_external_application_id"),
        "applications",
        ["external_application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_id"),
        "applications",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_job_id"),
        "applications",
        ["job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_source_platform"),
        "applications",
        ["source_platform"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_status"),
        "applications",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_user_id"),
        "applications",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "application_status_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_application_status_history_application_id"),
        "application_status_history",
        ["application_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_status_history_changed_at"),
        "application_status_history",
        ["changed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_status_history_id"),
        "application_status_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_application_status_history_new_status"),
        "application_status_history",
        ["new_status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        op.f("ix_application_status_history_new_status"),
        table_name="application_status_history",
    )
    op.drop_index(
        op.f("ix_application_status_history_id"),
        table_name="application_status_history",
    )
    op.drop_index(
        op.f("ix_application_status_history_changed_at"),
        table_name="application_status_history",
    )
    op.drop_index(
        op.f("ix_application_status_history_application_id"),
        table_name="application_status_history",
    )
    op.drop_table("application_status_history")

    op.drop_index(
        op.f("ix_applications_user_id"),
        table_name="applications",
    )
    op.drop_index(
        op.f("ix_applications_status"),
        table_name="applications",
    )
    op.drop_index(
        op.f("ix_applications_source_platform"),
        table_name="applications",
    )
    op.drop_index(
        op.f("ix_applications_job_id"),
        table_name="applications",
    )
    op.drop_index(
        op.f("ix_applications_id"),
        table_name="applications",
    )
    op.drop_index(
        op.f("ix_applications_external_application_id"),
        table_name="applications",
    )
    op.drop_index(
        op.f("ix_applications_applied_at"),
        table_name="applications",
    )
    op.drop_table("applications")
