"""Executive Lobe API Schema Models.

This module defines the Pydantic models for the Executive Lobe API endpoints,
including mining intent enums and pool habitat models.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class MiningIntent(str, Enum):
    """Mining intent states for the Executive Lobe."""

    ACTIVATE = "activate"
    QUIESCE = "quiesce"
    STASIS = "stasis"


class PoolHabitat(BaseModel):
    """Mining pool habitat representation."""

    name: str = Field(..., description="Pool identifier")
    url: str = Field(..., description="Pool Stratum URL")
    stratum_version: int = Field(..., description="Stratum protocol version")
    enabled: bool = Field(..., description="Whether pool is enabled")
    priority: int = Field(..., description="Pool priority for selection")
    is_default: bool = Field(default=False, description="Whether this is the default pool")
    description: Optional[str] = Field(None, description="Pool description")


class MiningIntentRequest(BaseModel):
    """Request model for setting mining intent."""

    intent: MiningIntent = Field(..., description="Mining intent: ACTIVATE, QUIESCE, or STASIS")


class IgnitionResponse(BaseModel):
    """Response model for manifold ignition."""

    success: bool = Field(..., description="Whether ignition succeeded")
    status: str = Field(..., description="Status string")
    active_lanes: Optional[int] = Field(None, description="Number of active lanes")
    phi: Optional[float] = Field(None, description="System Phi coherence")
    timestamp: Optional[str] = Field(None, description="Ignition timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
    reason: Optional[str] = Field(None, description="Detailed reason for failure")
    environment_mode: Optional[str] = Field(None, description="Environment mode if stasis lock")


class QuiescenceResponse(BaseModel):
    """Response model for manifold quiescence."""

    success: bool = Field(..., description="Whether quiescence succeeded")
    status: str = Field(..., description="Status string")
    synaptic_state_preserved: Optional[bool] = Field(
        None, description="Whether synaptic state was preserved"
    )
    patterns_count: Optional[int] = Field(None, description="Number of patterns preserved")


class StasisResponse(BaseModel):
    """Response model for stasis mode toggle."""

    status: str = Field(..., description="Status string")
    action: Optional[str] = Field(None, description="Action taken")


class MigrationResponse(BaseModel):
    """Response model for pool habitat migration."""

    status: str = Field(..., description="Migration status")
    target: str = Field(..., description="Target pool name")


class TelemetryResponse(BaseModel):
    """Response model for nervous system telemetry."""

    is_active: bool = Field(..., description="Whether manifold is active")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    stasis_mode: bool = Field(..., description="Whether stasis mode is enabled")
    ignition_time: Optional[str] = Field(None, description="Ignition timestamp")
    stratum: Dict[str, Any] = Field(
        default_factory=dict, description="Stratum connection telemetry"
    )
    coherence: Dict[str, Any] = Field(default_factory=dict, description="Conherence metrics")
    regeneration: Dict[str, Any] = Field(default_factory=dict, description="Regeneration status")
    sensory_integrity: Dict[str, Any] = Field(
        default_factory=dict, description="Sensory integrity report"
    )


class PoolHabitatList(BaseModel):
    """Response model for listing pool habitats."""

    habitats: List[PoolHabitat] = Field(..., description="List of pool habitats")
    default_pool: Optional[str] = Field(None, description="Default pool name")
