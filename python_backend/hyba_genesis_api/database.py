"""
Database connection and schema initialization.
Uses SQLite for development, can be swapped for PostgreSQL in production.
"""

import sqlite3
import os
from typing import Optional

DB_PATH = os.getenv("HYBA_DB_PATH", "hyba_customer_portal.db")


def get_db_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """
    Initialize database schema for customer portal.
    Run this on first startup.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # API Keys table
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
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (customer_id) REFERENCES users(id)
        )
    """
    )

    # Usage tracking table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usage_logs (
            log_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            service_type TEXT NOT NULL,
            compute_units INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            api_key_id TEXT,
            execution_id TEXT,
            evidence_seal TEXT,
            FOREIGN KEY (customer_id) REFERENCES users(id),
            FOREIGN KEY (api_key_id) REFERENCES api_keys(api_key_id)
        )
    """
    )

    # Create index on timestamp for efficient queries
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_usage_timestamp 
        ON usage_logs(customer_id, timestamp)
    """
    )

    # Quota alerts configuration
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS quota_alerts (
            customer_id TEXT PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 1,
            threshold_percent INTEGER NOT NULL DEFAULT 90,
            notification_email TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES users(id)
        )
    """
    )

    # Customer subscriptions/tiers
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
            status TEXT NOT NULL DEFAULT 'active',
            FOREIGN KEY (customer_id) REFERENCES users(id)
        )
    """
    )

    conn.commit()
    conn.close()
    print(f"✅ Database initialized at {DB_PATH}")


if __name__ == "__main__":
    initialize_database()
