"""FastAPI entry point for the HYBA Genesis backend."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hyba_genesis_api.api import ai, health, mining, misc, security
from hyba_genesis_api.core.substrate import (
    get_substrate_state,
    initialize_substrate,
    shutdown_substrate,
)
from hyba_genesis_api.core.telemetry import (
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
    yield
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
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(telemetry_middleware)

app.include_router(health.router)
app.include_router(mining.router)
app.include_router(security.router)
app.include_router(misc.router)
app.include_router(ai.router)


@app.get("/health", response_model=Dict[str, Any], tags=["health"])
async def root_health_check():
    """Compatibility health endpoint used by end-to-end smoke tests."""

    return {"status": "ok", "substrate": get_substrate_state(), "telemetry": get_metrics()}


@app.get("/api/substrate", response_model=Dict[str, Any], tags=["substrate"])
async def get_substrate_status():
    """Return the full substrate readiness and initialization order."""

    return get_substrate_state()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
