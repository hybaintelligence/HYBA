from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/mining", tags=["mining"])


class PowerScaleRequest(BaseModel):
    scale: float = Field(default=1.0, ge=0.1, le=10.0)


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


def _share_counts(state: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if not state:
        return {"submitted": 0, "accepted": 0, "rejected": 0}
    submitted = int(state.get("total_shares") or 0)
    accepted = int(state.get("accepted_shares") or 0)
    rejected = int(state.get("rejected_shares") or max(submitted - accepted, 0))
    return {"submitted": submitted, "accepted": accepted, "rejected": rejected}


@router.get("/pools")
async def get_pools():
    state = get_pythia_state()
    pools = state.get("pools", []) if state else []
    active_pool_name = state.get("active_pool") if state else None
    quantum = state.get("quantum", {}) if state else {}

    return {
        "pools": pools,
        "summary": {
            "total_pools": len(pools),
            "active_pools": sum(1 for p in pools if p.get("is_active")),
            "active_pool_name": active_pool_name,
            "total_hashrate": state.get("hashrate_ehs") if state else None,
            "capacity_source": quantum.get("capacity_source") if quantum else "not_configured",
            "global_acceptance_rate": state.get("acceptance_rate") if state else None,
            "total_shares_24h": state.get("total_shares", 0) if state else 0,
            "estimated_btc_per_day": None,
            "telemetry_source": state.get("telemetry_source") if state else "unavailable",
        },
    }


@router.get("/stats")
async def get_stats():
    state = get_pythia_state()
    shares = _share_counts(state)
    quantum = state.get("quantum", {}) if state else {}
    hashrate = state.get("hashrate_ehs") if state else None
    acceptance_rate = state.get("acceptance_rate") if state else None

    return {
        "timeframe": "24h",
        "summary": {
            "total_hashrate": hashrate,
            "avg_hashrate": None,
            "peak_hashrate": None,
            "total_shares": shares["submitted"],
            "accepted_shares": shares["accepted"],
            "rejected_shares": shares["rejected"],
            "acceptance_rate": acceptance_rate,
            "estimated_revenue_btc": None,
            "estimated_revenue_usd": None,
            "power_scale": state.get("power_scale") if state else None,
            "telemetry_source": state.get("telemetry_source") if state else "unavailable",
        },
        "timeseries": [],
        "quantum_performance": {
            "quantum_speedup_avg": None,
            "phi_resonance_avg": quantum.get("phi_phase_alignment") if quantum else None,
            "vqe_iterations_avg": None,
            "consciousness_correlation": None,
            "quantum_metrics": quantum,
        },
    }


@router.post("/power")
async def set_power_scale(data: PowerScaleRequest):
    """Update power scale in governance config file."""
    scale = data.scale
    config_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "mining_config.json",
    )

    try:
        temp_file = config_file + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump({"power_scale": scale, "timestamp": os.getpid()}, f)
        os.replace(temp_file, config_file)
        return {"status": "success", "requested_scale": scale}
    except OSError as e:
        return {"status": "error", "message": str(e)}
