"""Database connection and schema initialization for customer self-service."""

from __future__ import annotations

import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_PATH = os.getenv("HYBA_DB_PATH", "hyba_customer_portal.db")

# SQLAlchemy setup for enterprise-grade ORM support
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"sqlite:///{DB_PATH}"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create SessionLocal for dependency injection
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row access enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Initialize customer portal tables idempotently."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            api_key_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            hashed_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            last_used_at TEXT,
            deleted_at TEXT,
            status TEXT NOT NULL DEFAULT 'active'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_logs (
            log_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            service_type TEXT NOT NULL,
            compute_units INTEGER NOT NULL CHECK (compute_units >= 0),
            timestamp TEXT NOT NULL,
            api_key_id TEXT,
            execution_id TEXT,
            evidence_seal TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_usage_customer_timestamp
        ON usage_logs(customer_id, timestamp)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_usage_customer_execution
        ON usage_logs(customer_id, execution_id)
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quota_alerts (
            customer_id TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1,
            threshold_percent INTEGER NOT NULL DEFAULT 90,
            notification_email TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_subscriptions (
            customer_id TEXT PRIMARY KEY,
            tier TEXT NOT NULL DEFAULT 'developer',
            compute_units_quota INTEGER NOT NULL DEFAULT 1000,
            cost_per_unit REAL NOT NULL DEFAULT 0.01,
            currency TEXT NOT NULL DEFAULT 'USD',
            billing_cycle TEXT NOT NULL DEFAULT 'monthly',
            subscription_start TEXT NOT NULL,
            subscription_end TEXT,
            status TEXT NOT NULL DEFAULT 'active'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            period TEXT NOT NULL,
            amount REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD',
            status TEXT NOT NULL DEFAULT 'pending',
            issued_at TEXT NOT NULL,
            paid_at TEXT,
            UNIQUE(customer_id, period)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_methods (
            payment_method_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            last4 TEXT NOT NULL,
            card_type TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active'
        )
        """
    )

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")


def init_db() -> None:
    """Backwards-compatible alias used by older backend startup code.
    
    Initializes both SQLite customer portal tables and SQLAlchemy enterprise models.
    """
    # Initialize SQLite customer portal tables
    initialize_database()
    
    # Initialize SQLAlchemy enterprise models
    try:
        from consciousness_db.models import create_all_tables
        create_all_tables(engine)
        print("✅ SQLAlchemy enterprise models initialized")
    except Exception as e:
        print(f"⚠️  SQLAlchemy model initialization failed: {e}")
        # Non-fatal - continue with SQLite tables


def get_db_session():
    """Get a SQLAlchemy database session with proper cleanup.
    
    Use this in dependency injection:
        db: Session = Depends(get_db_session)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    initialize_database()
