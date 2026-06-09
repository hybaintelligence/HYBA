from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any
import json
import os

router = APIRouter(prefix="/api/mining", tags=["mining"])


class PowerScaleRequest(BaseModel):
    scale: float = Field(default=1.0, ge=0.1, le=10.0)


def get_pythia_state():
    state_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "pythia_state.json")
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                return json.load(f)
        except:
            pass
    return None

@router.get("/pools")
async def get_pools():
    state = get_pythia_state()
    active_pool_name = state.get("active_pool", "Unknown") if state else "Unknown"
    pools = state.get("pools", []) if state else []
    
    return {
        "pools": pools,
        "summary": {
            "total_pools": len(pools),
            "active_pools": sum(1 for p in pools if p.get("is_active")),
            "active_pool_name": active_pool_name,
            "total_hashrate": 2071.08, # Base quantum metric
            "global_acceptance_rate": state.get("acceptance_rate", 0.0) if state else 0.0,
            "total_shares_24h": state.get("total_shares", 0) if state else 0,
            "estimated_btc_per_day": 0.00054321
        }
    }

@router.get("/stats")
async def get_stats():
    state = get_pythia_state()
    total_shares = state.get("total_shares", 0) if state else 0
    acceptance_rate = state.get("acceptance_rate", 1.0) if state else 1.0
    accepted = int(total_shares * acceptance_rate)
    hashrate = state.get("hashrate_ehs", 50.0) if state else 50.0
    
    return {
      "timeframe": "24h",
      "summary": {
        "total_hashrate": hashrate,
        "avg_hashrate": hashrate * 0.98,
        "peak_hashrate": hashrate * 1.15,
        "total_shares": total_shares,
        "accepted_shares": accepted,
        "rejected_shares": total_shares - accepted,
        "acceptance_rate": acceptance_rate,
        "estimated_revenue_btc": 0.00037801,
        "estimated_revenue_usd": 16.82,
        "power_scale": state.get("power_scale", 1.0) if state else 1.0
      },
      "timeseries": [
        {
          "hashrate": hashrate,
          "shares_submitted": total_shares,
          "shares_accepted": accepted,
          "acceptance_rate": acceptance_rate
        }
      ],
      "quantum_performance": {
        "quantum_speedup_avg": 38.7,
        "phi_resonance_avg": 0.0594,
        "vqe_iterations_avg": 87.3,
        "consciousness_correlation": state.get("consciousness_level", 0.1838) if state else 0.1838,
        "quantum_metrics": state.get("quantum", {}) if state else {}
      }
    }

@router.post("/power")
async def set_power_scale(data: PowerScaleRequest):
    """Update power scale in governance config file."""
    scale = data.scale
    config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "mining_config.json")
    
    try:
        temp_file = config_file + ".tmp"
        with open(temp_file, "w") as f:
            json.dump({"power_scale": scale, "timestamp": os.getpid()}, f)
        os.replace(temp_file, config_file)
        return {"status": "success", "requested_scale": scale}
    except Exception as e:
        return {"status": "error", "message": str(e)}
