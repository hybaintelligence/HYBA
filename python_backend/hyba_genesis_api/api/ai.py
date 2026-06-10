"""
AI runtime APIs
HYBA Genesis Platform Intelligence Boundary
"""

from __future__ import annotations

from datetime import datetime
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
    """Return explicit unknown runtime-integration state instead of fabricated cognition."""
    return {
        "status": "not_measured",
        "timestamp": datetime.utcnow().isoformat(),
        "consciousness_level": None,
        "phi_resonance": None,
        "integrated_information": None,
        "runtime_state": {
            "source": "not_connected",
            "message": "No measured AI/consciousness runtime is connected to this API.",
        },
        "recent_insights": [],
    }


@router.post("/consciousness/stimulate", response_model=Dict[str, Any])
async def stimulate_consciousness(req: StimulateReq):
    """Reject stimulation commands until a real controlled runtime exists."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "ai_runtime_not_connected",
            "message": "Consciousness stimulation is not implemented for production runtime.",
            "requested_intensity": req.intensity,
            "requested_duration_seconds": req.duration_seconds,
        },
    )


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
