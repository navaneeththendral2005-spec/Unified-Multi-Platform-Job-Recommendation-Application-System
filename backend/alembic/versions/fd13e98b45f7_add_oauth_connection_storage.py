"""add oauth connection storage

Revision ID: fd13e98b45f7
Revises: 622bcab417a9
Create Date: 2026-09-21 15:09:39.556139

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "fd13e98b45f7"
down_revision: Union[str, Sequence[str], None] = "622bcab417a9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create OAuth connection and OAuth state storage."""

    op.create_table(
        "oauth_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text(), nullable=False),
        sa.Column("refresh_token_encrypted", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "provider",
            name="uq_oauth_connection_user_provider",
        ),
    )

    op.create_index(
        op.f("ix_oauth_connections_id"),
        "oauth_connections",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_oauth_connections_user_id"),
        "oauth_connections",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_oauth_connections_provider"),
        "oauth_connections",
        ["provider"],
        unique=False,
    )

    op.create_index(
        op.f("ix_oauth_connections_is_active"),
        "oauth_connections",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_oauth_states_id"),
        "oauth_states",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_oauth_states_state"),
        "oauth_states",
        ["state"],
        unique=True,
    )

    op.create_index(
        op.f("ix_oauth_states_user_id"),
        "oauth_states",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_oauth_states_provider"),
        "oauth_states",
        ["provider"],
        unique=False,
    )


def downgrade() -> None:
    """Remove OAuth connection and OAuth state storage."""

    op.drop_index(
        op.f("ix_oauth_states_provider"),
        table_name="oauth_states",
    )

    op.drop_index(
        op.f("ix_oauth_states_user_id"),
        table_name="oauth_states",
    )

    op.drop_index(
        op.f("ix_oauth_states_state"),
        table_name="oauth_states",
    )

    op.drop_index(
        op.f("ix_oauth_states_id"),
        table_name="oauth_states",
    )

    op.drop_table("oauth_states")

    op.drop_index(
        op.f("ix_oauth_connections_is_active"),
        table_name="oauth_connections",
    )

    op.drop_index(
        op.f("ix_oauth_connections_provider"),
        table_name="oauth_connections",
    )

    op.drop_index(
        op.f("ix_oauth_connections_user_id"),
        table_name="oauth_connections",
    )

    op.drop_index(
        op.f("ix_oauth_connections_id"),
        table_name="oauth_connections",
    )

    op.drop_table("oauth_connections")