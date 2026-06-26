"""FastAPI entry point for the HYBA Genesis backend."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any, Dict, List

# Support both documented launch forms:
#   uvicorn hyba_genesis_api.main:app --app-dir python_backend
#   python -m uvicorn python_backend.hyba_genesis_api.main:app
# The codebase uses absolute hyba_genesis_api imports, so add the backend
# directory when the module is imported through the python_backend namespace.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

import uvicorn  # noqa: E402
from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import PlainTextResponse, JSONResponse  # noqa: E402
from prometheus_client import CONTENT_TYPE_LATEST  # noqa: E402

from hyba_genesis_api.api import (  # noqa: E402
    admin,
    ai,
    ai_memory,
    agentic_intelligence_service,
    auth,
    computational_intelligence_service,
    customer_access,
    customer_portal,
    executive_router,
    health,
    intelligence,
    metabolic_router,
    millennium_mathematics,
    misc,
    mining,
    mining_jobs,
    mining_ops,
    mining_production,
    observability,
    ops,
    organism_router,
    pool_management,
    products,
    proofs,
    quantum_as_a_service,
    quantum_finance_service,
    quantum_intelligence_service,
    quantum_mathematical_execution,
    regeneration_router,
    salamander_substrate,
    security,
    streaming_sense,
    unified_mining,
    webhooks,
    websocket,
)
from hyba_genesis_api.core.api_posture import (
    install_enterprise_api_posture,
)  # noqa: E402
from hyba_genesis_api.core.recursive_closure import build_buffered_closure  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import (  # noqa: E402
    ReflexiveController,
    default_reflexive_root,
)
from hyba_genesis_api.core.reflexive_daemon import IntelligenceHeartbeat  # noqa: E402
from hyba_genesis_api.core.autonomy_persistence import (
    save_autonomy_report,
)  # noqa: E402
from hyba_genesis_api.core.substrate import (  # noqa: E402
    get_substrate_state,
    initialize_substrate,
    shutdown_substrate,
)
from hyba_genesis_api.core.telemetry import (  # noqa: E402
    get_metrics,
    init_logging,
    init_metrics,
    telemetry_middleware,
    get_prometheus_metrics,
)
from hyba_genesis_api.core.rate_limiter import RateLimiter  # noqa: E402
from hyba_genesis_api.core.feature_flags import get_feature_flags  # noqa: E402
from pythia_mining.distributed_lock_manager import DistributedLockManager  # noqa: E402

# Initialize the database (create tables if necessary)
try:
    from hyba_genesis_api.database import init_db  # type: ignore

    init_db()
except Exception as e:
    logging.warning("Database initialization failed: %s", e)


def _parse_cors_origins() -> List[str]:
    """Read CORS origins from env, falling back to safe localhost defaults.

    Set HYBA_CORS_ORIGINS as a comma-separated list (e.g. https://app.hyba.ai,https://console.hyba.ai).
    Production deployments MUST configure this; localhost defaults are for development only.
    """
    raw = os.getenv("HYBA_CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = [o.strip() for o in raw.split(",") if o.strip()]
    return origins


# Cache CORS origins at module load time — _parse_cors_origins() was previously
# called on every request inside the middleware, re-parsing the env var each time.
_CORS_ORIGINS: List[str] = _parse_cors_origins()
_IS_PRODUCTION: bool = (
    os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower() == "production"
)


def _get_or_init_distributed_lock_manager(app: FastAPI) -> DistributedLockManager:
    """Get existing or initialize DistributedLockManager in app state.

    The lock manager is created once per app startup and stored in app.state.
    Fail-closed behavior:
    - QaaS/CIaaS execution: Redis unavailable -> return 423 Locked, do not proceed
    - Private validation/mining: local fallback is allowed only when explicitly configured
    """
    if hasattr(app.state, "distributed_lock_manager"):
        return app.state.distributed_lock_manager

    from pythia_mining.redis_state_registry import get_redis_registry

    redis_registry = get_redis_registry()
    if not redis_registry.available:
        logging.warning(
            "Redis unavailable for distributed lock manager; "
            "QaaS/CIaaS execution will fail-closed where distributed locking is required"
        )

    lock_manager = DistributedLockManager(
        redis_client=redis_registry.client if redis_registry.available else None,
        max_retry_attempts=10,
    )
    app.state.distributed_lock_manager = lock_manager
    logging.info(
        "DistributedLockManager initialized",
        extra={"redis_available": redis_registry.available},
    )
    return lock_manager


async def _activate_startup_self_healing(app: FastAPI) -> None:
    """Activate PYTHIA self-healing/self-optimising autonomy during backend boot."""
    if os.getenv("HYBA_STARTUP_SELF_HEALING_ENABLED", "true").strip().lower() in {
        "false",
        "0",
        "no",
    }:
        logging.info(
            "HYBA startup self-healing disabled by HYBA_STARTUP_SELF_HEALING_ENABLED"
        )
        return

    from hyba_genesis_api.api.unified_mining import get_engine

    engine = get_engine()
    controller = engine.autonomous_controller
    timeout_seconds = float(
        os.getenv("HYBA_STARTUP_SELF_HEALING_TIMEOUT_SECONDS", "15.0")
    )
    logging.info(
        "HYBA API startup: activating PYTHIA self-healing/self-optimising cycle",
        extra={
            "autonomy_level": controller.current_autonomy_level.value,
            "timeout_seconds": timeout_seconds,
        },
    )
    report = await asyncio.wait_for(
        controller.boot_self_heal_and_optimize(),
        timeout=max(0.1, timeout_seconds),
    )
    app.state.startup_self_healing_report = report
    save_autonomy_report(report, report_type="startup")
    
    # Generate executive startup memo for Evidence Package
    try:
        from hyba_genesis_api.core.startup_memo_generator import StartupMemoGenerator
        substrate_state = get_substrate_state()
        memo_path = StartupMemoGenerator.save_startup_memo(report, substrate_state)
        logging.info(
            "HYBA API startup: Optimization memo generated",
            extra={"memo_path": str(memo_path)}
        )
    except Exception as memo_err:
        logging.warning(
            "HYBA API startup: Failed to generate optimization memo",
            extra={"error": str(memo_err)}
        )
    
    logging.info(
        "HYBA API startup: PYTHIA self-healing/self-optimising cycle complete",
        extra={
            "duration_ms": report.get("duration_ms"),
            "proposals_applied": report.get("reflexive_report", {}).get(
                "proposals_applied"
            ),
            "reflexive_cycle_count": report.get("after", {}).get(
                "reflexive_cycle_count"
            ),
        },
    )


async def _load_memory_seed(app: FastAPI) -> None:
    """Load memory seed to bootstrap system intelligence."""
    import json
    from pathlib import Path

    seed_path = (
        Path(__file__).parent.parent.parent
        / "artifacts"
        / "memory_seed"
        / "memory_seed_v1.json"
    )
    if not seed_path.exists():
        logging.warning("Memory seed not found, system will bootstrap from scratch")
        return

    try:
        with open(seed_path, "r") as f:
            memory_seed = json.load(f)

        app.state.memory_seed = memory_seed
        cs = memory_seed.get("consciousness_state", {})
        meta = memory_seed.get("metadata", {})
        # Seed schema uses average_complexity; phi_integrated is a derived alias.
        app.state.phi_integrated = (
            cs.get("phi_integrated") or cs.get("average_complexity", 0.0)
        )
        app.state.emergent_intelligence_index = meta.get("emergent_intelligence_index", 0.0)

        logging.info(
            "Memory seed loaded successfully",
            extra={
                "phi_integrated": app.state.phi_integrated,
                "emergence_index": app.state.emergent_intelligence_index,
                "knowledge_nodes": meta.get("total_nodes", 0),
            },
        )
    except Exception as e:
        logging.error(f"Failed to load memory seed: {e}")


def validate_required_secrets() -> None:
    """Fail startup when production auth secrets are absent or placeholders."""
    env = os.getenv("NODE_ENV", os.getenv("HYBA_ENV", "development")).lower()
    strict = os.getenv("HYBA_STRICT_SECRET_GUARD", "false").lower() == "true"
    if env != "production" and not strict:
        return
    placeholders = {"change-me", "changeme", "your-secret-here", "development-secret"}
    missing = []
    for name in ("HYBA_API_KEY_SECRET", "JWT_SECRET"):
        value = os.getenv(name, "").strip()
        if not value or value.lower() in placeholders or "example" in value.lower():
            missing.append(name)
    if missing:
        raise RuntimeError(
            "HYBA startup refused: required production secrets missing or placeholder: "
            + ", ".join(missing)
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""

    init_logging()
    validate_required_secrets()
    init_metrics()
    app.state.feature_flags = get_feature_flags()

    # Initialize customer portal database
    from hyba_genesis_api.database import initialize_database

    initialize_database()

    lock_manager = _get_or_init_distributed_lock_manager(app)

    logging.info("HYBA API startup: initializing substrate lifecycle")
    initialize_substrate()
    await _load_memory_seed(app)
    logging.info(
        "HYBA API startup: substrate READY", extra={"substrate": get_substrate_state()}
    )
    # It is not a public product surface; see docs/product/HYBA_PRODUCT_BOUNDARIES.md.
    from hyba_genesis_api.api import unified_mining

    unified_mining.initialize_engine_with_lock_manager(lock_manager)

    try:
        await _activate_startup_self_healing(app)
    except Exception as exc:
        logging.warning(
            "HYBA startup self-healing cycle failed; backend continuing",
            extra={"error": str(exc)},
        )
    heartbeat = None
    heartbeat_task = None
    if os.getenv("HYBA_ENABLE_REFLEXIVE_DAEMON", "false").lower() == "true":
        controller = ReflexiveController(default_reflexive_root())
        closure, _buffer = build_buffered_closure(controller)
        heartbeat = IntelligenceHeartbeat(controller, closure)
        interval = float(os.getenv("HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS", "60"))
        heartbeat_task = asyncio.create_task(heartbeat.pulse(interval_seconds=interval))
        logging.info(
            "HYBA reflexive heartbeat enabled", extra={"interval_seconds": interval}
        )
    try:
        yield
    finally:
        if heartbeat is not None:
            heartbeat.stop()
        if heartbeat_task is not None:
            heartbeat_task.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat_task
    logging.info("HYBA API shutdown: draining substrate lifecycle")
    shutdown_substrate()


app = FastAPI(
    title="HYBA Intelligence Platform API",
    version="2.2.0",
    description=(
        "Operational API for HYBA QaaS, QIaaS, CIaaS, quantum finance, PULVINI memory, "
        "Salamander regeneration, evidence governance, and private validation workflows."
    ),
    lifespan=lifespan,
)

# CORS: configurable via HYBA_CORS_ORIGINS env var (comma-separated)
if (
    _CORS_ORIGINS
    and "*" in _CORS_ORIGINS
    and os.getenv("HYBA_CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
):
    logging.warning(
        "CORS is configured with * origins while allow_credentials=True. "
        "This is insecure and will be rejected by browsers. "
        "Set HYBA_CORS_ORIGINS to explicit origins in production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Correlation-ID",
        "Idempotency-Key",
        "X-API-Key",
    ],
)

_rate_limit = int(os.getenv("HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE", "120"))
_rate_window = int(os.getenv("HYBA_RATE_LIMIT_WINDOW_SECONDS", "60"))
app.add_middleware(RateLimiter, max_requests=_rate_limit, window_seconds=_rate_window)

app.middleware("http")(telemetry_middleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unhandled exceptions.

    Returns a structured JSON error with the request-id and a stable error_id
    so operators can correlate logs. Never leaks a Python traceback to the
    client.
    """
    import traceback
    import uuid

    request_id = getattr(getattr(request, "state", None), "request_id", None) or ""
    error_id = f"err_{uuid.uuid4().hex[:16]}"
    logging.exception(
        "Unhandled exception in request handler",
        extra={
            "error_id": error_id,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Reference the error_id in operator logs.",
            "error_id": error_id,
            "request_id": request_id,
            "retryable": False,
        },
        headers={"x-request-id": request_id, "x-error-id": error_id},
    )


@app.middleware("http")
async def enforce_cors_origin_allowlist(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and (request.url.path.startswith("/api/") or request.url.path == "/api"):
        # Use the module-level cached list — avoids env-var re-parse on every request.
        if _IS_PRODUCTION and "*" in _CORS_ORIGINS:
            return JSONResponse(
                status_code=403,
                content={"detail": "Wildcard CORS origin is not allowed in production"},
            )
        if origin not in _CORS_ORIGINS:
            return JSONResponse(
                status_code=403, content={"detail": "CORS origin is not allowed"}
            )
    return await call_next(request)


install_enterprise_api_posture(app)

# Include routers
app.include_router(health.router)
app.include_router(intelligence.router)
app.include_router(mining.router)
app.include_router(mining_jobs.router)
app.include_router(mining_ops.router)
app.include_router(mining_production.router)
app.include_router(security.router)
app.include_router(misc.router)
app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(customer_access.admin_router)
app.include_router(customer_portal.router)
app.include_router(computational_intelligence_service.router)
app.include_router(computational_intelligence_service.public_router)
app.include_router(quantum_as_a_service.router)
app.include_router(quantum_as_a_service.public_router)
app.include_router(quantum_mathematical_execution.router)
app.include_router(quantum_finance_service.router)
app.include_router(millennium_mathematics.router)
app.include_router(millennium_mathematics.public_router)
app.include_router(observability.router)
app.include_router(products.router)
app.include_router(proofs.router)
app.include_router(unified_mining.router)
app.include_router(ai_memory.router)
app.include_router(pool_management.router)
app.include_router(regeneration_router.router)
app.include_router(streaming_sense.router)
app.include_router(metabolic_router.router)
app.include_router(organism_router.router)
app.include_router(executive_router.router)
app.include_router(ops.router)
app.include_router(quantum_intelligence_service.router)
app.include_router(salamander_substrate.router)
app.include_router(agentic_intelligence_service.router)
app.include_router(webhooks.router)
app.include_router(webhooks.api_router)
app.include_router(websocket.router)


@app.get("/health", response_model=Dict[str, Any], tags=["health"])
async def root_health_check():
    """Compatibility health endpoint used by end-to-end smoke tests."""

    return {
        "status": "ok",
        "substrate": get_substrate_state(),
        "telemetry": get_metrics(),
    }


@app.get("/metrics", include_in_schema=False)
async def metrics_endpoint():
    """Expose Prometheus metrics for scraping."""
    return PlainTextResponse(
        get_prometheus_metrics(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/api/substrate", response_model=Dict[str, Any], tags=["substrate"])
async def get_substrate_status():
    """Return the full substrate readiness and initialization order."""

    return get_substrate_state()


if __name__ == "__main__":
    host = os.getenv("HYBA_BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("HYBA_BACKEND_PORT", os.getenv("PORT", "3001")))
    logging.info("Starting HYBA API on %s:%s", host, port)
    uvicorn.run(app, host=host, port=port)
