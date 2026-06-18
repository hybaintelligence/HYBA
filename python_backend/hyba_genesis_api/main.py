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
from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import PlainTextResponse  # noqa: E402
from prometheus_client import CONTENT_TYPE_LATEST  # noqa: E402

from hyba_genesis_api.api import (  # noqa: E402
    admin,
    ai,
    ai_memory,
    auth,
    health,
    intelligence,
    mining,
    mining_jobs,
    mining_ops,
    mining_production,
    misc,
    pool_management,
    products,
    regeneration_router,
    security,
    streaming_sense,
    unified_mining,
)
from hyba_genesis_api.core.api_posture import install_enterprise_api_posture  # noqa: E402
from hyba_genesis_api.core.recursive_closure import build_buffered_closure  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import (  # noqa: E402
    ReflexiveController,
    default_reflexive_root,
)
from hyba_genesis_api.core.reflexive_daemon import IntelligenceHeartbeat  # noqa: E402
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""

    init_logging()
    init_metrics()
    logging.info("HYBA API startup: initializing substrate lifecycle")
    initialize_substrate()
    logging.info("HYBA API startup: substrate READY", extra={"substrate": get_substrate_state()})
    heartbeat = None
    heartbeat_task = None
    if os.getenv("HYBA_ENABLE_REFLEXIVE_DAEMON", "false").lower() == "true":
        controller = ReflexiveController(default_reflexive_root())
        closure, _buffer = build_buffered_closure(controller)
        heartbeat = IntelligenceHeartbeat(controller, closure)
        interval = float(os.getenv("HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS", "60"))
        heartbeat_task = asyncio.create_task(heartbeat.pulse(interval_seconds=interval))
        logging.info("HYBA reflexive heartbeat enabled", extra={"interval_seconds": interval})
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
    title="HYBA Genesis Platform API",
    version="2.0.1",
    description="Operational API for HYBA Genesis telemetry, substrate readiness, and mining workflows.",
    lifespan=lifespan,
)

# CORS: configurable via HYBA_CORS_ORIGINS env var (comma-separated)
_cors_origins = _parse_cors_origins()
if _cors_origins and "*" in _cors_origins and os.getenv("HYBA_CORS_ALLOW_CREDENTIALS", "true").lower() == "true":
    logging.warning(
        "CORS is configured with * origins while allow_credentials=True. "
        "This is insecure and will be rejected by browsers. "
        "Set HYBA_CORS_ORIGINS to explicit origins in production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Correlation-ID",
        "Idempotency-Key",
    ],
)

# Rate limiting: derived from environment variables or defaults
_rate_limit = int(os.getenv("HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE", "120"))
_rate_window = int(os.getenv("HYBA_RATE_LIMIT_WINDOW_SECONDS", "60"))
app.add_middleware(RateLimiter, max_requests=_rate_limit, window_seconds=_rate_window)

# Telemetry middleware for structured logging and metrics
app.middleware("http")(telemetry_middleware)

# Install enterprise posture middleware
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
app.include_router(products.router)
app.include_router(unified_mining.router)
app.include_router(ai_memory.router)
app.include_router(pool_management.router)
<<<<<<< Updated upstream
app.include_router(regeneration_router.router)
=======
app.include_router(streaming_sense.router)
>>>>>>> Stashed changes


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
