"""Security API endpoints with API key enforcement via HYBA_API_KEYS."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from hyba_genesis_api.auth.jwt_handler import APIKeyManager

router = APIRouter(prefix="/api/security", tags=["security"])

_api_key_manager: Optional[APIKeyManager] = None


def _get_api_key_manager() -> APIKeyManager:
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


async def api_key_dependency(x_api_key: str = Header(None)) -> None:
    """Require a valid API key in X-API-Key header when HYBA_API_KEYS is configured."""
    api_keys = os.getenv("HYBA_API_KEYS", "")
    if not api_keys:
        # No API keys configured — security endpoints operate in degraded mode
        return
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header is required when HYBA_API_KEYS is configured",
        )
    manager = _get_api_key_manager()
    result = manager.validate_api_key(x_api_key)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


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


@router.post("/shield", response_model=Dict[str, Any], dependencies=[Depends(api_key_dependency)])
async def post_shield(param: ShieldParam):
    """Accept validated shield settings in degraded mode when no runtime is connected.
    
    Requires a valid X-API-Key header when HYBA_API_KEYS is configured.
    """
    return {
        "success": True,
        "status": "accepted_degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "requested_strength": param.strength,
        "applied_strength": param.strength,
        "source": "security_runtime_not_connected",
        "message": "Shield calibration accepted in degraded mode; no active security runtime is attached.",
    }