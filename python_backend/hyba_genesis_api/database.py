"""Database connection management.

This module centralizes database configuration for HYBA Genesis.  By using SQLAlchemy's engine and session, the application can support multiple backends (SQLite or PostgreSQL) and perform migrations more easily.

The database URL is read from the `DATABASE_URL` environment variable.  If it is not set, the code defaults to a local SQLite database at `data/metrics.db`.  For SQLite, `check_same_thread` is disabled to allow multi-threaded access via SQLAlchemy.

Example usage:

    from .database import SessionLocal

    def get_user(id: int):
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == id).first()
        finally:
            db.close()
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Determine the database URL from environment or fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/metrics.db")

# Provide special arguments for SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # handle sqlite-specific flags
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize the database by creating any missing tables.

    On startup the API will call this function to ensure that the
    SQLAlchemy models have corresponding tables in the configured
    database.  When using SQLite this will create the necessary tables
    on disk.  When using PostgreSQL this will attempt to create tables
    if they do not already exist.  For production deployments we
    recommend running Alembic migrations instead of relying on
    `create_all`, but this fallback ensures that development
    environments work out of the box.
    """
    try:
        # Import ORM models only when initialising; this avoids
        # unnecessary dependencies for callers that only use SessionLocal.
        from consciousness_db.models import Base  # type: ignore
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        # Log the exception but allow the application to start; database
        # initialisation failures will surface through runtime errors.
        import logging
        logging.error("Database initialization failed", exc_info=exc)
