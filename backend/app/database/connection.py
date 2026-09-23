import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Find the backend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load backend/.env explicitly
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set. Check backend/.env")


def _pool_options() -> dict:
    """Build conservative production pool settings from environment."""
    options = {
        "pool_pre_ping": True,
    }

    pool_recycle = os.getenv("DB_POOL_RECYCLE_SECONDS", "1800").strip()

    try:
        options["pool_recycle"] = max(0, int(pool_recycle))
    except ValueError:
        options["pool_recycle"] = 1800

    return options


engine = create_engine(
    DATABASE_URL,
    **_pool_options(),
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
