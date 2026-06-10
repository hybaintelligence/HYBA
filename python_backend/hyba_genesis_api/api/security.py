from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/security", tags=["security"])


class ShieldParam(BaseModel):
    strength: float = Field(default=0.9, ge=0.0, le=1.0)


@router.get("/status", response_model=Dict[str, Any])
async def get_security_status():
    """Return measured security status only; do not fabricate threats or blocks."""
    return {
        "status": "not_connected",
        "timestamp": datetime.utcnow().isoformat(),
        "threat_level": None,
        "defense_systems": {},
        "recent_threats": [],
        "source": "security_runtime_not_connected",
    }


@router.post("/shield", response_model=Dict[str, Any])
async def post_shield(param: ShieldParam):
    """Reject shield calibration until a real security runtime is connected."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "error": "security_runtime_not_connected",
            "message": "Shield calibration is not implemented for production runtime.",
            "requested_strength": param.strength,
        },
    )
