"""
Metrics persistence for HYBA mining operations.

This module provides durable storage for mining metrics including share counters,
latency statistics, and connection metrics using SQLite for production-grade persistence.
"""

from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading


@dataclass
class PoolMetrics:
    """Metrics snapshot for a mining pool."""
    pool_name: str
    pool_url: str
    shares_submitted: int
    shares_accepted: int
    shares_rejected: int
    connection_failures: int
    avg_latency_ms: Optional[float]
    last_activity_timestamp: float
    last_pool_event_timestamp: Optional[float]
    last_share_submit_timestamp: Optional[float]
    current_difficulty: float
    current_jobs_count: int
    acceptance_rate: float


class MetricsStore:
    """
    Production-grade metrics persistence using SQLite.
    
    Provides thread-safe storage and retrieval of mining metrics with automatic
    schema initialization and periodic cleanup of old records.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the metrics store.
        
        Args:
            db_path: Path to SQLite database file. Defaults to data/metrics.db
        """
        if db_path is None:
            db_path = os.getenv("HYBA_METRICS_DB_PATH", "data/metrics.db")
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Initialize database schema
        self._initialize_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn
    
    def _initialize_schema(self) -> None:
        """Initialize database schema with required tables."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Pool metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pool_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_name TEXT NOT NULL,
                pool_url TEXT NOT NULL,
                shares_submitted INTEGER DEFAULT 0,
                shares_accepted INTEGER DEFAULT 0,
                shares_rejected INTEGER DEFAULT 0,
                connection_failures INTEGER DEFAULT 0,
                avg_latency_ms REAL,
                last_activity_timestamp REAL,
                last_pool_event_timestamp REAL,
                last_share_submit_timestamp REAL,
                current_difficulty REAL DEFAULT 1.0,
                current_jobs_count INTEGER DEFAULT 0,
                acceptance_rate REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pool_name, pool_url)
            )
        """)
        
        # Share submission history table for detailed analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS share_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_name TEXT NOT NULL,
                pool_url TEXT NOT NULL,
                job_id TEXT NOT NULL,
                nonce INTEGER NOT NULL,
                accepted BOOLEAN NOT NULL,
                error_code INTEGER,
                error_message TEXT,
                block_hash TEXT,
                target TEXT,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Connection history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pool_name TEXT NOT NULL,
                pool_url TEXT NOT NULL,
                event_type TEXT NOT NULL,
                latency_ms REAL,
                error_message TEXT,
                attempt_number INTEGER,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_share_history_pool 
            ON share_history(pool_name, pool_url, submitted_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_connection_history_pool 
            ON connection_history(pool_name, pool_url, occurred_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_share_history_submitted_at 
            ON share_history(submitted_at)
        """)
        
        conn.commit()
    
    def update_pool_metrics(self, metrics: PoolMetrics) -> None:
        """
        Update or insert pool metrics.
        
        Args:
            metrics: PoolMetrics object with current metrics
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO pool_metrics (
                    pool_name, pool_url, shares_submitted, shares_accepted, shares_rejected,
                    connection_failures, avg_latency_ms, last_activity_timestamp,
                    last_pool_event_timestamp, last_share_submit_timestamp,
                    current_difficulty, current_jobs_count, acceptance_rate, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                metrics.pool_name,
                metrics.pool_url,
                metrics.shares_submitted,
                metrics.shares_accepted,
                metrics.shares_rejected,
                metrics.connection_failures,
                metrics.avg_latency_ms,
                metrics.last_activity_timestamp,
                metrics.last_pool_event_timestamp,
                metrics.last_share_submit_timestamp,
                metrics.current_difficulty,
                metrics.current_jobs_count,
                metrics.acceptance_rate,
            ))
            
            conn.commit()
    
    def get_pool_metrics(self, pool_name: str, pool_url: str) -> Optional[PoolMetrics]:
        """
        Retrieve current metrics for a specific pool.
        
        Args:
            pool_name: Name of the pool
            pool_url: URL of the pool
            
        Returns:
            PoolMetrics object if found, None otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pool_name, pool_url, shares_submitted, shares_accepted, shares_rejected,
                   connection_failures, avg_latency_ms, last_activity_timestamp,
                   last_pool_event_timestamp, last_share_submit_timestamp,
                   current_difficulty, current_jobs_count, acceptance_rate
            FROM pool_metrics
            WHERE pool_name = ? AND pool_url = ?
        """, (pool_name, pool_url))
        
        row = cursor.fetchone()
        if row:
            return PoolMetrics(
                pool_name=row[0],
                pool_url=row[1],
                shares_submitted=row[2],
                shares_accepted=row[3],
                shares_rejected=row[4],
                connection_failures=row[5],
                avg_latency_ms=row[6],
                last_activity_timestamp=row[7],
                last_pool_event_timestamp=row[8],
                last_share_submit_timestamp=row[9],
                current_difficulty=row[10],
                current_jobs_count=row[11],
                acceptance_rate=row[12],
            )
        return None
    
    def record_share_submission(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
        nonce: int,
        accepted: bool,
        error_code: Optional[int] = None,
        error_message: Optional[str] = None,
        block_hash: Optional[str] = None,
        target: Optional[int] = None,
    ) -> None:
        """
        Record a share submission in the history table.
        
        Args:
            pool_name: Name of the pool
            pool_url: URL of the pool
            job_id: Job identifier
            nonce: Nonce value
            accepted: Whether the share was accepted
            error_code: Error code if rejected
            error_message: Error message if rejected
            block_hash: Block hash if available
            target: Target value if available
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO share_history (
                    pool_name, pool_url, job_id, nonce, accepted, error_code,
                    error_message, block_hash, target, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                pool_name,
                pool_url,
                job_id,
                nonce,
                accepted,
                error_code,
                error_message,
                block_hash,
                str(target) if target is not None else None,
            ))
            
            conn.commit()
    
    def record_connection_event(
        self,
        pool_name: str,
        pool_url: str,
        event_type: str,
        latency_ms: Optional[float] = None,
        error_message: Optional[str] = None,
        attempt_number: Optional[int] = None,
    ) -> None:
        """
        Record a connection event in the history table.
        
        Args:
            pool_name: Name of the pool
            pool_url: URL of the pool
            event_type: Type of event (connection_attempt, connection_success, etc.)
            latency_ms: Connection latency if successful
            error_message: Error message if failed
            attempt_number: Attempt number for reconnection attempts
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO connection_history (
                    pool_name, pool_url, event_type, latency_ms, error_message,
                    attempt_number, occurred_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                pool_name,
                pool_url,
                event_type,
                latency_ms,
                error_message,
                attempt_number,
            ))
            
            conn.commit()
    
    def get_all_pool_metrics(self) -> List[PoolMetrics]:
        """
        Retrieve metrics for all pools.
        
        Returns:
            List of PoolMetrics objects
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pool_name, pool_url, shares_submitted, shares_accepted, shares_rejected,
                   connection_failures, avg_latency_ms, last_activity_timestamp,
                   last_pool_event_timestamp, last_share_submit_timestamp,
                   current_difficulty, current_jobs_count, acceptance_rate
            FROM pool_metrics
            ORDER BY updated_at DESC
        """)
        
        metrics = []
        for row in cursor.fetchall():
            metrics.append(PoolMetrics(
                pool_name=row[0],
                pool_url=row[1],
                shares_submitted=row[2],
                shares_accepted=row[3],
                shares_rejected=row[4],
                connection_failures=row[5],
                avg_latency_ms=row[6],
                last_activity_timestamp=row[7],
                last_pool_event_timestamp=row[8],
                last_share_submit_timestamp=row[9],
                current_difficulty=row[10],
                current_jobs_count=row[11],
                acceptance_rate=row[12],
            ))
        
        return metrics
    
    def get_share_history(
        self,
        pool_name: Optional[str] = None,
        pool_url: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve share submission history.
        
        Args:
            pool_name: Filter by pool name (optional)
            pool_url: Filter by pool URL (optional)
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of share history records as dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT pool_name, pool_url, job_id, nonce, accepted, error_code,
                   error_message, block_hash, target, submitted_at
            FROM share_history
        """
        params = []
        
        if pool_name and pool_url:
            query += " WHERE pool_name = ? AND pool_url = ?"
            params.extend([pool_name, pool_url])
        
        query += " ORDER BY submitted_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "pool_name": row[0],
                "pool_url": row[1],
                "job_id": row[2],
                "nonce": row[3],
                "accepted": bool(row[4]),
                "error_code": row[5],
                "error_message": row[6],
                "block_hash": row[7],
                "target": row[8],
                "submitted_at": row[9],
            })
        
        return history
    
    def get_connection_history(
        self,
        pool_name: Optional[str] = None,
        pool_url: Optional[str] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve connection event history.
        
        Args:
            pool_name: Filter by pool name (optional)
            pool_url: Filter by pool URL (optional)
            limit: Maximum number of records to return
            offset: Offset for pagination
            
        Returns:
            List of connection history records as dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT pool_name, pool_url, event_type, latency_ms, error_message,
                   attempt_number, occurred_at
            FROM connection_history
        """
        params = []
        
        if pool_name and pool_url:
            query += " WHERE pool_name = ? AND pool_url = ?"
            params.extend([pool_name, pool_url])
        
        query += " ORDER BY occurred_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "pool_name": row[0],
                "pool_url": row[1],
                "event_type": row[2],
                "latency_ms": row[3],
                "error_message": row[4],
                "attempt_number": row[5],
                "occurred_at": row[6],
            })
        
        return history
    
    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Clean up old records from history tables.
        
        Args:
            days_to_keep: Number of days of history to retain
            
        Returns:
            Total number of records deleted
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 86400)
            
            # Clean up share history
            cursor.execute("""
                DELETE FROM share_history WHERE submitted_at < ?
            """, (cutoff_date,))
            share_deleted = cursor.rowcount
            
            # Clean up connection history
            cursor.execute("""
                DELETE FROM connection_history WHERE occurred_at < ?
            """, (cutoff_date,))
            conn_deleted = cursor.rowcount
            
            conn.commit()
            
            return share_deleted + conn_deleted
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, 'conn') and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None


# Global metrics store instance
_metrics_store: Optional[MetricsStore] = None


def get_metrics_store() -> MetricsStore:
    """Get or create the global metrics store instance for the active DB path."""
    global _metrics_store
    configured_path = Path(os.getenv("HYBA_METRICS_DB_PATH", "data/metrics.db"))
    if _metrics_store is not None and _metrics_store.db_path != configured_path:
        _metrics_store.close()
        _metrics_store = None
    if _metrics_store is None:
        _metrics_store = MetricsStore(str(configured_path))
    return _metrics_store


def set_metrics_store(store: MetricsStore) -> None:
    """Set the global metrics store instance."""
    global _metrics_store
    if _metrics_store is not None and _metrics_store is not store:
        _metrics_store.close()
    _metrics_store = store


def reset_metrics_store() -> None:
    """Close and clear the global metrics store so env-scoped tests cannot leak state."""
    global _metrics_store
    if _metrics_store is not None:
        _metrics_store.close()
    _metrics_store = None


__all__ = [
    "PoolMetrics",
    "MetricsStore",
    "get_metrics_store",
    "set_metrics_store",
    "reset_metrics_store",
]
