"""HYBA Mining API — regulated PYTHIA/MIDAS mining control boundary."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, validator

from hyba_genesis_api.auth.jwt_handler import TokenPayload, get_token_payload
from hyba_genesis_api.core.midas_controls import (
    BackpressureError,
    MiningState,
    RateLimitExceededError,
    RequestStatus,
    StateTransitionError,
    midas_backpressure_guard,
    midas_rate_limiter,
    midas_state_machine,
    mining_request_tracker,
)

router = APIRouter(prefix="/api/mining", tags=["mining"])

# In-memory process state. The PYTHIA daemon writes pythia_state.json for runtime
# telemetry; durable accounting/custody remains outside this application boundary.
_ACTIVE_CONNECTION: Optional[Dict[str, Any]] = None
_JOBS_SUBMITTED: int = 0
_SHARES_ACCEPTED: int = 0
_SHARES_REJECTED: int = 0
_PYTHIA_PROCESS: Optional[subprocess.Popen] = None
_DAEMON_STARTED: bool = False

MINING_CONTROL_ROLES = {"ceo", "treasury_admin", "mining_operator", "mining:operate"}
MINING_READ_ROLES = {
    "ceo",
    "treasury_admin",
    "mining_operator",
    "treasury_viewer",
    "mining:read",
    "mining:operate",
}


class PowerScaleRequest(BaseModel):
    scale: float = Field(default=1.0, ge=0.1, le=10.0)


class ConnectRequest(BaseModel):
    pool_id: str = Field(..., description="Pool identifier (viabtc, nicehash, braiins, ckpool)")
    worker: str = Field(..., description="Worker name (e.g. PYTHIA.001)")
    password: str = Field(..., description="Worker password")
    capacity_ehs: float = Field(default=1.0, ge=0.01, le=100.0, description="Capacity in EH/s")

    @validator("pool_id")
    def validate_pool(cls, value: str) -> str:
        allowed = {"viabtc", "nicehash", "braiins", "ckpool"}
        if value.lower() not in allowed:
            raise ValueError(f"pool_id must be one of: {', '.join(sorted(allowed))}")
        return value.lower()

    @validator("worker")
    def validate_worker(cls, value: str) -> str:
        if not value or len(value) > 64:
            raise ValueError("Worker name must be 1-64 characters")
        if not all(char.isalnum() or char in "._-" for char in value):
            raise ValueError("Worker name can only contain alphanumeric characters, dots, underscores, and hyphens")
        return value


class SubmitJobRequest(BaseModel):
    pool_id: str = Field(...)
    worker: str = Field(...)
    job_id: str = Field(..., description="Job identifier from pool")
    nonce: str = Field(..., description="Mining nonce (hex)")
    hashrate_ehs: float = Field(default=0.0, ge=0.0)
    extranonce2: Optional[str] = Field(None, description="Extranonce2 value (hex)")

    @validator("nonce")
    def validate_nonce(cls, value: str) -> str:
        if not value.startswith("0x"):
            raise ValueError("Nonce must start with 0x")
        hex_value = value[2:]
        if not all(char in "0123456789abcdefABCDEF" for char in hex_value):
            raise ValueError("Nonce must be valid hexadecimal")
        if len(hex_value) > 16:
            raise ValueError("Nonce too long")
        return value


async def require_mining_control(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
    """Require mining operation permission; treasury allocation is intentionally separate."""
    if not any(role in MINING_CONTROL_ROLES for role in payload.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Mining control requires one of: {', '.join(sorted(MINING_CONTROL_ROLES))}",
        )
    return payload


async def require_mining_read(payload: TokenPayload = Depends(get_token_payload)) -> TokenPayload:
    if not any(role in MINING_READ_ROLES for role in payload.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Mining read access requires one of: {', '.join(sorted(MINING_READ_ROLES))}",
        )
    return payload


def _request_id(request: Request) -> str:
    request_id = request.headers.get("x-request-id") or request.headers.get("x-correlation-id")
    if request_id:
        return request_id[:128]
    return mining_request_tracker.generate_request_id()


def _idempotency_key(request: Request, explicit: str | None, operation_type: str, parameters: dict[str, Any]) -> str:
    return (
        explicit
        or request.headers.get("idempotency-key")
        or request.headers.get("x-idempotency-key")
        or mining_request_tracker.generate_idempotency_key(operation_type, parameters)
    )


def _admit_midas_control(request_id: str) -> None:
    try:
        midas_rate_limiter.allow(request_id=request_id)
        midas_backpressure_guard.admit(request_id=request_id)
    except RateLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=exc.to_response_body(),
            headers={"Retry-After": str(max(1, int(exc.retry_after_seconds)))},
        ) from exc
    except BackpressureError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.to_response_body()) from exc


def _state_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "pythia_state.json",
    )


def _config_path() -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "mining_config.json",
    )


def get_pythia_state() -> Optional[Dict[str, Any]]:
    path = _state_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _write_state(state: Dict[str, Any]) -> None:
    path = _state_path()
    temp = path + ".tmp"
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)
        os.replace(temp, path)
        os.chmod(path, 0o600)
    except OSError as exc:
        if os.path.exists(temp):
            try:
                os.unlink(temp)
            except OSError:
                pass
        raise RuntimeError(f"Failed to write state file: {exc}") from exc


def _share_counts(state: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if not state:
        return {"submitted": _JOBS_SUBMITTED, "accepted": _SHARES_ACCEPTED, "rejected": _SHARES_REJECTED}
    submitted = int(state.get("total_shares") or _JOBS_SUBMITTED)
    accepted = int(state.get("accepted_shares") or _SHARES_ACCEPTED)
    rejected = int(state.get("rejected_shares") or max(submitted - accepted, 0))
    return {"submitted": submitted, "accepted": accepted, "rejected": rejected}


def _redacted_connection(connection: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if connection is None:
        return None
    redacted = dict(connection)
    redacted.pop("password", None)
    return redacted


def start_pythia_daemon() -> Dict[str, Any]:
    """Start the Pythia quantum mining orchestrator as a background process."""
    global _PYTHIA_PROCESS, _DAEMON_STARTED

    if _DAEMON_STARTED and _PYTHIA_PROCESS and _PYTHIA_PROCESS.poll() is None:
        return {"status": "already_running", "pid": _PYTHIA_PROCESS.pid}

    python_backend = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", python_backend)

    try:
        _PYTHIA_PROCESS = subprocess.Popen(
            [sys.executable, "-m", "pythia_mining.main"],
            cwd=os.path.dirname(python_backend),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _DAEMON_STARTED = True
        return {"status": "started", "pid": _PYTHIA_PROCESS.pid}
    except Exception as exc:  # pragma: no cover - OS/runtime dependent
        return {"status": "error", "message": str(exc)}


def stop_pythia_daemon() -> Dict[str, Any]:
    """Gracefully stop the Pythia mining daemon."""
    global _PYTHIA_PROCESS, _DAEMON_STARTED

    if _PYTHIA_PROCESS and _PYTHIA_PROCESS.poll() is None:
        _PYTHIA_PROCESS.terminate()
        try:
            _PYTHIA_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _PYTHIA_PROCESS.kill()
        _DAEMON_STARTED = False
        return {"status": "stopped"}
    _DAEMON_STARTED = False
    return {"status": "not_running"}


POOL_PROFILES = {
    "viabtc": {
        "name": "ViaBTC BTC",
        "url": os.getenv("HYBA_POOL_VIABTC_URL", "stratum+ssl://btc.viabtc.io:3334"),
        "stratum_version": 1,
        "tls_required": True,
    },
    "nicehash": {
        "name": "NiceHash SHA256",
        "url": os.getenv("HYBA_POOL_NICEHASH_URL", "stratum+ssl://sha256.eu.nicehash.com:3334"),
        "stratum_version": 1,
        "tls_required": True,
    },
    "braiins": {
        "name": "Braiins Pool",
        "url": os.getenv("HYBA_POOL_BRAIINS_URL", "stratum2+tcp://eu.braiins-pool.com:3336"),
        "stratum_version": 2,
        "tls_required": False,
    },
    "ckpool": {
        "name": "Solo CKPool",
        "url": os.getenv("HYBA_POOL_CKPOOL_URL", "stratum+tcp://solo.ckpool.org:3333"),
        "stratum_version": 1,
        "tls_required": False,
    },
}


@router.get("/pools", dependencies=[Depends(require_mining_read)])
async def get_pools():
    state = get_pythia_state()
    pools = state.get("pools", []) if state else []
    active_pool_name = state.get("active_pool") if state else None
    quantum = state.get("quantum", {}) if state else {}

    if not pools:
        for pool_id, profile in POOL_PROFILES.items():
            is_active = _ACTIVE_CONNECTION is not None and _ACTIVE_CONNECTION.get("pool_id") == pool_id
            pools.append(
                {
                    "pool_id": pool_id,
                    "name": profile["name"],
                    "url": profile["url"],
                    "stratum_version": profile["stratum_version"],
                    "status": "connected" if is_active else "disconnected",
                    "is_active": is_active,
                    "performance": {
                        "latency_ms": None,
                        "shares_submitted": _JOBS_SUBMITTED,
                        "shares_accepted": _SHARES_ACCEPTED,
                        "shares_rejected": _SHARES_REJECTED,
                        "acceptance_rate": _SHARES_ACCEPTED / max(_JOBS_SUBMITTED, 1),
                    },
                }
            )
        active_pool_name = _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None

    total_hashrate = state.get("hashrate_ehs") if state else None
    if total_hashrate is None and _ACTIVE_CONNECTION:
        total_hashrate = _ACTIVE_CONNECTION.get("capacity_ehs")

    return {
        "pools": pools,
        "summary": {
            "total_pools": len(pools),
            "active_pools": sum(1 for pool in pools if pool.get("is_active")),
            "active_pool_name": active_pool_name,
            "total_hashrate": total_hashrate,
            "capacity_source": "configured" if total_hashrate is not None else "not_configured",
            "global_acceptance_rate": _SHARES_ACCEPTED / max(_JOBS_SUBMITTED, 1),
            "total_shares_24h": _JOBS_SUBMITTED,
            "estimated_btc_per_day": None,
            "telemetry_source": "live_api",
            "daemon_running": _DAEMON_STARTED and _PYTHIA_PROCESS is not None and _PYTHIA_PROCESS.poll() is None,
            "midas_state": midas_state_machine.get_state().value,
            "midas_metrics": midas_state_machine.validate_state_machine()["metrics"],
            "quantum_metrics": quantum,
        },
    }


@router.post("/connect", dependencies=[Depends(require_mining_control)])
async def connect_to_pool(
    req: ConnectRequest,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """Connect to a mining pool through MIDAS state, idempotency, and backpressure controls."""
    global _ACTIVE_CONNECTION

    request_id = _request_id(request)
    parameters = {"pool_id": req.pool_id, "worker": req.worker, "capacity_ehs": req.capacity_ehs}
    idem = _idempotency_key(request, idempotency_key, "connect", parameters)
    tracked = mining_request_tracker.create_request("connect", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result
    if tracked.status == RequestStatus.PROCESSING:
        return {"status": "processing", "request_id": tracked.request_id, "idempotency_key": idem}

    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)

    try:
        profile = POOL_PROFILES.get(req.pool_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown pool: {req.pool_id}")
        if _ACTIVE_CONNECTION is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "mining_already_connected", "active_connection": _redacted_connection(_ACTIVE_CONNECTION)},
            )

        midas_state_machine.transition(
            MiningState.STARTING,
            request_id=request_id,
            reason="operator requested pool connection",
            metadata={"pool_id": req.pool_id, "worker": req.worker, "tracked_request_id": tracked.request_id},
        )
        daemon_status = start_pythia_daemon()
        if daemon_status.get("status") == "error":
            raise RuntimeError(str(daemon_status.get("message")))

        _ACTIVE_CONNECTION = {
            "pool_id": req.pool_id,
            "worker": req.worker,
            "profile": profile,
            "capacity_ehs": req.capacity_ehs,
            "connected_at": datetime.utcnow().isoformat(),
            "request_id": request_id,
        }
        state = get_pythia_state() or {}
        state["active_pool"] = req.pool_id
        state["hashrate_ehs"] = req.capacity_ehs
        state["capacity_source"] = "configured"
        state["telemetry_source"] = "live_api"
        state["system_health"] = "HEALTHY"
        state["midas_state"] = "running"
        _write_state(state)

        midas_state_machine.transition(
            MiningState.RUNNING,
            request_id=request_id,
            reason="pool connection established",
            metadata={"pool_id": req.pool_id, "tracked_request_id": tracked.request_id},
        )
        result = {
            "status": "connected",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "pool": profile["name"],
            "worker": req.worker,
            "url": profile["url"],
            "capacity_ehs": req.capacity_ehs,
            "daemon": daemon_status,
            "midas_state": midas_state_machine.get_state().value,
            "connected_at": _ACTIVE_CONNECTION["connected_at"],
        }
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.COMPLETED, result=result)
        return result
    except HTTPException as exc:
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.FAILED, error=str(exc.detail))
        raise
    except (RuntimeError, StateTransitionError) as exc:
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.FAILED, error=str(exc))
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail={"error": "mining_connect_failed", "detail": str(exc), "request_id": request_id}) from exc
    finally:
        midas_backpressure_guard.release()


@router.post("/submit")
async def submit_job(
    job: SubmitJobRequest,
    request: Request,
    _payload: TokenPayload = Depends(require_mining_control),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """Submit a share result after local proof-of-work validation and MIDAS controls."""
    global _JOBS_SUBMITTED, _SHARES_ACCEPTED, _SHARES_REJECTED

    request_id = _request_id(request)
    parameters = {"pool_id": job.pool_id, "worker": job.worker, "job_id": job.job_id, "nonce": job.nonce[:18]}
    idem = _idempotency_key(request, idempotency_key, "submit", parameters)
    tracked = mining_request_tracker.create_request("submit", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result
    if tracked.status == RequestStatus.PROCESSING:
        return {"status": "processing", "request_id": tracked.request_id, "idempotency_key": idem}

    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)

    try:
        if _ACTIVE_CONNECTION is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active pool connection. Call /api/mining/connect first.")
        if midas_state_machine.get_state() != MiningState.RUNNING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "midas_not_running", "state": midas_state_machine.get_state().value})
        if job.pool_id != _ACTIVE_CONNECTION.get("pool_id"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pool mismatch. You can only submit shares for the active pool.")
        if job.worker != _ACTIVE_CONNECTION.get("worker"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Worker mismatch. You can only submit shares for the connected worker.")

        _JOBS_SUBMITTED += 1
        try:
            from pythia_mining.mining_validation import MiningValidationError, validate_share
            from pythia_mining.stratum_client import MiningJob

            state = get_pythia_state() or {}
            current_job_data = state.get("current_job")
            if not current_job_data:
                _SHARES_REJECTED += 1
                result_status = "rejected"
                reason = "no_active_mining_job"
            else:
                nonce_int = int(job.nonce, 16)
                mining_job = MiningJob(
                    job_id=current_job_data.get("job_id", job.job_id),
                    prevhash=current_job_data.get("prevhash", "00" * 32),
                    coinbase_parts=(current_job_data.get("coinbase1", ""), current_job_data.get("coinbase2", "")),
                    merkle_branch=current_job_data.get("merkle_branch", []),
                    version=current_job_data.get("version", "20000000"),
                    nbits=current_job_data.get("nbits", "1d00ffff"),
                    ntime=current_job_data.get("ntime", ""),
                    target=current_job_data.get("target", 2**256 - 1),
                    extranonce1=current_job_data.get("extranonce1", ""),
                    extranonce2_size=current_job_data.get("extranonce2_size", 4),
                )
                extranonce2 = job.extranonce2 or ("00" * mining_job.extranonce2_size)
                validation = validate_share(mining_job, nonce_int, extranonce2)
                if validation.valid:
                    _SHARES_ACCEPTED += 1
                    result_status = "accepted"
                    reason = None
                else:
                    _SHARES_REJECTED += 1
                    result_status = "rejected"
                    reason = validation.reason or "invalid_proof_of_work"
        except MiningValidationError as exc:
            _SHARES_REJECTED += 1
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Validation error: {exc}") from exc
        except ValueError as exc:
            _SHARES_REJECTED += 1
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid nonce format: {exc}") from exc
        except Exception as exc:
            _SHARES_REJECTED += 1
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Share validation failed: {exc}") from exc

        state = get_pythia_state() or {}
        state["total_shares"] = _JOBS_SUBMITTED
        state["accepted_shares"] = _SHARES_ACCEPTED
        state["rejected_shares"] = _SHARES_REJECTED
        state["acceptance_rate"] = _SHARES_ACCEPTED / max(_JOBS_SUBMITTED, 1)
        state["hashrate_ehs"] = job.hashrate_ehs if job.hashrate_ehs > 0 else state.get("hashrate_ehs")
        state["last_job"] = {
            "job_id": job.job_id,
            "nonce": job.nonce[:16] + "...",
            "timestamp": datetime.utcnow().isoformat(),
            "status": result_status,
            "reason": reason,
            "request_id": request_id,
        }
        _write_state(state)

        response = {
            "status": result_status,
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "job_id": job.job_id,
            "worker": job.worker,
            "pool_id": job.pool_id,
            "hashrate_ehs": state.get("hashrate_ehs"),
            "total_submitted": _JOBS_SUBMITTED,
            "total_accepted": _SHARES_ACCEPTED,
            "acceptance_rate": _SHARES_ACCEPTED / max(_JOBS_SUBMITTED, 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
        if reason:
            response["rejection_reason"] = reason
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.COMPLETED, result=response)
        return response
    except HTTPException as exc:
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.FAILED, error=str(exc.detail))
        raise
    finally:
        midas_backpressure_guard.release()


@router.get("/status", dependencies=[Depends(require_mining_read)])
async def mining_status():
    state = get_pythia_state()
    shares = _share_counts(state)
    return {
        "active": _ACTIVE_CONNECTION is not None,
        "daemon_running": _DAEMON_STARTED and _PYTHIA_PROCESS is not None and _PYTHIA_PROCESS.poll() is None,
        "connection": _redacted_connection(_ACTIVE_CONNECTION),
        "shares": shares,
        "acceptance_rate": shares["accepted"] / max(shares["submitted"], 1),
        "hashrate_ehs": state.get("hashrate_ehs") if state else (_ACTIVE_CONNECTION.get("capacity_ehs") if _ACTIVE_CONNECTION else None),
        "capacity_source": (state or {}).get("capacity_source", "configured" if _ACTIVE_CONNECTION else "not_configured"),
        "last_job": state.get("last_job") if state else None,
        "system_health": state.get("system_health") if state else "HEALTHY",
        "telemetry_source": "live_api",
        "midas": {
            "state": midas_state_machine.get_state().value,
            "validation": midas_state_machine.validate_state_machine(),
            "rate_limiter": midas_rate_limiter.metrics(),
            "backpressure": midas_backpressure_guard.metrics(),
            "requests": mining_request_tracker.get_stats(),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/disconnect", dependencies=[Depends(require_mining_control)])
async def disconnect(
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """Disconnect from the active pool through the canonical MIDAS stop path."""
    global _ACTIVE_CONNECTION

    request_id = _request_id(request)
    parameters = {"active_pool": _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None}
    idem = _idempotency_key(request, idempotency_key, "disconnect", parameters)
    tracked = mining_request_tracker.create_request("disconnect", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result

    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)
    try:
        pool_name = _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None
        if midas_state_machine.get_state() == MiningState.RUNNING:
            midas_state_machine.transition(MiningState.STOPPING, request_id=request_id, reason="operator requested disconnect")
        daemon_status = stop_pythia_daemon()
        _ACTIVE_CONNECTION = None
        state = get_pythia_state() or {}
        state["active_pool"] = None
        state["midas_state"] = "stopped"
        _write_state(state)
        if midas_state_machine.get_state() == MiningState.STOPPING:
            midas_state_machine.transition(MiningState.STOPPED, request_id=request_id, reason="pool disconnected")
        result = {
            "status": "disconnected",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "previous_pool": pool_name,
            "daemon": daemon_status,
            "midas_state": midas_state_machine.get_state().value,
        }
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.COMPLETED, result=result)
        return result
    except StateTransitionError as exc:
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.FAILED, error=str(exc))
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "invalid_midas_transition", "detail": str(exc), "request_id": request_id}) from exc
    finally:
        midas_backpressure_guard.release()


@router.get("/daemon", dependencies=[Depends(require_mining_control)])
async def daemon_status():
    """Read daemon status without starting a new daemon."""
    running = _DAEMON_STARTED and _PYTHIA_PROCESS is not None and _PYTHIA_PROCESS.poll() is None
    return {
        "status": "running" if running else "not_running",
        "pid": _PYTHIA_PROCESS.pid if running and _PYTHIA_PROCESS else None,
        "midas_state": midas_state_machine.get_state().value,
    }


@router.get("/stats", dependencies=[Depends(require_mining_read)])
async def get_stats():
    state = get_pythia_state()
    shares = _share_counts(state)
    quantum = state.get("quantum", {}) if state else {}
    hashrate = state.get("hashrate_ehs") if state else (_ACTIVE_CONNECTION.get("capacity_ehs") if _ACTIVE_CONNECTION else None)
    acceptance_rate = state.get("acceptance_rate") if state else (shares["accepted"] / max(shares["submitted"], 1))
    return {
        "timeframe": "24h",
        "summary": {
            "total_hashrate": hashrate,
            "avg_hashrate": hashrate,
            "peak_hashrate": hashrate,
            "capacity_source": "configured" if hashrate is not None else "not_configured",
            "total_shares": shares["submitted"],
            "accepted_shares": shares["accepted"],
            "rejected_shares": shares["rejected"],
            "acceptance_rate": acceptance_rate,
            "estimated_revenue_btc": None,
            "estimated_revenue_usd": None,
            "power_scale": state.get("power_scale") if state else 1.0,
            "telemetry_source": "live_api",
        },
        "timeseries": [],
        "quantum_performance": {
            "quantum_speedup_avg": None,
            "phi_resonance_avg": quantum.get("phi_phase_alignment") if quantum else None,
            "vqe_iterations_avg": None,
            "consciousness_correlation": None,
            "quantum_metrics": quantum,
        },
        "midas": {
            "state": midas_state_machine.get_state().value,
            "state_machine": midas_state_machine.validate_state_machine(),
            "rate_limiter": midas_rate_limiter.metrics(),
            "backpressure": midas_backpressure_guard.metrics(),
            "requests": mining_request_tracker.get_stats(),
        },
    }


@router.post("/power", dependencies=[Depends(require_mining_control)])
async def set_power_scale(
    data: PowerScaleRequest,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    """Update power scale in the governance config file through MIDAS controls."""
    global _ACTIVE_CONNECTION

    request_id = _request_id(request)
    parameters = {"scale": data.scale}
    idem = _idempotency_key(request, idempotency_key, "power", parameters)
    tracked = mining_request_tracker.create_request("power", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result

    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)
    try:
        if midas_state_machine.get_state() != MiningState.RUNNING:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={"error": "midas_not_running", "state": midas_state_machine.get_state().value})
        config_file = _config_path()
        fd = os.open(config_file + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump({"power_scale": data.scale, "timestamp": datetime.utcnow().isoformat(), "request_id": request_id}, file)
        os.replace(config_file + ".tmp", config_file)
        os.chmod(config_file, 0o600)
        if _ACTIVE_CONNECTION:
            _ACTIVE_CONNECTION["capacity_ehs"] = data.scale
        result = {
            "status": "success",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "requested_scale": data.scale,
            "midas_state": midas_state_machine.get_state().value,
        }
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.COMPLETED, result=result)
        return result
    except HTTPException as exc:
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.FAILED, error=str(exc.detail))
        raise
    except OSError as exc:
        mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.FAILED, error=str(exc))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update power scale: {exc}") from exc
    finally:
        midas_backpressure_guard.release()
