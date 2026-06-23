"""Operational mining telemetry, audit, and alert endpoints.

These endpoints expose production-readiness controls without changing the mining
runtime boundary. They are read-only and require mining read permission.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from hyba_genesis_api.api.mining import get_pythia_state, require_mining_read
from pythia_mining.metrics_store import get_metrics_store

router = APIRouter(prefix="/api/mining/ops", tags=["mining-ops"])


def _audit_log_dir() -> Path:
    return Path(os.getenv("HYBA_AUDIT_LOG_DIR", "logs/audit"))


def _parse_audit_line(line: str) -> Optional[dict[str, Any]]:
    # File format is "timestamp | LEVEL | logger | {json}".
    if " | " in line:
        candidate = line.rsplit(" | ", 1)[-1]
    else:
        candidate = line
    try:
        event = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    # Defensive redaction in case future event_data adds sensitive fields.
    event_data = event.get("event_data") or {}
    for key in list(event_data.keys()):
        lowered = key.lower()
        if "password" in lowered or "secret" in lowered or "token" in lowered:
            event_data[key] = "[REDACTED]"
    event["event_data"] = event_data
    return event


def _recent_audit_events(limit: int) -> list[dict[str, Any]]:
    log_dir = _audit_log_dir()
    if not log_dir.exists():
        return []
    files = sorted(
        log_dir.glob("audit_*.log"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    events: list[dict[str, Any]] = []
    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            parsed = _parse_audit_line(line)
            if parsed is not None:
                events.append(parsed)
            if len(events) >= limit:
                return events
    return events


def _derive_alerts(
    metrics: list[dict[str, Any]], state: Optional[dict[str, Any]]
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc).isoformat()
    for pool in metrics:
        pool_name = pool.get("pool_name")
        rejected = int(pool.get("shares_rejected") or 0)
        submitted = int(pool.get("shares_submitted") or 0)
        failures = int(pool.get("connection_failures") or 0)
        latency = pool.get("avg_latency_ms")
        acceptance_rate = float(pool.get("acceptance_rate") or 0.0)
        if submitted >= 10 and acceptance_rate < 0.5:
            alerts.append(
                {
                    "severity": "warning",
                    "code": "low_share_acceptance_rate",
                    "pool_name": pool_name,
                    "message": "Share acceptance rate is below 50% after at least 10 submissions.",
                    "value": acceptance_rate,
                    "timestamp": now,
                }
            )
        if submitted >= 10 and rejected / max(submitted, 1) > 0.5:
            alerts.append(
                {
                    "severity": "warning",
                    "code": "high_share_rejection_rate",
                    "pool_name": pool_name,
                    "message": "Share rejection rate is above 50% after at least 10 submissions.",
                    "value": rejected / max(submitted, 1),
                    "timestamp": now,
                }
            )
        if failures >= 3:
            alerts.append(
                {
                    "severity": "critical",
                    "code": "repeated_pool_connection_failures",
                    "pool_name": pool_name,
                    "message": "Pool has three or more recorded connection failures.",
                    "value": failures,
                    "timestamp": now,
                }
            )
        if latency is not None and float(latency) > 5_000:
            alerts.append(
                {
                    "severity": "warning",
                    "code": "high_pool_latency",
                    "pool_name": pool_name,
                    "message": "Average pool latency is above 5 seconds.",
                    "value": latency,
                    "timestamp": now,
                }
            )
    if state and state.get("system_health") in {"DEGRADED", "ERROR"}:
        alerts.append(
            {
                "severity": "critical",
                "code": "mining_system_health_degraded",
                "message": "PYTHIA mining state reports degraded or error health.",
                "value": state.get("system_health"),
                "timestamp": now,
            }
        )
    return alerts


def _pool_metrics_to_dict() -> list[dict[str, Any]]:
    store = get_metrics_store()
    return [metric.__dict__ for metric in store.get_all_pool_metrics()]


@router.get("/metrics", dependencies=[Depends(require_mining_read)])
async def mining_metrics(
    share_history_limit: int = Query(50, ge=0, le=500),
    connection_history_limit: int = Query(50, ge=0, le=500),
):
    """Return persisted mining metrics and derived alert signals."""
    store = get_metrics_store()
    pools = _pool_metrics_to_dict()
    state = get_pythia_state() or {}
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pools": pools,
        "share_history": store.get_share_history(limit=share_history_limit),
        "connection_history": store.get_connection_history(
            limit=connection_history_limit
        ),
        "alerts": _derive_alerts(pools, state),
        "state": {
            "active_pool": state.get("active_pool"),
            "system_health": state.get("system_health"),
            "hashrate_ehs": state.get("hashrate_ehs"),
            "capacity_source": state.get("capacity_source", "not_configured"),
        },
    }


@router.get("/audit", dependencies=[Depends(require_mining_read)])
async def recent_audit_events(limit: int = Query(100, ge=0, le=1000)):
    """Return recent structured audit events with defensive secret redaction."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_log_dir": str(_audit_log_dir()),
        "events": _recent_audit_events(limit),
    }


@router.get("/profitability", dependencies=[Depends(require_mining_read)])
async def profitability_inputs():
    """Return profitability inputs without inventing market or power-cost data."""
    state = get_pythia_state() or {}
    return {
        "status": "input_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hashrate_ehs": state.get("hashrate_ehs"),
        "capacity_source": state.get("capacity_source", "not_configured"),
        "estimated_btc_per_day": None,
        "estimated_revenue_usd": None,
        "electricity_cost_usd_per_kwh": None,
        "btc_price_usd": None,
        "message": "Profitability requires externally supplied BTC price, power draw, electricity cost, pool fee, and hardware data.",
    }


@router.get("/autonomics", dependencies=[Depends(require_mining_read)])
async def autonomics_state():
    """Return the latest standalone PULVINI autonomics state exported by mining."""
    state = get_pythia_state() or {}
    autonomics = state.get("pulvini_autonomics") or {}
    return {
        "status": "ok" if autonomics else "unavailable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "autonomic_repairs": state.get("autonomic_repairs", 0),
        "latest_autonomic_event": state.get("latest_autonomic_event"),
        "pulvini_autonomics": autonomics,
    }
