import sys
from pathlib import Path

import pytest
from sqlalchemy.orm import Session


BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture
def db_session():
    """
    Provide a database session using the project's existing
    SQLAlchemy engine.

    Each test runs inside an outer transaction which is rolled
    back after the test, keeping test data out of the database.
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