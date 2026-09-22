import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# backend directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load backend/.env
load_dotenv(BASE_DIR / ".env")


# ============================================================
# ALEMBIC CONFIGURATION
# ============================================================

config = context.config


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL is not set. "
        "Check backend/.env"
    )

# Set the database URL dynamically
config.set_main_option(
    "sqlalchemy.url",
    DATABASE_URL
)


# ============================================================
# LOGGING
# ============================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================
# IMPORT DATABASE BASE
# ============================================================

from app.database.base import Base


# ============================================================
# IMPORT ALL MODELS
# ============================================================

# Importing models ensures SQLAlchemy registers them
# inside Base.metadata before Alembic autogeneration runs.

from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_preference import UserPreference

from app.models.resume import Resume
from app.models.resume_analysis import ResumeAnalysis

from app.models.skill import Skill
from app.models.skill_alias import SkillAlias

from app.models.user_skill import UserSkill

from app.models.job import Job
from app.models.job_skill import JobSkill

from app.models.application import Application
from app.models.application_status_history import ApplicationStatusHistory
from app.models.application_event import ApplicationEvent
from app.models.company import Company
from app.models.job_source import JobSource
from app.models.job_source_listing import JobSourceListing

# ============================================================
# TARGET METADATA
# ============================================================

target_metadata = Base.metadata


# ============================================================
# OFFLINE MIGRATIONS
# ============================================================

def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = config.get_main_option(
        "sqlalchemy.url"
    )

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================
# ONLINE MIGRATIONS
# ============================================================

def run_migrations_online() -> None:
    """
    Run migrations using a live database connection.
    """

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================
# RUN MIGRATIONS
# ============================================================

if context.is_offline_mode():

    run_migrations_offline()

else:

    run_migrations_online()