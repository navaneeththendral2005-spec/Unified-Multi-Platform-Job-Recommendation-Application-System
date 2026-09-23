"""Add notification preference controls.

Revision ID: a4c2e8f1d7b0
Revises: fd13e98b45f7
"""
from alembic import op
import sqlalchemy as sa

revision = "a4c2e8f1d7b0"
down_revision = "fd13e98b45f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_preferences",
        sa.Column("email_application_updates", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "user_preferences",
        sa.Column("email_recommendations", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.alter_column("user_preferences", "email_application_updates", server_default=None)
    op.alter_column("user_preferences", "email_recommendations", server_default=None)


def downgrade() -> None:
    op.drop_column("user_preferences", "email_recommendations")
    op.drop_column("user_preferences", "email_application_updates")
