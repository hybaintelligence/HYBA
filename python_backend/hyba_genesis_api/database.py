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
if DATABASE_URL.startswith("sqlite"):  # handle sqlite-specific flags
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Optional: function to initialize DB models (no-op here)
def init_db() -> None:
    """Placeholder for initializing database models.

    This function can be expanded to import models and create tables.
    For example:

        from . import models
        models.Base.metadata.create_all(bind=engine)

    """
    pass
