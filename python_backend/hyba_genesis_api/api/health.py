"""
Health & Status APIs
HYBA Genesis Platform Monitoring
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from hyba_genesis_api.core.substrate import get_substrate_state, is_ready
from hyba_genesis_api.core.telemetry import get_metrics

router = APIRouter(prefix="/api/health", tags=["health"])


def get_pythia_state() -> Optional[Dict[str, Any]]:
    state_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "pythia_state.json",
    )
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _calculate_structural_coupling_index(substrate_state: Dict[str, Any], pythia_state: Optional[Dict[str, Any]]) -> float:
    """Calculate the Structural Coupling Index for biological health monitoring.
    
    The Structural Coupling Index measures how well the system components are integrated
    and coupled together, inspired by biological systems where structural coupling indicates
    the health of the nervous system and its ability to coordinate responses.
    
    Args:
        substrate_state: Current substrate state from get_substrate_state()
        pythia_state: Current pythia mining state (optional)
    
    Returns:
        Structural Coupling Index (0.0 = severed nerves, 1.0 = fully coupled)
    """
    coupling_factors = []
    
    # Factor 1: Substrate readiness (0.0 to 1.0)
    if substrate_state.get("status") == "ready":
        coupling_factors.append(1.0)
    else:
        coupling_factors.append(0.3)
    
    # Factor 2: Component initialization count
    initialized_components = substrate_state.get("initialized_components", 0)
    total_components = substrate_state.get("total_components", 1)
    if total_components > 0:
        coupling_factors.append(initialized_components / total_components)
    
    # Factor 3: Pythia system health if available
    if pythia_state:
        system_health = pythia_state.get("system_health", "unknown")
        if system_health == "healthy":
            coupling_factors.append(1.0)
        elif system_health == "degraded":
            coupling_factors.append(0.5)
        else:
            coupling_factors.append(0.3)
    
    # Factor 4: Phi-resonance if available
    if pythia_state:
        quantum = pythia_state.get("quantum", {})
        phi_resonance = quantum.get("phi_phase_alignment", 0.0)
        if phi_resonance > 0.5:
            coupling_factors.append(1.0)
        elif phi_resonance > 0.2:
            coupling_factors.append(0.7)
        else:
            coupling_factors.append(0.3)
    
    # Calculate weighted average
    if coupling_factors:
        return sum(coupling_factors) / len(coupling_factors)
    return 0.5  # Default middle value if no factors available


@router.get("/live", response_model=Dict[str, Any])
async def liveness_probe():
    """Liveness probe: returns 200 if process is alive."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_probe():
    """Readiness probe: returns 200 if substrate is fully initialized, else 503."""
    substrate_state = get_substrate_state()
    if not is_ready():
        return JSONResponse(
            status_code=503,
            content={
                "status": "initializing",
                "message": "Substrate initialization is incomplete.",
                "substrate": substrate_state,
            },
        )
    return {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "substrate": substrate_state,
    }


@router.get("", response_model=Dict[str, Any])
async def get_health_status():
    state = get_pythia_state()
    quantum = state.get("quantum", {}) if state else {}
    substrate_state = get_substrate_state()
    
    # Calculate Structural Coupling Index and Φ-Floor
    # Structural Coupling Index: measures how well the system components are integrated
    # Φ-Floor: minimum acceptable φ-resonance threshold for healthy operation
    structural_coupling_index = _calculate_structural_coupling_index(substrate_state, state)
    phi_floor = 0.2  # Minimum φ-resonance threshold for healthy operation
    innervation_status = "healthy" if structural_coupling_index > phi_floor else "degraded"
    
    return {
        "status": "healthy" if is_ready() else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.1",
        "telemetry_source": state.get("telemetry_source") if state else "unavailable",
        "quantumCoherence": quantum.get("basis_coherence"),
        "decoherenceTimeMs": None,
        "quantumSpeedupFactor": None,
        "actualSpeedupFactor": None,
        "phiResonance": quantum.get("phi_phase_alignment"),
        "telemetry": get_metrics(),
        "substrate": substrate_state,
        # Biological Health Check Metrics
        "structural_coupling_index": structural_coupling_index,
        "phi_floor": phi_floor,
        "innervation_status": innervation_status,
        "systemMetrics": {
            "blockHeight": state.get("block_height") if state else None,
            "currentHashrate": state.get("hashrate_ehs") if state else None,
            "powerConsumption": state.get("power_consumption") if state else None,
            "activePool": state.get("active_pool") if state else None,
            "difficultyTarget": state.get("difficulty_target") if state else None,
            "networkDifficulty": state.get("network_difficulty") if state else None,
            "power_scale": state.get("power_scale") if state else None,
            "phi_tier": state.get("phi_tier") if state else None,
            "phi_tier_composition": (state.get("phi_tier_composition") if state else None),
            "memory_compression_contract": (
                state.get("memory_compression_contract") if state else None
            ),
            "system_health": state.get("system_health") if state else "unavailable",
        },
    }


@router.get("/readiness", response_model=Dict[str, Any])
async def get_substrate_readiness():
    """Detailed readiness check without fabricated governance thresholds."""
    state = get_pythia_state()
    return {
        "status": "ready" if is_ready() else "initializing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "substrate": get_substrate_state(),
        "pythia": {
            "available": state is not None,
            "system_health": state.get("system_health") if state else "unavailable",
            "telemetry_source": (state.get("telemetry_source") if state else "unavailable"),
        },
    }
