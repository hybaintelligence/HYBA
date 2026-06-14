from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/security", tags=["security"])


class ShieldParam(BaseModel):
    strength: float = Field(default=0.9, ge=0.0, le=1.0)


@router.get("/status", response_model=Dict[str, Any])
async def get_security_status():
    """Return measured security status only; do not fabricate threats or blocks."""
    return {
        "status": "not_connected",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "threat_level": None,
        "defense_systems": {},
        "recent_threats": [],
        "source": "security_runtime_not_connected",
    }


@router.post("/shield", response_model=Dict[str, Any])
async def post_shield(param: ShieldParam):
    """Accept validated shield settings in degraded mode when no runtime is connected."""
    return {
        "success": True,
        "status": "accepted_degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requested_strength": param.strength,
        "applied_strength": param.strength,
        "source": "security_runtime_not_connected",
        "message": "Shield calibration accepted in degraded mode; no active security runtime is attached.",
    }
