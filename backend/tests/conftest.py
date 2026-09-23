import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import Session


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Keep production configuration strict while providing an isolated
# SQLite database for local pytest runs when DATABASE_URL is not set.
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///./pytest_test.db",
)

os.environ.setdefault(
    "SECRET_KEY",
    "test-secret-key-for-local-pytest-only-32-chars",
)


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    """Create the SQLAlchemy test schema once for the test session."""
    from app.database.base import Base
    import app.models  # noqa: F401 - register model metadata
    from app.models.company import Company  # noqa: F401
    from app.models.job_source import JobSource  # noqa: F401
    from app.models.job_source_listing import JobSourceListing  # noqa: F401

    from app.database.connection import engine

    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(create_test_schema):
    """
    Provide a database session using the project's existing SQLAlchemy engine.

    Each test runs inside an outer transaction which is rolled back after the
    test, keeping test data isolated from the rest of the test session.
    """
    from app.database.connection import engine

    connection = engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
