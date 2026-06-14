"""FastAPI entry point for the HYBA Genesis backend."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from typing import Any, Dict

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

from hyba_genesis_api.api import (  # noqa: E402
    ai,
    auth,
    health,
    intelligence,
    mining,
    mining_jobs,
    mining_ops,
    misc,
    products,
    security,
)
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
)


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
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
app.middleware("http")(telemetry_middleware)

app.include_router(health.router)
app.include_router(intelligence.router)
app.include_router(mining.router)
app.include_router(mining_jobs.router)
app.include_router(mining_ops.router)
app.include_router(security.router)
app.include_router(misc.router)
app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(products.router)


@app.get("/health", response_model=Dict[str, Any], tags=["health"])
async def root_health_check():
    """Compatibility health endpoint used by end-to-end smoke tests."""

    return {
        "status": "ok",
        "substrate": get_substrate_state(),
        "telemetry": get_metrics(),
    }


@app.get("/api/substrate", response_model=Dict[str, Any], tags=["substrate"])
async def get_substrate_status():
    """Return the full substrate readiness and initialization order."""

    return get_substrate_state()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
