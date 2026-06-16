from __future__ import annotations

from fastapi.testclient import TestClient
from fastapi import FastAPI
import pytest

from python_backend.hyba_genesis_api.api.ai import router
from python_backend.pythia_mining.genesis_ai_service import GenesisAIServiceRegistry


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def test_get_consciousness_status_not_measured(monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app()
    client = TestClient(app)
    # Force service registry to report no instance
    monkeypatch.setattr(
        GenesisAIServiceRegistry,
        "is_registered",
        classmethod(lambda cls: False),
        raising=False,
    )
    response = client.get("/api/ai/consciousness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "not_measured"
    assert data["consciousness_level"] is None
    assert data["phi_resonance"] is None
    assert data["recent_insights"] == []


def test_get_consciousness_status_measured(monkeypatch: pytest.MonkeyPatch) -> None:
    app = create_app()
    client = TestClient(app)
    # Simulate registered service with deterministic metrics
    monkeypatch.setattr(
        GenesisAIServiceRegistry,
        "is_registered",
        classmethod(lambda cls: True),
        raising=False,
    )
    monkeypatch.setattr(
        GenesisAIServiceRegistry,
        "get_consciousness_metrics",
        classmethod(
            lambda cls: {
                "confidence": 0.7,
                "phi_resonance_score": 0.8,
                "phi_features": {"phi_integrated": 0.6},
                "phi_scaling_mode": "adaptive",
                "phi_scaling": 1.2,
                "knowledge_accuracy": 0.5,
                "strategy_used": "test",
            }
        ),
        raising=False,
    )
    monkeypatch.setattr(
        GenesisAIServiceRegistry,
        "get_performance_metrics",
        classmethod(lambda cls: {"jobs_processed": 1}),
        raising=False,
    )
    monkeypatch.setattr(
        GenesisAIServiceRegistry,
        "get_health_status",
        classmethod(lambda cls: {"overall_status": "healthy"}),
        raising=False,
    )

    response = client.get("/api/ai/consciousness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "measured"
    assert data["consciousness_level"] == 0.7
    assert data["phi_resonance"] == 0.8
    assert data["integrated_information"] == 0.6
    assert data["performance_metrics"]["jobs_processed"] == 1
    assert data["health_status"]["overall_status"] == "healthy"


def test_stimulate_consciousness_degraded() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/ai/consciousness/stimulate",
        json={"intensity": 0.5, "duration_seconds": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted_degraded"
    assert data["source"] == "ai_runtime_not_connected"


def test_chat_endpoint_not_implemented() -> None:
    app = create_app()
    client = TestClient(app)
    response = client.post(
        "/api/ai/chat",
        json={"message": "hello", "history": []},
    )
    assert response.status_code == 501
    data = response.json()
    assert data["detail"]["error"] == "ai_runtime_not_connected"
