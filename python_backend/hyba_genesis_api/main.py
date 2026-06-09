"""
HYBA Genesis Platform API Server
Production-grade main entrypoint (FastAPI)
"""

import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Routers
from api.health import router as health_router
from api.ai import router as ai_router
from api.mining import router as mining_router
from api.security import router as security_router
from api.misc import router as misc_router

# Substrate initialization hooks
from core.substrate import (
    init_pulvini_runtime,
    init_quantum_path,
    init_mining_engine,
    shutdown_substrate,
)

# Observability
from core.telemetry import init_logging, init_metrics

# ─────────────────────────────────────────────────────────────────────────────
# APP INITIALIZATION
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="HYBA Genesis Platform API",
    description="Enterprise Quantum Mining Platform with Consciousness Integration",
    version="2.0.1"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL EXCEPTION HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception at {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred within the HYBA substrate.",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ─────────────────────────────────────────────────────────────────────────────
# STARTUP / SHUTDOWN EVENTS
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    # Observability first
    init_logging()
    init_metrics()

    logging.info("Starting HYBA Genesis Platform substrate...")

    try:
        # Initialize substrate layers
        init_pulvini_runtime()
        init_quantum_path()
        init_mining_engine()
        logging.info("HYBA substrate initialized successfully.")
    except Exception as e:
        logging.critical(f"FATAL: Substrate initialization failed: {e}")
        # In a real production environment, we might want to exit here
        # but for this environment we'll log it and let FastAPI try to run.

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutting down HYBA substrate...")
    shutdown_substrate()
    logging.info("Shutdown complete.")

# ─────────────────────────────────────────────────────────────────────────────
# ROUTERS
# ─────────────────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(ai_router)
app.include_router(mining_router)
app.include_router(security_router)
app.include_router(misc_router)

# ─────────────────────────────────────────────────────────────────────────────
# ROOT ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "HYBA Genesis Platform API",
        "version": "2.0.1",
        "timestamp": datetime.utcnow().isoformat(),
        "architecture": "Self-Healing/Self-Optimising Substrate"
    }
