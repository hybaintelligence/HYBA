"""Schemas for the organism regeneration API surface."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BlastemaState(BaseModel):
    """Operator-visible state for a lane progenitor template."""

    lane_id: int = Field(ge=0, le=31)
    progenitor_id: str
    module_id: str
    role_probabilities: Dict[str, float]
    blastema_entropy: float = Field(ge=0.0)
    l3_residency_time_ms: Optional[float] = None
    is_primed: bool = True
    evidence_source: str


class FidelityEvent(BaseModel):
    """Audit event emitted after a lane regeneration attempt."""

    timestamp: datetime
    lane_id: int = Field(ge=0, le=31)
    module_id: str
    pre_injury_phi: float = Field(ge=0.0)
    post_recovery_fidelity: float = Field(ge=0.0, le=1.0)
    scarring_detected: bool
    recovery_duration_ms: float = Field(ge=0.0)
    status: str
    collapsed_role: Optional[str] = None
    trace: Dict[str, object] = Field(default_factory=dict)


class RegenerativeStatus(BaseModel):
    """Aggregate regeneration health for the 32-lane manifold."""

    system_phi: float = Field(ge=0.0)
    innervation_stable: bool
    active_blastemas: int = Field(ge=0)
    global_fidelity_mean: float = Field(ge=0.0, le=1.0)
    regeneration_potential: str
    fidelity_events: int = Field(ge=0)
    lanes: List[BlastemaState]
