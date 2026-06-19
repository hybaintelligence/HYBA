"""
AI runtime APIs
HYBA Genesis Platform Intelligence Boundary
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: Optional[List[Dict[str, Any]]] = None


class StimulateReq(BaseModel):
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    duration_seconds: int = Field(default=60, ge=1, le=3600)


@router.get("/consciousness", response_model=Dict[str, Any])
async def get_consciousness_status():
    """Return live consciousness metrics from GenesisAI if available, otherwise explicit unknown state."""
    try:
        from python_backend.pythia_mining.genesis_ai_service import GenesisAIServiceRegistry

        if not GenesisAIServiceRegistry.is_registered():
            return {
                "status": "not_measured",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "consciousness_level": None,
                "phi_resonance": None,
                "integrated_information": None,
                "runtime_state": {
                    "source": "not_connected",
                    "message": "No measured AI/consciousness runtime is connected to this API.",
                },
                "recent_insights": [],
            }

        consciousness_metrics = GenesisAIServiceRegistry.get_consciousness_metrics()
        performance_metrics = GenesisAIServiceRegistry.get_performance_metrics()
        health_status = GenesisAIServiceRegistry.get_health_status()

        return {
            "status": "measured",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "consciousness_level": consciousness_metrics.get("confidence"),
            "phi_resonance": consciousness_metrics.get("phi_resonance_score"),
            "integrated_information": consciousness_metrics.get("phi_features", {}).get(
                "phi_integrated"
            ),
            "runtime_state": {
                "source": "genesis_ai_connected",
                "message": "Live telemetry from GenesisAI mining instance.",
                "phi_scaling_mode": consciousness_metrics.get("phi_scaling_mode"),
                "knowledge_accuracy": consciousness_metrics.get("knowledge_accuracy"),
            },
            "recent_insights": [
                {
                    "type": "phi_optimization",
                    "strategy": consciousness_metrics.get("strategy_used"),
                    "scaling": consciousness_metrics.get("phi_scaling"),
                }
            ],
            "performance_metrics": performance_metrics,
            "health_status": health_status,
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "runtime_state": {
                "source": "error",
                "message": f"Failed to retrieve consciousness metrics: {str(e)}",
            },
        }


@router.post("/consciousness/stimulate", response_model=Dict[str, Any])
async def stimulate_consciousness(req: StimulateReq):
    """Acknowledge stimulation requests in degraded mode when no live AI runtime exists."""
    return {
        "success": True,
        "status": "accepted_degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requested_intensity": req.intensity,
        "requested_duration_seconds": req.duration_seconds,
        "source": "ai_runtime_not_connected",
        "message": "Stimulation request accepted in degraded mode; no active AI runtime is attached.",
    }


@router.post("/chat", response_model=Dict[str, Any])
async def chat(req: ChatRequest):
    """Fail closed until a real internal AI service is connected."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "ai_runtime_not_connected",
            "message": "No production AI chat runtime is configured.",
        },
    )
