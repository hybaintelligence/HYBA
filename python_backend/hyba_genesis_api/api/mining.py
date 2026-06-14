"""HYBA Mining API — regulated PYTHIA/MIDAS mining control boundary."""

from __future__ import annotations

import json
import logging
import math
import os
import subprocess
import sys
from datetime import datetime, timezone
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
from pythia_mining.pool_profiles import (
    DEFAULT_POOL_SPECS,
    PoolCredentialConfig,
    PoolProfileError,
    load_runtime_pool_configs,
    save_runtime_pool_config,
    validate_pool_config,
)

router = APIRouter(prefix="/api/mining", tags=["mining"])
LOGGER = logging.getLogger(__name__)

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
PULVINI_HASHRATE_CAP_EHS = 1.0
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_TIERS = (7, 10, 12, 15, 18, 20, 31, 76)
DEFAULT_PHI_TIER = 12


def _phi_tier_composition(phi_tier: int = DEFAULT_PHI_TIER) -> Dict[str, Any]:
    exponent = int(phi_tier)
    phi_multiplier = PHI**exponent
    scale_factor = (10**exponent) * phi_multiplier
    return {
        "label": f"10^{exponent}",
        "phi_exponent": exponent,
        "phi_multiplier": phi_multiplier,
        "scale_factor": scale_factor,
        "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
        "memory_compression_contract": "pulvini_phi_compressed_pre_search",
        "frontend_scaling_enabled": True,
    }


class PowerScaleRequest(BaseModel):
    scale: float = Field(default=1.0, ge=0.1, le=10.0)
    phi_tier: int = Field(
        default=DEFAULT_PHI_TIER,
        description="Dynamic φ tier exponent for memory-compression scaling metadata",
    )

    @validator("phi_tier")
    def validate_phi_tier(cls, value: int) -> int:
        if int(value) not in PHI_TIERS:
            raise ValueError(f"phi_tier must be one of: {PHI_TIERS}")
        return int(value)


class PoolCredentialRequest(BaseModel):
    pool_id: str = Field(..., description="viabtc, braiins, ckpool, or nicehash")
    url: str | None = None
    username: str | None = None
    password: str | None = None
    btc_address: str | None = None
    worker: str | None = None
    nicehash_pool_id: str | None = None
    priority: int | None = Field(default=None, ge=0)
    enabled: bool = True

    @validator("pool_id")
    def validate_pool(cls, value: str) -> str:
        pool_id = value.lower()
        if pool_id not in DEFAULT_POOL_SPECS:
            raise ValueError(f"pool_id must be one of: {', '.join(sorted(DEFAULT_POOL_SPECS))}")
        return pool_id

    @validator("username", "worker", "nicehash_pool_id")
    def validate_plain_identifier(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if len(value) > 128:
            raise ValueError("identifier must be 128 characters or fewer")
        if not all(char.isalnum() or char in "._-" for char in value):
            raise ValueError(
                "identifier can only contain alphanumeric characters, dots, underscores, and hyphens"
            )
        return value

    @validator("btc_address")
    def validate_btc_address(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if len(value) < 26 or len(value) > 90:
            raise ValueError("BTC address length is invalid")
        if not all(char.isalnum() for char in value):
            raise ValueError("BTC address must be alphanumeric")
        return value


class ConnectRequest(BaseModel):
    pool_id: str = Field(..., description="Pool identifier (viabtc, braiins, ckpool, nicehash)")
    worker: Optional[str] = Field(None, description="Legacy worker/username override")
    password: Optional[str] = Field(None, description="Legacy password override")
    username: Optional[str] = None
    btc_address: Optional[str] = None
    nicehash_pool_id: Optional[str] = None
    url: Optional[str] = None
    capacity_ehs: float = Field(
        default=1.0,
        ge=0.01,
        le=PULVINI_HASHRATE_CAP_EHS,
        description="Capacity in EH/s; hard-capped at 1 EH/s",
    )
    switch: bool = Field(
        default=True,
        description="Disconnect active pool before connecting selected pool",
    )

    @validator("pool_id")
    def validate_pool(cls, value: str) -> str:
        pool_id = value.lower()
        if pool_id not in DEFAULT_POOL_SPECS:
            raise ValueError(f"pool_id must be one of: {', '.join(sorted(DEFAULT_POOL_SPECS))}")
        return pool_id


class SubmitJobRequest(BaseModel):
    pool_id: str = Field(...)
    worker: str = Field(...)
    job_id: str = Field(..., description="Job identifier from pool")
    nonce: str = Field(..., description="Mining nonce (hex)")
    hashrate_ehs: float = Field(default=0.0, ge=0.0, le=PULVINI_HASHRATE_CAP_EHS)
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


async def require_mining_control(
    payload: TokenPayload = Depends(get_token_payload),
) -> TokenPayload:
    if not any(role in MINING_CONTROL_ROLES for role in payload.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Mining control requires one of: {', '.join(sorted(MINING_CONTROL_ROLES))}",
        )
    return payload


async def require_mining_read(
    payload: TokenPayload = Depends(get_token_payload),
) -> TokenPayload:
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


def _idempotency_key(
    request: Request,
    explicit: str | None,
    operation_type: str,
    parameters: dict[str, Any],
) -> str:
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=exc.to_response_body(),
        ) from exc


def _capped_hashrate_ehs(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hashrate_ehs must be numeric",
        ) from exc
    if not math.isfinite(parsed) or parsed < 0.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="hashrate_ehs must be finite and non-negative",
        )
    return float(min(parsed, PULVINI_HASHRATE_CAP_EHS))


def _effective_hashrate_ehs(base_capacity_ehs: Any, power_scale: Any = 1.0) -> Optional[float]:
    base = _capped_hashrate_ehs(base_capacity_ehs)
    if base is None:
        return None
    try:
        scale = float(power_scale)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="power_scale must be numeric",
        ) from exc
    if not math.isfinite(scale) or scale <= 0.0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="power_scale must be finite and positive",
        )
    return float(min(base * scale, PULVINI_HASHRATE_CAP_EHS))


def _backend_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _state_path() -> str:
    return os.path.join(_backend_root(), "pythia_state.json")


def _config_path() -> str:
    return os.path.join(_backend_root(), "mining_config.json")


def get_pythia_state() -> Optional[Dict[str, Any]]:
    """Read the PYTHIA state file, failing loudly on corrupt or unreadable state."""

    path = _state_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as file:
            state = json.load(file)
    except OSError as exc:
        LOGGER.exception("Failed to read PYTHIA state file", extra={"path": path})
        raise RuntimeError(f"Failed to read PYTHIA state file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        LOGGER.exception("PYTHIA state file is invalid JSON", extra={"path": path})
        raise RuntimeError(
            f"PYTHIA state file {path} is invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(state, dict):
        raise RuntimeError(
            f"PYTHIA state file {path} must contain a JSON object, got {type(state).__name__}"
        )
    return state


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
        cleanup_error = None
        if os.path.exists(temp):
            try:
                os.unlink(temp)
            except OSError as unlink_exc:
                cleanup_error = unlink_exc
                LOGGER.exception(
                    "Failed to remove temporary PYTHIA state file", extra={"path": temp}
                )
        detail = f"Failed to write state file {path}: {exc}"
        if cleanup_error is not None:
            detail = (
                f"{detail}; additionally failed to remove temporary file {temp}: {cleanup_error}"
            )
        raise RuntimeError(detail) from exc


def _share_counts(state: Optional[Dict[str, Any]]) -> Dict[str, int]:
    if not state:
        return {
            "submitted": _JOBS_SUBMITTED,
            "accepted": _SHARES_ACCEPTED,
            "rejected": _SHARES_REJECTED,
        }
    submitted = int(state.get("total_shares") or _JOBS_SUBMITTED)
    accepted = int(state.get("accepted_shares") or _SHARES_ACCEPTED)
    rejected = int(state.get("rejected_shares") or max(submitted - accepted, 0))
    return {"submitted": submitted, "accepted": accepted, "rejected": rejected}


def _redacted_connection(
    connection: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if connection is None:
        return None
    redacted = dict(connection)
    redacted.pop("password", None)
    redacted.pop("secret", None)
    return redacted


def _pool_config_response(
    config: PoolCredentialConfig, active_pool_id: Optional[str]
) -> Dict[str, Any]:
    spec = DEFAULT_POOL_SPECS[config.pool_id]
    payload = config.to_dict(include_secret_fields=False)
    payload["required_fields"] = spec["required_fields"]
    payload["is_active"] = active_pool_id == config.pool_id
    payload["status"] = (
        "connected"
        if active_pool_id == config.pool_id
        else "configured" if payload.get("configured") else "not_configured"
    )
    return payload


def _build_pool_config_from_request(req: PoolCredentialRequest) -> PoolCredentialConfig:
    base = load_runtime_pool_configs().get(req.pool_id)
    if base is None:
        base = PoolCredentialConfig(
            **DEFAULT_POOL_SPECS[req.pool_id], pool_id=req.pool_id
        )  # type: ignore[arg-type]
    return PoolCredentialConfig(
        pool_id=req.pool_id,
        name=base.name,
        url=req.url or base.url,
        stratum_version=base.stratum_version,
        tls_required=base.tls_required,
        credential_mode=base.credential_mode,
        username=req.username or "",
        password=req.password or "",
        btc_address=req.btc_address or "",
        worker=req.worker or "",
        nicehash_pool_id=req.nicehash_pool_id or "",
        priority=req.priority if req.priority is not None else base.priority,
        enabled=req.enabled,
        source="runtime",
    )


def _resolve_connect_config(req: ConnectRequest) -> PoolCredentialConfig:
    configs = load_runtime_pool_configs()
    config = configs[req.pool_id]
    if any(
        [
            req.worker,
            req.password,
            req.username,
            req.btc_address,
            req.nicehash_pool_id,
            req.url,
        ]
    ):
        config = PoolCredentialConfig(
            pool_id=req.pool_id,
            name=config.name,
            url=req.url or config.url,
            stratum_version=config.stratum_version,
            tls_required=config.tls_required,
            credential_mode=config.credential_mode,
            username=req.username
            or (req.worker if req.pool_id in {"viabtc", "braiins"} else "")
            or config.username,
            password=req.password or config.password,
            btc_address=req.btc_address
            or (req.worker if req.pool_id == "ckpool" else "")
            or config.btc_address,
            worker=req.worker if req.pool_id == "nicehash" else config.worker,
            nicehash_pool_id=req.nicehash_pool_id or config.nicehash_pool_id,
            priority=config.priority,
            enabled=True,
            source="request",
        )
        validate_pool_config(config)
        save_runtime_pool_config(config)
    return validate_pool_config(config)


def start_pythia_daemon(capacity_ehs: Optional[float] = None) -> Dict[str, Any]:
    global _PYTHIA_PROCESS, _DAEMON_STARTED
    if _DAEMON_STARTED and _PYTHIA_PROCESS and _PYTHIA_PROCESS.poll() is None:
        return {"status": "already_running", "pid": _PYTHIA_PROCESS.pid}
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", _backend_root())
    capped_capacity = _capped_hashrate_ehs(capacity_ehs)
    if capped_capacity is not None:
        env["HYBA_QUANTUM_CAPACITY_EHS"] = str(capped_capacity)
        env["HYBA_PULVINI_HASHRATE_CAP_EHS"] = str(PULVINI_HASHRATE_CAP_EHS)
    try:
        _PYTHIA_PROCESS = subprocess.Popen(
            [sys.executable, "-m", "pythia_mining.main"],
            cwd=os.path.dirname(_backend_root()),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _DAEMON_STARTED = True
        return {
            "status": "started",
            "pid": _PYTHIA_PROCESS.pid,
            "capacity_ehs": capped_capacity,
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
        }
    except (OSError, ValueError) as exc:  # pragma: no cover
        LOGGER.exception("Failed to start PYTHIA daemon")
        raise RuntimeError(f"Failed to start PYTHIA daemon: {exc}") from exc


def stop_pythia_daemon() -> Dict[str, Any]:
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


@router.get("/pool-config", dependencies=[Depends(require_mining_read)])
async def get_pool_config():
    active_pool_id = _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None
    configs = load_runtime_pool_configs()
    return {
        "pools": [_pool_config_response(config, active_pool_id) for config in configs.values()],
        "active_pool_id": active_pool_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/pool-config", dependencies=[Depends(require_mining_control)])
async def configure_pool(
    req: PoolCredentialRequest,
    request: Request,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
):
    request_id = _request_id(request)
    parameters = {"pool_id": req.pool_id, "url": req.url, "enabled": req.enabled}
    idem = _idempotency_key(request, idempotency_key, "pool-config", parameters)
    tracked = mining_request_tracker.create_request("pool-config", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result
    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)
    try:
        config = save_runtime_pool_config(_build_pool_config_from_request(req))
        result = {
            "status": "configured",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "pool": _pool_config_response(
                config,
                _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None,
            ),
        }
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.COMPLETED, result=result
        )
        return result
    except PoolProfileError as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_pool_config",
                "detail": str(exc),
                "request_id": request_id,
            },
        ) from exc
    finally:
        midas_backpressure_guard.release()


@router.get("/pools", dependencies=[Depends(require_mining_read)])
async def get_pools():
    state = get_pythia_state()
    active_pool_id = _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None
    configs = load_runtime_pool_configs()
    pools = []
    shares = _share_counts(state)
    for config in configs.values():
        is_active = active_pool_id == config.pool_id
        pool_payload = _pool_config_response(config, active_pool_id)
        pool_payload.update(
            {
                "pool_id": config.pool_id,
                "name": config.name,
                "url": config.url,
                "stratum_version": config.stratum_version,
                "connection_state": "connected" if is_active else "disconnected",
                "performance": {
                    "latency_ms": None,
                    "shares_submitted": shares["submitted"] if is_active else 0,
                    "shares_accepted": shares["accepted"] if is_active else 0,
                    "shares_rejected": shares["rejected"] if is_active else 0,
                    "acceptance_rate": (
                        shares["accepted"] / max(shares["submitted"], 1) if is_active else 0
                    ),
                },
            }
        )
        pools.append(pool_payload)
    raw_hashrate = (
        state.get("hashrate_ehs")
        if state
        else (_ACTIVE_CONNECTION.get("capacity_ehs") if _ACTIVE_CONNECTION else None)
    )
    total_hashrate = _capped_hashrate_ehs(raw_hashrate)
    return {
        "pools": pools,
        "summary": {
            "total_pools": len(pools),
            "configured_pools": sum(1 for pool in pools if pool.get("configured")),
            "active_pools": sum(1 for pool in pools if pool.get("is_active")),
            "active_pool_name": active_pool_id,
            "total_hashrate": total_hashrate,
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "capacity_source": (
                "configured_capped" if total_hashrate is not None else "not_configured"
            ),
            "global_acceptance_rate": shares["accepted"] / max(shares["submitted"], 1),
            "total_shares_24h": shares["submitted"],
            "estimated_btc_per_day": None,
            "telemetry_source": "live_api",
            "daemon_running": _DAEMON_STARTED
            and _PYTHIA_PROCESS is not None
            and _PYTHIA_PROCESS.poll() is None,
            "midas_state": midas_state_machine.get_state().value,
            "midas_metrics": midas_state_machine.validate_state_machine()["metrics"],
        },
    }


@router.post("/connect", dependencies=[Depends(require_mining_control)])
async def connect_to_pool(
    req: ConnectRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    global _ACTIVE_CONNECTION
    request_id = _request_id(request)
    capacity_ehs = _capped_hashrate_ehs(req.capacity_ehs)
    parameters = {
        "pool_id": req.pool_id,
        "capacity_ehs": capacity_ehs,
        "switch": req.switch,
    }
    idem = _idempotency_key(request, idempotency_key, "connect", parameters)
    tracked = mining_request_tracker.create_request("connect", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result
    if tracked.status == RequestStatus.PROCESSING:
        return {
            "status": "processing",
            "request_id": tracked.request_id,
            "idempotency_key": idem,
        }
    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)
    try:
        config = _resolve_connect_config(req)
        if _ACTIVE_CONNECTION is not None:
            if not req.switch:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "mining_already_connected",
                        "active_connection": _redacted_connection(_ACTIVE_CONNECTION),
                    },
                )
            stop_pythia_daemon()
            _ACTIVE_CONNECTION = None
            if midas_state_machine.get_state() == MiningState.RUNNING:
                midas_state_machine.transition(
                    MiningState.STOPPING,
                    request_id=request_id,
                    reason="operator requested pool switch",
                )
                midas_state_machine.transition(
                    MiningState.STOPPED,
                    request_id=request_id,
                    reason="previous pool stopped before switch",
                )

        current_state = midas_state_machine.get_state()
        if current_state in {MiningState.IDLE, MiningState.STOPPED}:
            midas_state_machine.transition(
                MiningState.STARTING,
                request_id=request_id,
                reason="operator requested pool connection",
                metadata={
                    "pool_id": req.pool_id,
                    "tracked_request_id": tracked.request_id,
                    "capacity_ehs": capacity_ehs,
                    "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
                },
            )
        else:
            raise StateTransitionError(f"Cannot connect from MIDAS state {current_state.value}")

        daemon_status = start_pythia_daemon(capacity_ehs=capacity_ehs)

        profile = config.to_profile()
        _ACTIVE_CONNECTION = {
            "pool_id": config.pool_id,
            "worker": config.resolved_username(),
            "profile": profile.to_dict(include_secret_fields=False),
            "base_capacity_ehs": capacity_ehs,
            "capacity_ehs": capacity_ehs,
            "power_scale": 1.0,
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "credential_mode": config.credential_mode,
        }
        state = get_pythia_state() or {}
        state["active_pool"] = config.pool_id
        state["active_worker"] = config.resolved_username()
        state["base_capacity_ehs"] = capacity_ehs
        state["hashrate_ehs"] = capacity_ehs
        state["hashrate_cap_ehs"] = PULVINI_HASHRATE_CAP_EHS
        state["capacity_source"] = "configured_capped"
        state["power_scale"] = 1.0
        state["telemetry_source"] = "live_api"
        state["system_health"] = "HEALTHY"
        state["midas_state"] = "running"
        _write_state(state)

        midas_state_machine.transition(
            MiningState.RUNNING,
            request_id=request_id,
            reason="pool connection established",
            metadata={
                "pool_id": req.pool_id,
                "tracked_request_id": tracked.request_id,
                "capacity_ehs": capacity_ehs,
                "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            },
        )
        result = {
            "status": "connected",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "pool_id": config.pool_id,
            "pool": config.name,
            "worker": config.resolved_username(),
            "url": config.url,
            "base_capacity_ehs": capacity_ehs,
            "capacity_ehs": capacity_ehs,
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "daemon": daemon_status,
            "midas_state": midas_state_machine.get_state().value,
            "connected_at": _ACTIVE_CONNECTION["connected_at"],
        }
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.COMPLETED, result=result
        )
        return result
    except HTTPException as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc.detail)
        )
        raise
    except (RuntimeError, StateTransitionError, PoolProfileError) as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "mining_connect_failed",
                "detail": str(exc),
                "request_id": request_id,
            },
        ) from exc
    finally:
        midas_backpressure_guard.release()


@router.post("/switch", dependencies=[Depends(require_mining_control)])
async def switch_pool(
    req: ConnectRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    req.switch = True
    return await connect_to_pool(req, request, idempotency_key)


@router.post("/submit")
async def submit_job(
    job: SubmitJobRequest,
    request: Request,
    _payload: TokenPayload = Depends(require_mining_control),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    global _JOBS_SUBMITTED, _SHARES_ACCEPTED, _SHARES_REJECTED
    request_id = _request_id(request)
    parameters = {
        "pool_id": job.pool_id,
        "worker": job.worker,
        "job_id": job.job_id,
        "nonce": job.nonce[:18],
    }
    idem = _idempotency_key(request, idempotency_key, "submit", parameters)
    tracked = mining_request_tracker.create_request("submit", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result
    if tracked.status == RequestStatus.PROCESSING:
        return {
            "status": "processing",
            "request_id": tracked.request_id,
            "idempotency_key": idem,
        }
    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)
    try:
        if _ACTIVE_CONNECTION is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active pool connection. Call /api/mining/connect first.",
            )
        if midas_state_machine.get_state() != MiningState.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "midas_not_running",
                    "state": midas_state_machine.get_state().value,
                },
            )
        if job.pool_id != _ACTIVE_CONNECTION.get("pool_id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pool mismatch. You can only submit shares for the active pool.",
            )
        if job.worker != _ACTIVE_CONNECTION.get("worker"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Worker mismatch. You can only submit shares for the connected worker.",
            )
        _JOBS_SUBMITTED += 1
        try:
            from pythia_mining.mining_validation import (
                MiningValidationError,
                validate_share,
            )
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
                    coinbase_parts=(
                        current_job_data.get("coinbase1", ""),
                        current_job_data.get("coinbase2", ""),
                    ),
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Validation error: {exc}",
            ) from exc
        except ValueError as exc:
            _SHARES_REJECTED += 1
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid nonce format: {exc}",
            ) from exc
        except Exception as exc:
            _SHARES_REJECTED += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Share validation failed: {exc}",
            ) from exc
        state = get_pythia_state() or {}
        state["total_shares"] = _JOBS_SUBMITTED
        state["accepted_shares"] = _SHARES_ACCEPTED
        state["rejected_shares"] = _SHARES_REJECTED
        state["acceptance_rate"] = _SHARES_ACCEPTED / max(_JOBS_SUBMITTED, 1)
        state["hashrate_ehs"] = (
            _capped_hashrate_ehs(job.hashrate_ehs)
            if job.hashrate_ehs > 0
            else _capped_hashrate_ehs(state.get("hashrate_ehs"))
        )
        state["hashrate_cap_ehs"] = PULVINI_HASHRATE_CAP_EHS
        state["capacity_source"] = (
            "configured_capped"
            if state.get("hashrate_ehs") is not None
            else state.get("capacity_source")
        )
        state["last_job"] = {
            "job_id": job.job_id,
            "nonce": job.nonce[:16] + "...",
            "timestamp": datetime.now(timezone.utc).isoformat(),
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
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "total_submitted": _JOBS_SUBMITTED,
            "total_accepted": _SHARES_ACCEPTED,
            "acceptance_rate": _SHARES_ACCEPTED / max(_JOBS_SUBMITTED, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if reason:
            response["rejection_reason"] = reason
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.COMPLETED, result=response
        )
        return response
    except HTTPException as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc.detail)
        )
        raise
    finally:
        midas_backpressure_guard.release()


@router.get("/status", dependencies=[Depends(require_mining_read)])
async def mining_status():
    state = get_pythia_state()
    shares = _share_counts(state)
    raw_hashrate = (
        state.get("hashrate_ehs")
        if state
        else (_ACTIVE_CONNECTION.get("capacity_ehs") if _ACTIVE_CONNECTION else None)
    )
    hashrate = _capped_hashrate_ehs(raw_hashrate)
    return {
        "active": _ACTIVE_CONNECTION is not None,
        "daemon_running": _DAEMON_STARTED
        and _PYTHIA_PROCESS is not None
        and _PYTHIA_PROCESS.poll() is None,
        "connection": _redacted_connection(_ACTIVE_CONNECTION),
        "shares": shares,
        "acceptance_rate": shares["accepted"] / max(shares["submitted"], 1),
        "hashrate_ehs": hashrate,
        "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
        "capacity_source": (state or {}).get(
            "capacity_source",
            "configured_capped" if _ACTIVE_CONNECTION else "not_configured",
        ),
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health", dependencies=[Depends(require_mining_read)])
async def health_check():
    """Comprehensive health check for mining system with detailed status."""
    state = get_pythia_state()
    health_status = {
        "status": "healthy",
        "checks": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Daemon health check
    daemon_running = (
        _DAEMON_STARTED and _PYTHIA_PROCESS is not None and _PYTHIA_PROCESS.poll() is None
    )
    health_status["checks"]["daemon"] = {
        "status": "healthy" if daemon_running else "unhealthy",
        "running": daemon_running,
        "pid": _PYTHIA_PROCESS.pid if _PYTHIA_PROCESS else None,
    }

    # Connection health check
    connection_healthy = _ACTIVE_CONNECTION is not None
    health_status["checks"]["connection"] = {
        "status": "healthy" if connection_healthy else "unhealthy",
        "active": connection_healthy,
        "pool_id": _ACTIVE_CONNECTION.get("pool_id") if _ACTIVE_CONNECTION else None,
    }

    # Activity health check
    last_activity = state.get("last_job", {}).get("timestamp") if state else None
    if last_activity:
        try:
            activity_age = (
                datetime.now(timezone.utc)
                - datetime.fromisoformat(last_activity).replace(tzinfo=timezone.utc)
            ).total_seconds()
            activity_healthy = activity_age < 300  # 5 minutes
            health_status["checks"]["activity"] = {
                "status": "healthy" if activity_healthy else "degraded",
                "last_activity": last_activity,
                "age_seconds": activity_age,
            }
        except (ValueError, TypeError):
            health_status["checks"]["activity"] = {
                "status": "unknown",
                "error": "invalid_timestamp",
            }
    else:
        health_status["checks"]["activity"] = {
            "status": "unknown",
            "last_activity": None,
        }

    # MIDAS state machine health
    midas_validation = midas_state_machine.validate_state_machine()
    midas_healthy = midas_validation["valid"]
    health_status["checks"]["midas"] = {
        "status": "healthy" if midas_healthy else "degraded",
        "state": midas_state_machine.get_state().value,
        "validation": midas_validation,
    }

    # Overall health status
    check_statuses = [check["status"] for check in health_status["checks"].values()]
    if "unhealthy" in check_statuses:
        health_status["status"] = "unhealthy"
    elif "degraded" in check_statuses:
        health_status["status"] = "degraded"

    return health_status


@router.post("/disconnect", dependencies=[Depends(require_mining_control)])
async def disconnect(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
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
            midas_state_machine.transition(
                MiningState.STOPPING,
                request_id=request_id,
                reason="operator requested disconnect",
            )
        daemon_status = stop_pythia_daemon()
        _ACTIVE_CONNECTION = None
        state = get_pythia_state() or {}
        state["active_pool"] = None
        state["active_worker"] = None
        state["midas_state"] = "stopped"
        _write_state(state)
        if midas_state_machine.get_state() == MiningState.STOPPING:
            midas_state_machine.transition(
                MiningState.STOPPED, request_id=request_id, reason="pool disconnected"
            )
        result = {
            "status": "disconnected",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "previous_pool": pool_name,
            "daemon": daemon_status,
            "midas_state": midas_state_machine.get_state().value,
        }
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.COMPLETED, result=result
        )
        return result
    except StateTransitionError as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_midas_transition",
                "detail": str(exc),
                "request_id": request_id,
            },
        ) from exc
    finally:
        midas_backpressure_guard.release()


@router.get("/daemon", dependencies=[Depends(require_mining_control)])
async def daemon_status():
    running = _DAEMON_STARTED and _PYTHIA_PROCESS is not None and _PYTHIA_PROCESS.poll() is None
    return {
        "status": "running" if running else "not_running",
        "pid": _PYTHIA_PROCESS.pid if running and _PYTHIA_PROCESS else None,
        "midas_state": midas_state_machine.get_state().value,
        "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
    }


@router.get("/stats", dependencies=[Depends(require_mining_read)])
async def get_stats():
    state = get_pythia_state()
    shares = _share_counts(state)
    quantum = state.get("quantum", {}) if state else {}
    raw_hashrate = (
        state.get("hashrate_ehs")
        if state
        else (_ACTIVE_CONNECTION.get("capacity_ehs") if _ACTIVE_CONNECTION else None)
    )
    hashrate = _capped_hashrate_ehs(raw_hashrate)
    acceptance_rate = (
        state.get("acceptance_rate")
        if state
        else (shares["accepted"] / max(shares["submitted"], 1))
    )
    return {
        "timeframe": "24h",
        "summary": {
            "total_hashrate": hashrate,
            "avg_hashrate": hashrate,
            "peak_hashrate": hashrate,
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "capacity_source": ("configured_capped" if hashrate is not None else "not_configured"),
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
            "phi_resonance_avg": (quantum.get("phi_phase_alignment") if quantum else None),
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
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
):
    global _ACTIVE_CONNECTION
    request_id = _request_id(request)
    parameters = {"scale": data.scale, "phi_tier": data.phi_tier}
    idem = _idempotency_key(request, idempotency_key, "power", parameters)
    tracked = mining_request_tracker.create_request("power", parameters, idem)
    if tracked.status == RequestStatus.COMPLETED and tracked.result:
        return tracked.result
    _admit_midas_control(request_id)
    mining_request_tracker.update_request_status(tracked.request_id, RequestStatus.PROCESSING)
    try:
        if midas_state_machine.get_state() != MiningState.RUNNING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "midas_not_running",
                    "state": midas_state_machine.get_state().value,
                },
            )
        state = get_pythia_state() or {}
        base_capacity = (
            (_ACTIVE_CONNECTION or {}).get("base_capacity_ehs")
            or state.get("base_capacity_ehs")
            or (_ACTIVE_CONNECTION or {}).get("capacity_ehs")
            or state.get("hashrate_ehs")
        )
        effective_hashrate = _effective_hashrate_ehs(base_capacity, data.scale)
        phi_tier_composition = _phi_tier_composition(data.phi_tier)
        config_file = _config_path()
        fd = os.open(config_file + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "power_scale": data.scale,
                    "phi_tier": data.phi_tier,
                    "phi_tier_composition": phi_tier_composition,
                    "memory_compression_contract": "pulvini_phi_compressed_pre_search",
                    "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": request_id,
                },
                file,
            )
        os.replace(config_file + ".tmp", config_file)
        os.chmod(config_file, 0o600)
        state["power_scale"] = data.scale
        state["phi_tier"] = data.phi_tier
        state["phi_tier_composition"] = phi_tier_composition
        state["memory_compression_contract"] = "pulvini_phi_compressed_pre_search"
        state["hashrate_ehs"] = effective_hashrate
        state["hashrate_cap_ehs"] = PULVINI_HASHRATE_CAP_EHS
        state["capacity_source"] = (
            "configured_capped"
            if effective_hashrate is not None
            else state.get("capacity_source", "not_configured")
        )
        _write_state(state)
        if _ACTIVE_CONNECTION:
            _ACTIVE_CONNECTION["power_scale"] = data.scale
            _ACTIVE_CONNECTION["phi_tier"] = data.phi_tier
            _ACTIVE_CONNECTION["phi_tier_composition"] = phi_tier_composition
            _ACTIVE_CONNECTION["capacity_ehs"] = effective_hashrate
            _ACTIVE_CONNECTION["hashrate_cap_ehs"] = PULVINI_HASHRATE_CAP_EHS
        result = {
            "status": "success",
            "request_id": request_id,
            "tracked_request_id": tracked.request_id,
            "idempotency_key": idem,
            "requested_scale": data.scale,
            "phi_tier": data.phi_tier,
            "phi_tier_composition": phi_tier_composition,
            "effective_hashrate_ehs": effective_hashrate,
            "hashrate_cap_ehs": PULVINI_HASHRATE_CAP_EHS,
            "midas_state": midas_state_machine.get_state().value,
        }
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.COMPLETED, result=result
        )
        return result
    except HTTPException as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc.detail)
        )
        raise
    except OSError as exc:
        mining_request_tracker.update_request_status(
            tracked.request_id, RequestStatus.FAILED, error=str(exc)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update power scale: {exc}",
        ) from exc
    finally:
        midas_backpressure_guard.release()
