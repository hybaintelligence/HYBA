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
    # TODO: Integrate with live GenesisAI instance
    # For now, return explicit unknown state
    return {
        "status": "not_measured",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "consciousness_level": None,
        "phi_resonance": None,
        "integrated_information": None,
        "runtime_state": {
            "source": "not_connected",
            "message": "No measured AI/consciousness runtime is connected to this API.",
            "integration_required": "GenesisAI telemetry integration pending",
        },
        "recent_insights": [],
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
