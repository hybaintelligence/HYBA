"""
Health & Status APIs
HYBA Genesis Platform Monitoring
"""

from __future__ import annotations

import json
import os
from datetime import datetime
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


@router.get("/live", response_model=Dict[str, Any])
async def liveness_probe():
    """Liveness probe: returns 200 if process is alive."""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


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
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat(), "substrate": substrate_state}


@router.get("", response_model=Dict[str, Any])
async def get_health_status():
    state = get_pythia_state()
    quantum = state.get("quantum", {}) if state else {}
    return {
        "status": "healthy" if is_ready() else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.1",
        "telemetry_source": state.get("telemetry_source") if state else "unavailable",
        "quantumCoherence": quantum.get("basis_coherence"),
        "decoherenceTimeMs": None,
        "quantumSpeedupFactor": None,
        "actualSpeedupFactor": None,
        "phiResonance": quantum.get("phi_phase_alignment"),
        "telemetry": get_metrics(),
        "substrate": get_substrate_state(),
        "systemMetrics": {
            "blockHeight": state.get("block_height") if state else None,
            "currentHashrate": state.get("hashrate_ehs") if state else None,
            "powerConsumption": state.get("power_consumption") if state else None,
            "activePool": state.get("active_pool") if state else None,
            "difficultyTarget": state.get("difficulty_target") if state else None,
            "networkDifficulty": state.get("network_difficulty") if state else None,
            "power_scale": state.get("power_scale") if state else None,
            "system_health": state.get("system_health") if state else "unavailable",
        },
    }


@router.get("/readiness", response_model=Dict[str, Any])
async def get_substrate_readiness():
    """Detailed readiness check without fabricated governance thresholds."""
    state = get_pythia_state()
    return {
        "status": "ready" if is_ready() else "initializing",
        "timestamp": datetime.utcnow().isoformat(),
        "substrate": get_substrate_state(),
        "pythia": {
            "available": state is not None,
            "system_health": state.get("system_health") if state else "unavailable",
            "telemetry_source": state.get("telemetry_source") if state else "unavailable",
        },
    }
