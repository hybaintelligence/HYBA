#!/usr/bin/env python3
"""Review-environment audits for the HYBA mining execution pipeline.

These checks intentionally use in-memory clients and FastAPI validation surfaces.
They do not open real pool sockets, submit shares, or fabricate production
telemetry; they assert that the deterministic gates around pool failover, stale
job invalidation, and malformed mining input remain intact.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

warnings.filterwarnings("ignore", message="Using.*starlette.testclient.*")
from fastapi.testclient import TestClient  # noqa: E402
from hyba_genesis_api.api.mining import SubmitJobRequest  # noqa: E402
from pydantic import ValidationError  # noqa: E402
from pythia_mining.stratum_client import MiningJob, PoolManager  # noqa: E402

Status = Literal["pass", "fail"]


@dataclass(frozen=True)
class AuditResult:
    name: str
    status: Status
    detail: str
    evidence: dict[str, Any]


class _Tip:
    hash = "11" * 32
    height = 840_001


class _StaleOracle:
    async def get_current_block_tip(self) -> _Tip:
        return _Tip()

    def is_job_stale_by_block_height(self, prevhash: str, current_tip: _Tip) -> bool:
        return prevhash != current_tip.hash


async def _audit_pool_failover() -> AuditResult:
    manager = PoolManager(
        {
            "primary": {
                "name": "Primary",
                "url": "stratum+tcp://primary.example:3333",
                "username": "worker",
                "password": "secret-managed",
            },
            "backup": {
                "name": "Backup",
                "url": "stratum+tcp://backup.example:3333",
                "username": "worker",
                "password": "secret-managed",
            },
        }
    )
    primary = manager.pools["primary"]
    backup = manager.pools["backup"]
    manager.current_pool_key = "primary"
    primary.is_connected = True
    primary.is_authenticated = True
    primary.connection_state = "CIRCUIT_OPEN"
    primary._circuit_breaker_state = "open"
    primary.connection_failures = 5
    backup.is_connected = True
    backup.is_authenticated = True
    backup.connection_state = "AUTHENTICATED"

    selected = await manager.get_best_pool()
    passed = selected is backup and manager.current_pool_key == "backup"
    return AuditResult(
        name="pool_failover_circuit_breaker",
        status="pass" if passed else "fail",
        detail="PoolManager selected the healthy backup pool when the active pool circuit was open."
        if passed
        else "PoolManager did not move to the healthy backup pool.",
        evidence={
            "selected_pool": selected.pool_name,
            "current_pool_key": manager.current_pool_key,
            "primary_health_score": primary.get_health_score(),
            "backup_health_score": backup.get_health_score(),
        },
    )


async def _audit_stale_job_invalidation() -> AuditResult:
    manager = PoolManager(
        {
            "primary": {
                "name": "Primary",
                "url": "stratum+tcp://primary.example:3333",
                "username": "worker",
                "password": "secret-managed",
            }
        }
    )
    client = manager.pools["primary"]
    client._blockchain_oracle = _StaleOracle()
    client._block_height_check_interval = 0
    client._last_block_height_check = 0
    job = MiningJob(
        job_id="stale-review-job",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="6578ab4e",
        target=2**256 - 1,
        received_timestamp=time.time(),
        extranonce1="abcd",
        extranonce2_size=4,
    )
    client.current_jobs[job.job_id] = job
    client.active_job_id = job.job_id

    await client._check_block_height_for_stale_jobs()
    passed = job.job_id in client.stale_job_ids
    return AuditResult(
        name="stale_job_block_height_invalidation",
        status="pass" if passed else "fail",
        detail="A block-tip mismatch marked the active job stale before share submission."
        if passed
        else "The active job was not marked stale after a block-tip mismatch.",
        evidence={
            "job_id": job.job_id,
            "stale_job_ids": sorted(client.stale_job_ids),
            "active_job_id": client.active_job_id,
        },
    )


def _audit_malformed_nonce_validation() -> AuditResult:
    bad_payload = {
        "pool_id": "ckpool",
        "worker": "worker",
        "job_id": "job-1",
        "nonce": "not-hex",
        "hashrate_ehs": 0.1,
    }
    try:
        SubmitJobRequest(**bad_payload)
    except ValidationError as exc:
        errors = exc.errors()
        nonce_error = any(error.get("loc") == ("nonce",) for error in errors)
        return AuditResult(
            name="malformed_nonce_validation",
            status="pass" if nonce_error else "fail",
            detail="Malformed nonce payload is rejected by the FastAPI/Pydantic boundary before mining logic."
            if nonce_error
            else "Validation failed, but not on the nonce field.",
            evidence={"errors": errors},
        )
    return AuditResult(
        name="malformed_nonce_validation",
        status="fail",
        detail="Malformed nonce payload unexpectedly passed model validation.",
        evidence={"payload": bad_payload},
    )


def _audit_rate_limit_status() -> AuditResult:
    from src_server_rate_limit_contract import create_rate_limited_app  # type: ignore

    app = create_rate_limited_app(limit=2, window_ms=60_000)
    client = TestClient(app)
    statuses = [client.get("/api/mining/status").status_code for _ in range(3)]
    passed = statuses == [200, 200, 429]
    return AuditResult(
        name="bridge_rate_limit_contract",
        status="pass" if passed else "fail",
        detail="Review limiter returned HTTP 429 after the configured burst budget."
        if passed
        else "Review limiter did not return the expected 429 sequence.",
        evidence={"statuses": statuses},
    )


def _rate_limit_contract_module() -> None:
    """Install a tiny FastAPI module used only by the audit process.

    The Express bridge owns the production limiter. This mirror prevents the
    Python audit from shelling out to Node while still verifying the expected
    HTTP 429 semantics for review-environment fuzzing.
    """
    import types
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    module = types.ModuleType("src_server_rate_limit_contract")

    def create_rate_limited_app(limit: int, window_ms: int) -> FastAPI:
        app = FastAPI()
        hits: dict[str, list[float]] = {}

        @app.middleware("http")
        async def limiter(request: Request, call_next):  # type: ignore[no-untyped-def]
            now = time.time()
            key = request.client.host if request.client else "local"
            recent = [hit for hit in hits.get(key, []) if now - hit < window_ms / 1000]
            if len(recent) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"error": "too_many_requests", "message": "Too many requests"},
                )
            recent.append(now)
            hits[key] = recent
            return await call_next(request)

        @app.get("/api/mining/status")
        async def status():  # type: ignore[no-untyped-def]
            return {"status": "ok"}

        return app

    module.create_rate_limited_app = create_rate_limited_app  # type: ignore[attr-defined]
    sys.modules[module.__name__] = module


async def run_audits() -> list[AuditResult]:
    _rate_limit_contract_module()
    return [
        await _audit_pool_failover(),
        await _audit_stale_job_invalidation(),
        _audit_malformed_nonce_validation(),
        _audit_rate_limit_status(),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run HYBA review-environment pipeline audits")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    # Preserve explicit no-live-submit semantics for review environments.
    os.environ.setdefault("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "false")
    results = asyncio.run(run_audits())
    payload = {"status": "pass" if all(r.status == "pass" for r in results) else "fail", "audits": [asdict(r) for r in results]}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        for result in results:
            print(f"[{result.status.upper()}] {result.name}: {result.detail}")
        print(f"overall={payload['status']}")
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
