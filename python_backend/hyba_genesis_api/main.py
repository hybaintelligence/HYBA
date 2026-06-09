"""
HYBA Genesis Platform API Server
Main application entry point (FastAPI framework replica)
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from api.health import router as health_router
from api.ai import router as ai_router

app = FastAPI(
    title="HYBA Genesis Platform API",
    description="Enterprise Quantum Mining Platform with Consciousness Integration",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

app.include_router(health_router)
app.include_router(ai_router)

@app.get("/")
async def root():
    return {
        "message": "HYBA Genesis Platform API [FastAPI Interface]",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
