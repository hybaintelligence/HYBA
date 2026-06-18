"""Immune and Sensory schema models for the Organism CNS."""

from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime


class RealityAnchorReport(BaseModel):
    """Report on reality verification via Mass-Gap jitter analysis."""
    
    jitter_coherence: float  # Analysis of network latency vs (3 - phi)
    is_simulated: bool
    entropy_drift: float
    anchor_verified_at: datetime


class ImmuneStatus(BaseModel):
    """Status of the immune system and phi-floor enforcement."""
    
    phi_floor: float
    is_in_lockdown: bool
    quarantined_lanes: List[int]
    inseparability_index: float  # Entropy between Mining and Intelligence
