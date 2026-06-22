"""Enterprise API contract tests for the Salamander substrate surface."""

import pytest

fastapi = pytest.importorskip("fastapi")
testclient = pytest.importorskip("fastapi.testclient")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from hyba_genesis_api.api.salamander_substrate import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_metabolism_status_does_not_fabricate_live_telemetry():
    response = _client().get("/api/v1/salamander/metabolism/status")

    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "salamander.substrate.enterprise.v1"
    assert body["verdict"] == "TELEMETRY_ADAPTER_REQUIRED"
    assert body["data"]["status"] == "NO_LIVE_TELEMETRY"
    assert body["evidence"]["fabricated_values"] is False


def test_dream_simulate_returns_enterprise_traceable_verdict():
    response = _client().post(
        "/api/v1/salamander/dream/simulate",
        json={
            "baseline_gene": "phi_ratio",
            "baseline_value": 1.60,
            "mutated_value": 1.618033988749895,
            "min_value": 1.0,
            "max_value": 2.0,
            "promotion_threshold": 0.001,
            "baseline_evidence": [
                {
                    "event": "capability_observed",
                    "actor": "enterprise",
                    "timestamp": 1.0,
                    "data": {"roi": 0.2},
                }
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "PROMOTABLE"
    assert body["trace_id"].startswith("DRM-SIM-")
    assert body["data"]["improvement_detected"] > 0
    assert body["evidence"]["audit_event"]["event"] == "dream_mutation_replayed"


def test_regeneration_jump_is_plan_only_and_operator_gated():
    response = _client().post(
        "/api/v1/salamander/regenerate/jump",
        json={
            "target_node": "tokyo-node-04",
            "target_language": "rust",
            "manifest_digest": "abc123def456abc123def456abc123de",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "PLAN_READY"
    assert body["evidence"]["operator_approval_required"] is True
    assert body["evidence"]["automatic_execution"] is False


def test_audit_verdict_surfaces_invariant_results():
    response = _client().post(
        "/api/v1/salamander/audit/verdict",
        json={
            "evidence": [
                {
                    "event": "capability_observed",
                    "actor": "auditor",
                    "timestamp": 1.0,
                    "data": {"roi": 0.1},
                }
            ],
            "metabolic_metrics": {
                "work_performed": 10.0,
                "energy_input_joules": 10.0,
                "thermodynamic_efficiency": 1.0,
                "max_work_per_joule": 1.0,
            },
            "phi_value": 1.618033988749895,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "PASS"
    assert body["data"]["evidence_fidelity"]["passed"] is True
    assert body["data"]["metabolic_conservation"]["passed"] is True
    assert body["data"]["phi_resonance_bounds"]["passed"] is True
