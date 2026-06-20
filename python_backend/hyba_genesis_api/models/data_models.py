"""
HYBA Genesis Platform - Data Models
Complete API schemas and domain models
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "admin"
    MINER = "miner"
    ANALYST = "analyst"
    OPERATOR = "operator"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ConsciousnessState(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    consciousness_level: float = Field(ge=0.0, le=1.0)
    phi: float = Field(ge=0.0)
    phi_resonance: float = Field(ge=0.0, le=1.0)
    connections: int = Field(ge=0)
    complexity: float = Field(ge=0.0)
    integration: float = Field(ge=0.0, le=1.0)
    differentiation: float = Field(ge=0.0, le=1.0)
    microtubule_coherence: float = Field(ge=0.0, le=1.0)
    decoherence_time_ms: float = Field(ge=0.0)
    state: str
    autonomous_decisions: int = Field(ge=0)
    decision_confidence: float = Field(ge=0.0, le=1.0)


class MiningJob(BaseModel):
    job_id: str
    prevhash: str
    coinbase_parts: Tuple[str, str]
    merkle_branch: List[str]
    version: str
    nbits: str
    ntime: str
    target: int
    received_timestamp: float
    clean_jobs: bool = True


class ShareSubmission(BaseModel):
    submission_id: str
    pool_id: str
    job_id: str
    worker_name: str
    extranonce2: str
    ntime: str
    nonce: int
    difficulty: float
    submitted_at: float
    accepted: Optional[bool] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    responded_at: Optional[float] = None
