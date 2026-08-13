from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Initialize SQLAlchemy Database Engine dynamically using DATABASE_URL from .env
if settings.DATABASE_URL:
    # pool_pre_ping=True checks connection liveness (prevents stale connections with Supabase)
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
else:
    engine = None
    SessionLocal = None


def get_db() -> Generator:
    """
    FastAPI dependency that yields a SQLAlchemy database session per request
    and guarantees the session is closed when the request finishes.
    """
    if SessionLocal is None:
        raise RuntimeError(
            "DATABASE_URL is not set in .env. "
            "Please configure your Supabase PostgreSQL connection string in the .env file."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
