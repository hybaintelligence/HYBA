"""Operator endpoints for monitoring PYTHIA autonomy and mining pools."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request

from hyba_genesis_api.core.autonomy_persistence import (
    get_latest_report,
    list_all_reports,
)
from hyba_genesis_api.api.pool_management import load_pools_config

router = APIRouter(prefix="/ops", tags=["operator"])


def _redact_pool_credentials(pool_config: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive credentials from pool config."""
    redacted = dict(pool_config)
    if "password" in redacted:
        redacted["password"] = "[REDACTED]"
    if "username" in redacted and redacted["username"]:
        # Keep username but don't expose full value if it looks like an org ID
        if len(redacted["username"]) > 8:
            redacted["username"] = redacted["username"][:4] + "..." + redacted["username"][-4:]
    return redacted


@router.get("/pythia/status")
async def get_pythia_status(request: Request) -> Dict[str, Any]:
    """Get current PYTHIA autonomy status."""
    # Check for startup report from app state
    startup_report = None
    if hasattr(request.app.state, "startup_self_healing_report"):
        startup_report = request.app.state.startup_self_healing_report

    # Get autonomy write mode from environment
    write_mode = os.getenv("HYBA_AUTONOMY_WRITE_MODE", "observe_only")

    return {
        "status": "operational",
        "autonomy_write_mode": write_mode,
        "startup_report_available": startup_report is not None,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/pythia/evidence/latest")
async def get_latest_evidence() -> Optional[Dict[str, Any]]:
    """Get the latest autonomy evidence report."""
    latest_report = get_latest_report()
    if not latest_report:
        raise HTTPException(status_code=404, detail="No autonomy reports available")
    return latest_report


@router.get("/pythia/evidence/list")
async def list_evidence(limit: int = 100) -> Dict[str, Any]:
    """List available autonomy evidence reports."""
    reports = list_all_reports(limit=limit)
    return {
        "count": len(reports),
        "reports": reports,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@router.get("/mining/pools")
async def get_mining_pools() -> Dict[str, Any]:
    """Get mining pool configuration (credentials redacted)."""
    config = load_pools_config()
    redacted_pools = {}
    for pool_name, pool_config in config.get("pools", {}).items():
        redacted_pools[pool_name] = _redact_pool_credentials(pool_config)
    return {
        "default_pool": config.get("default_pool"),
        "pools": redacted_pools,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
