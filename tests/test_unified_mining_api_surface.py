from __future__ import annotations

import pytest

from hyba_genesis_api.api import unified_mining
from hyba_genesis_api.api.unified_mining import (
    BatchResonanceRequest,
    ShareResultRequest,
    analyze_batch_resonance,
    get_ai_metrics,
    get_unified_status,
    report_share_result,
    unified_health,
)


def setup_function() -> None:
    unified_mining._engine = None


@pytest.mark.asyncio
async def test_unified_status_uses_canonical_engine_state() -> None:
    status = await get_unified_status()

    assert status.engine == "PYTHIA/PULVINI Unified Mining Engine"
    assert status.telemetry_source == "canonical_unified_engine_state"
    assert status.verifier_backend
    assert status.accepted_shares == 0
    assert status.rejected_shares == 0
    assert 0.0 <= status.consciousness_coherence <= 1.0


@pytest.mark.asyncio
async def test_unified_resonance_analysis_uses_hendrix_primitives() -> None:
    response = await analyze_batch_resonance(
        BatchResonanceRequest(nonces=[0, 1, 987654321, 2**32 + 7])
    )

    assert response.telemetry_source == "hendrix_phi_solver_primitives"
    assert response.count == 4
    assert 0.0 <= response.mean_phi_resonance <= 1.0
    assert 0.0 <= response.mass_gate_pass_rate <= 1.0
    assert {item.voronoi_domain for item in response.analysis} <= set(range(32))
    assert all(0.0 <= item.phi_resonance_strength <= 1.0 for item in response.analysis)


@pytest.mark.asyncio
async def test_unified_share_feedback_updates_engine_without_faking_acceptance() -> None:
    rejected = await report_share_result(
        ShareResultRequest(
            nonce=123,
            accepted=False,
            job_id="unit-job",
            phi_resonance_score=0.2,
            error_code=23,
            error_msg="low difficulty share",
        ),
        _payload=None,  # direct unit call; route dependency is tested by FastAPI wiring
    )
    assert rejected["accepted"] is False
    assert rejected["accepted_shares"] == 0
    assert rejected["rejected_shares"] == 1

    accepted = await report_share_result(
        ShareResultRequest(
            nonce=456,
            accepted=True,
            job_id="unit-job",
            phi_resonance_score=0.9,
        ),
        _payload=None,
    )
    assert accepted["accepted"] is True
    assert accepted["accepted_shares"] == 1
    assert accepted["rejected_shares"] == 1

    metrics = await get_ai_metrics()
    assert metrics.telemetry_source == "canonical_unified_engine_state"
    assert metrics.accepted_shares == 1
    assert metrics.rejected_shares == 1
    assert metrics.meta_learning_event_present is True


@pytest.mark.asyncio
async def test_unified_health_reports_measured_engine_surface() -> None:
    health = await unified_health()

    assert health["status"] == "healthy"
    assert health["engine"] == "PYTHIA/PULVINI Unified Mining Engine"
    assert health["telemetry_source"] == "canonical_unified_engine_state"
    assert health["verifier_backend"]
