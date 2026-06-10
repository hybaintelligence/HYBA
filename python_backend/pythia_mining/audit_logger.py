"""
Comprehensive audit logging for HYBA mining operations.

This module provides structured, production-grade audit logging for all critical
mining operations including connections, handshakes, job receptions, share submissions,
and security events. Logs are written to both file and console with appropriate severity levels.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class AuditEventType(Enum):
    """Types of audit events for categorization."""
    CONNECTION_ATTEMPT = "connection_attempt"
    CONNECTION_SUCCESS = "connection_success"
    CONNECTION_FAILURE = "connection_failure"
    DISCONNECTION = "disconnection"
    HANDSHAKE_START = "handshake_start"
    HANDSHAKE_SUCCESS = "handshake_success"
    HANDSHAKE_FAILURE = "handshake_failure"
    JOB_RECEIVED = "job_received"
    JOB_STALE = "job_stale"
    SHARE_SUBMISSION = "share_submission"
    SHARE_ACCEPTED = "share_accepted"
    SHARE_REJECTED = "share_rejected"
    SHARE_VALIDATION_ERROR = "share_validation_error"
    DIFFICULTY_CHANGE = "difficulty_change"
    EXTRANONCE_CHANGE = "extranonce_change"
    VERSION_MASK_CHANGE = "version_mask_change"
    RECONNECTION_ATTEMPT = "reconnection_attempt"
    HEARTBEAT_FAILURE = "heartbeat_failure"
    TLS_VERIFICATION_FAILURE = "tls_verification_failure"
    SECURITY_EVENT = "security_event"


@dataclass
class AuditEvent:
    """Structured audit event record."""
    event_type: AuditEventType
    pool_name: str
    pool_url: str
    timestamp: float
    event_data: Dict[str, Any]
    severity: str = "INFO"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for serialization."""
        return {
            "event_type": self.event_type.value,
            "pool_name": self.pool_name,
            "pool_url": self.pool_url,
            "timestamp": self.timestamp,
            "iso_timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "severity": self.severity,
            "event_data": self.event_data,
        }
    
    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict(), separators=(",", ":"))


class AuditLogger:
    """
    Production-grade audit logger for mining operations.
    
    Provides structured logging to both file and console with proper rotation
    and severity levels. All critical operations are logged for forensic analysis.
    """
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        log_level: str = "INFO",
        enable_console: bool = True,
    ):
        self.log_dir = Path(log_dir or os.getenv("HYBA_AUDIT_LOG_DIR", "logs/audit"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main audit logger
        self.logger = logging.getLogger("hyba.audit")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()
        
        # File handler with JSON formatting
        log_file = self.log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler if enabled
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def log_event(self, event: AuditEvent) -> None:
        """Log an audit event with appropriate severity."""
        log_level = getattr(logging, event.severity.upper(), logging.INFO)
        self.logger.log(log_level, event.to_json())
    
    def log_connection_attempt(
        self,
        pool_name: str,
        pool_url: str,
        stratum_version: int,
        attempt_number: int = 1,
    ) -> None:
        """Log a connection attempt."""
        event = AuditEvent(
            event_type=AuditEventType.CONNECTION_ATTEMPT,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "stratum_version": stratum_version,
                "attempt_number": attempt_number,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_connection_success(
        self,
        pool_name: str,
        pool_url: str,
        latency_ms: float,
        stratum_version: int,
    ) -> None:
        """Log a successful connection."""
        event = AuditEvent(
            event_type=AuditEventType.CONNECTION_SUCCESS,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "latency_ms": latency_ms,
                "stratum_version": stratum_version,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_connection_failure(
        self,
        pool_name: str,
        pool_url: str,
        error: str,
        attempt_number: int = 1,
    ) -> None:
        """Log a connection failure."""
        event = AuditEvent(
            event_type=AuditEventType.CONNECTION_FAILURE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "error": error,
                "attempt_number": attempt_number,
            },
            severity="ERROR",
        )
        self.log_event(event)
    
    def log_handshake_start(
        self,
        pool_name: str,
        pool_url: str,
        username: str,
    ) -> None:
        """Log handshake initiation."""
        event = AuditEvent(
            event_type=AuditEventType.HANDSHAKE_START,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "username": username,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_handshake_success(
        self,
        pool_name: str,
        pool_url: str,
        extranonce1: str,
        extranonce2_size: int,
    ) -> None:
        """Log successful handshake."""
        event = AuditEvent(
            event_type=AuditEventType.HANDSHAKE_SUCCESS,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "extranonce1": extranonce1,
                "extranonce2_size": extranonce2_size,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_handshake_failure(
        self,
        pool_name: str,
        pool_url: str,
        error: str,
    ) -> None:
        """Log handshake failure."""
        event = AuditEvent(
            event_type=AuditEventType.HANDSHAKE_FAILURE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "error": error,
            },
            severity="ERROR",
        )
        self.log_event(event)
    
    def log_job_received(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
        clean_jobs: bool,
        difficulty: float,
    ) -> None:
        """Log job reception."""
        event = AuditEvent(
            event_type=AuditEventType.JOB_RECEIVED,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "job_id": job_id,
                "clean_jobs": clean_jobs,
                "difficulty": difficulty,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_job_stale(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
    ) -> None:
        """Log job marked as stale."""
        event = AuditEvent(
            event_type=AuditEventType.JOB_STALE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "job_id": job_id,
            },
            severity="WARNING",
        )
        self.log_event(event)
    
    def log_share_submission(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
        nonce: int,
        extranonce2: str,
    ) -> None:
        """Log share submission attempt."""
        event = AuditEvent(
            event_type=AuditEventType.SHARE_SUBMISSION,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "job_id": job_id,
                "nonce": nonce,
                "extranonce2": extranonce2,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_share_accepted(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
        nonce: int,
        block_hash: Optional[str] = None,
    ) -> None:
        """Log share acceptance."""
        event = AuditEvent(
            event_type=AuditEventType.SHARE_ACCEPTED,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "job_id": job_id,
                "nonce": nonce,
                "block_hash": block_hash,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_share_rejected(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
        nonce: int,
        reason: str,
        error_code: Optional[int] = None,
    ) -> None:
        """Log share rejection."""
        event = AuditEvent(
            event_type=AuditEventType.SHARE_REJECTED,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "job_id": job_id,
                "nonce": nonce,
                "reason": reason,
                "error_code": error_code,
            },
            severity="WARNING",
        )
        self.log_event(event)
    
    def log_share_validation_error(
        self,
        pool_name: str,
        pool_url: str,
        job_id: str,
        nonce: int,
        error: str,
    ) -> None:
        """Log share validation error."""
        event = AuditEvent(
            event_type=AuditEventType.SHARE_VALIDATION_ERROR,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "job_id": job_id,
                "nonce": nonce,
                "error": error,
            },
            severity="ERROR",
        )
        self.log_event(event)
    
    def log_difficulty_change(
        self,
        pool_name: str,
        pool_url: str,
        old_difficulty: float,
        new_difficulty: float,
    ) -> None:
        """Log difficulty change."""
        event = AuditEvent(
            event_type=AuditEventType.DIFFICULTY_CHANGE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "old_difficulty": old_difficulty,
                "new_difficulty": new_difficulty,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_extranonce_change(
        self,
        pool_name: str,
        pool_url: str,
        old_extranonce1: str,
        new_extranonce1: str,
        old_extranonce2_size: int,
        new_extranonce2_size: int,
    ) -> None:
        """Log extranonce change."""
        event = AuditEvent(
            event_type=AuditEventType.EXTRANONCE_CHANGE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "old_extranonce1": old_extranonce1,
                "new_extranonce1": new_extranonce1,
                "old_extranonce2_size": old_extranonce2_size,
                "new_extranonce2_size": new_extranonce2_size,
            },
            severity="INFO",
        )
        self.log_event(event)
    
    def log_reconnection_attempt(
        self,
        pool_name: str,
        pool_url: str,
        attempt_number: int,
        delay_seconds: float,
    ) -> None:
        """Log reconnection attempt."""
        event = AuditEvent(
            event_type=AuditEventType.RECONNECTION_ATTEMPT,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "attempt_number": attempt_number,
                "delay_seconds": delay_seconds,
            },
            severity="WARNING",
        )
        self.log_event(event)
    
    def log_heartbeat_failure(
        self,
        pool_name: str,
        pool_url: str,
        idle_time_seconds: float,
    ) -> None:
        """Log heartbeat failure."""
        event = AuditEvent(
            event_type=AuditEventType.HEARTBEAT_FAILURE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "idle_time_seconds": idle_time_seconds,
            },
            severity="WARNING",
        )
        self.log_event(event)
    
    def log_tls_verification_failure(
        self,
        pool_name: str,
        pool_url: str,
        error: str,
    ) -> None:
        """Log TLS certificate verification failure."""
        event = AuditEvent(
            event_type=AuditEventType.TLS_VERIFICATION_FAILURE,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "error": error,
            },
            severity="CRITICAL",
        )
        self.log_event(event)
    
    def log_security_event(
        self,
        pool_name: str,
        pool_url: str,
        event_description: str,
        severity: str = "WARNING",
    ) -> None:
        """Log a general security event."""
        event = AuditEvent(
            event_type=AuditEventType.SECURITY_EVENT,
            pool_name=pool_name,
            pool_url=pool_url,
            timestamp=time.time(),
            event_data={
                "description": event_description,
            },
            severity=severity,
        )
        self.log_event(event)


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set the global audit logger instance."""
    global _audit_logger
    _audit_logger = logger


__all__ = [
    "AuditEventType",
    "AuditEvent",
    "AuditLogger",
    "get_audit_logger",
    "set_audit_logger",
]
