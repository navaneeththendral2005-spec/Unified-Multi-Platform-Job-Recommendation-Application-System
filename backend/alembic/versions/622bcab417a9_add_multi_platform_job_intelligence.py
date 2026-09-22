"""add multi platform job intelligence

Revision ID: 622bcab417a9
Revises: 83a0c41d571c
Create Date: 2026-09-21 00:45:11.648208

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "622bcab417a9"
down_revision: Union[str, Sequence[str], None] = "83a0c41d571c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---------------------------------------------------------
    # Companies
    # ---------------------------------------------------------
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "normalized_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("industry", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_companies_id",
        "companies",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_companies_name",
        "companies",
        ["name"],
        unique=False,
    )

    op.create_index(
        "ix_companies_normalized_name",
        "companies",
        ["normalized_name"],
        unique=True,
    )

    # ---------------------------------------------------------
    # Job Sources
    # ---------------------------------------------------------
    op.create_table(
        "job_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "display_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "source_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "base_url",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "search_supported",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "job_details_supported",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "direct_apply_supported",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "application_status_sync_supported",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "webhook_supported",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "health_status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "last_sync_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_job_sources_id",
        "job_sources",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_job_sources_name",
        "job_sources",
        ["name"],
        unique=True,
    )

    op.create_index(
        "ix_job_sources_is_active",
        "job_sources",
        ["is_active"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Job Source Listings
    # ---------------------------------------------------------
    op.create_table(
        "job_source_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column(
            "external_job_id",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "original_url",
            sa.String(length=1000),
            nullable=True,
        ),
        sa.Column(
            "source_title",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "source_company_name",
            sa.String(length=500),
            nullable=True,
        ),
        sa.Column(
            "raw_description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "raw_payload",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
            name="fk_job_source_listings_job_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["job_sources.id"],
            name="fk_job_source_listings_source_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_id",
            "external_job_id",
            name="uq_job_source_external_job",
        ),
    )

    op.create_index(
        "ix_job_source_listings_id",
        "job_source_listings",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_job_source_listings_job_id",
        "job_source_listings",
        ["job_id"],
        unique=False,
    )

    op.create_index(
        "ix_job_source_listings_source_id",
        "job_source_listings",
        ["source_id"],
        unique=False,
    )

    op.create_index(
        "ix_job_source_listings_external_job_id",
        "job_source_listings",
        ["external_job_id"],
        unique=False,
    )

    op.create_index(
        "ix_job_source_listings_is_active",
        "job_source_listings",
        ["is_active"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Connect existing Jobs to Companies
    # ---------------------------------------------------------
    op.add_column(
        "jobs",
        sa.Column(
            "company_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_jobs_company_id",
        "jobs",
        ["company_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_jobs_company_id",
        "jobs",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove Jobs → Companies relationship
    op.drop_constraint(
        "fk_jobs_company_id",
        "jobs",
        type_="foreignkey",
    )

    op.drop_index(
        "ix_jobs_company_id",
        table_name="jobs",
    )

    op.drop_column(
        "jobs",
        "company_id",
    )

    # Remove Job Source Listings
    op.drop_index(
        "ix_job_source_listings_is_active",
        table_name="job_source_listings",
    )

    op.drop_index(
        "ix_job_source_listings_external_job_id",
        table_name="job_source_listings",
    )

    op.drop_index(
        "ix_job_source_listings_source_id",
        table_name="job_source_listings",
    )

    op.drop_index(
        "ix_job_source_listings_job_id",
        table_name="job_source_listings",
    )

    op.drop_index(
        "ix_job_source_listings_id",
        table_name="job_source_listings",
    )

    op.drop_table("job_source_listings")

    # Remove Job Sources
    op.drop_index(
        "ix_job_sources_is_active",
        table_name="job_sources",
    )

    op.drop_index(
        "ix_job_sources_name",
        table_name="job_sources",
    )

    op.drop_index(
        "ix_job_sources_id",
        table_name="job_sources",
    )

    op.drop_table("job_sources")

    # Remove Companies
    op.drop_index(
        "ix_companies_normalized_name",
        table_name="companies",
    )

    op.drop_index(
        "ix_companies_name",
        table_name="companies",
    )

    op.drop_index(
        "ix_companies_id",
        table_name="companies",
    )

    op.drop_table("companies")