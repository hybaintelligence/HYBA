"""
Mining Pool Management REST API
================================

Manage pool selection, configuration, and switching from the frontend.
Supports Brains as default with fallback options.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# ─────────────────────────────────────────────────────────────────────────
# Pool Configuration Management
# ─────────────────────────────────────────────────────────────────────────

POOLS_CONFIG_PATH = Path(__file__).resolve().parents[2].parent / "config" / "mining_pools_live.json"

class PoolConfig(BaseModel):
    """Mining pool configuration."""
    name: str
    url: str
    stratum_version: int
    username: Optional[str] = None
    password: str = "x"
    worker: str = "hendrix_phi"
    priority: int
    enabled: bool
    is_default: bool = False
    description: Optional[str] = None
    btc_address: Optional[str] = None

class PoolListResponse(BaseModel):
    """Response: list of available pools."""
    default_pool: str
    pools: Dict[str, PoolConfig]
    timestamp: str

class SwitchPoolRequest(BaseModel):
    """Request to switch to a different pool."""
    pool_name: str = Field(..., description="Pool identifier (e.g., 'brains', 'ckpool')")

class PoolStatusResponse(BaseModel):
    """Response: current pool status."""
    active_pool: str
    connected: bool
    shares_submitted: int
    last_share_time: Optional[str] = None
    uptime_seconds: float

# ─────────────────────────────────────────────────────────────────────────
# Global State
# ─────────────────────────────────────────────────────────────────────────

_active_pool: str = "brains"  # Default pool
_pool_stats = {
    "shares_submitted": 0,
    "last_share_time": None,
    "uptime_seconds": 0.0,
}

# ─────────────────────────────────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────────────────────────────────

def load_pools_config() -> Dict[str, Any]:
    """Load pool configuration from JSON file."""
    if POOLS_CONFIG_PATH.exists():
        with open(POOLS_CONFIG_PATH) as f:
            return json.load(f)
    return {
        "default_pool": "brains",
        "pools": {}
    }

def get_default_pool() -> str:
    """Get the default pool name."""
    config = load_pools_config()
    return config.get("default_pool", "brains")

# ─────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/v1/pools", tags=["pool-management"])

# ─────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────

@router.get("/list", response_model=PoolListResponse)
async def list_pools() -> PoolListResponse:
    """Get list of all available mining pools."""
    try:
        config = load_pools_config()
        default = config.get("default_pool", "brains")
        
        pools_data = {}
        for pool_name, pool_config in config.get("pools", {}).items():
            pools_data[pool_name] = PoolConfig(
                name=pool_config.get("name", pool_name),
                url=pool_config.get("url", ""),
                stratum_version=pool_config.get("stratum_version", 1),
                username=pool_config.get("username"),
                password=pool_config.get("password", "x"),
                worker=pool_config.get("worker", "hendrix_phi"),
                priority=pool_config.get("priority", 0),
                enabled=pool_config.get("enabled", False),
                is_default=pool_config.get("is_default", False),
                description=pool_config.get("description"),
                btc_address=pool_config.get("btc_address"),
            )
        
        return PoolListResponse(
            default_pool=default,
            pools=pools_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/default")
async def get_default() -> Dict[str, Any]:
    """Get the default pool configuration."""
    config = load_pools_config()
    default_name = config.get("default_pool", "brains")
    pools = config.get("pools", {})
    
    if default_name not in pools:
        raise HTTPException(status_code=404, detail=f"Default pool '{default_name}' not found")
    
    pool_config = pools[default_name]
    return {
        "pool_name": default_name,
        "pool_config": pool_config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/current")
async def get_current_pool() -> Dict[str, Any]:
    """Get the currently active pool."""
    global _active_pool
    config = load_pools_config()
    pools = config.get("pools", {})
    
    if _active_pool not in pools:
        _active_pool = config.get("default_pool", "brains")
    
    pool_config = pools.get(_active_pool, {})
    
    return {
        "active_pool": _active_pool,
        "pool_config": pool_config,
        "is_connected": True,  # Placeholder
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.post("/switch")
async def switch_pool(req: SwitchPoolRequest) -> Dict[str, Any]:
    """Switch to a different mining pool."""
    global _active_pool
    config = load_pools_config()
    pools = config.get("pools", {})
    
    if req.pool_name not in pools:
        raise HTTPException(status_code=404, detail=f"Pool '{req.pool_name}' not found")
    
    pool_config = pools[req.pool_name]
    if not pool_config.get("enabled", False):
        raise HTTPException(status_code=400, detail=f"Pool '{req.pool_name}' is disabled")
    
    _active_pool = req.pool_name
    
    return {
        "status": "switched",
        "new_active_pool": _active_pool,
        "pool_config": pool_config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/enabled")
async def get_enabled_pools() -> Dict[str, Any]:
    """Get only enabled pools (selectable from frontend)."""
    config = load_pools_config()
    pools = config.get("pools", {})
    
    enabled = {
        name: pool
        for name, pool in pools.items()
        if pool.get("enabled", False)
    }
    
    return {
        "count": len(enabled),
        "enabled_pools": enabled,
        "default": config.get("default_pool", "brains"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/status", response_model=PoolStatusResponse)
async def pool_status() -> PoolStatusResponse:
    """Get current pool connection status."""
    global _active_pool, _pool_stats
    
    return PoolStatusResponse(
        active_pool=_active_pool,
        connected=True,  # Placeholder
        shares_submitted=_pool_stats.get("shares_submitted", 0),
        last_share_time=_pool_stats.get("last_share_time"),
        uptime_seconds=_pool_stats.get("uptime_seconds", 0.0),
    )

@router.post("/report-share")
async def report_share() -> Dict[str, Any]:
    """Report a share submission to track pool stats."""
    global _pool_stats
    _pool_stats["shares_submitted"] = _pool_stats.get("shares_submitted", 0) + 1
    _pool_stats["last_share_time"] = datetime.now(timezone.utc).isoformat()
    
    return {
        "status": "recorded",
        "shares_submitted": _pool_stats["shares_submitted"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/health")
async def pool_health() -> Dict[str, Any]:
    """Health check for pool management system."""
    try:
        config = load_pools_config()
        default_pool = config.get("default_pool", "brains")
        pool_count = len(config.get("pools", {}))
        
        return {
            "status": "healthy",
            "default_pool": default_pool,
            "total_pools": pool_count,
            "enabled_pools": sum(1 for p in config.get("pools", {}).values() if p.get("enabled")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "status": "unhealthy",
            "error": str(e),
        })
