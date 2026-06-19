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


@pytest.mark.asyncio
async def test_unified_blockchain_analysis_is_deterministic_and_bounded() -> None:
    req = unified_mining.BlockchainAnalysisRequest(
        chain="bitcoin",
        blocks=[
            unified_mining.BlockchainBlock(height=840000, block_hash="00" * 32),
            unified_mining.BlockchainBlock(height=840001, block_hash="11" * 32),
        ],
    )

    first = await unified_mining.analyze_blockchain(req)
    second = await unified_mining.analyze_blockchain(req)

    assert first["telemetry_source"] == "operator_supplied_blockchain_snapshot"
    assert first["snapshot_hash"] == second["snapshot_hash"]
    assert first["block_count"] == 2
    assert 0.0 <= first["mean_phi_resonance"] <= 1.0
    assert 0.0 <= first["mass_gate_pass_rate"] <= 1.0
    assert all(0 <= item["voronoi_domain"] < 32 for item in first["analysis"])


@pytest.mark.asyncio
async def test_it_from_bit_parser_is_claim_bounded_and_deterministic() -> None:
    req = unified_mining.ItFromBitRequest(bits="01001101", word_size=4)

    response = await unified_mining.analyze_it_from_bit(req)

    assert response["telemetry_source"] == "deterministic_information_parser"
    assert "not as an ontological or physical proof" in response["claim_boundary"]
    assert response["word_count"] == 2
    assert response["words"] == ["0100", "1101"]
    assert response["ones"] == 4
    assert response["zeros"] == 4
    assert response["digest"] == unified_mining.hashlib.sha256(b"01001101").hexdigest()


from hypothesis import given, strategies as st


@given(st.lists(st.integers(min_value=0, max_value=2**40), min_size=1, max_size=25))
def test_resonance_request_property_accepts_bounded_nonce_lists(nonces: list[int]) -> None:
    req = BatchResonanceRequest(nonces=nonces)
    assert len(req.nonces) == len(nonces)
    assert all(isinstance(nonce, int) for nonce in req.nonces)


@given(st.text(alphabet="01", min_size=1, max_size=256), st.integers(min_value=1, max_value=32))
def test_it_from_bit_request_property_preserves_binary_payload(bits: str, word_size: int) -> None:
    req = unified_mining.ItFromBitRequest(bits=bits, word_size=word_size)
    assert req.bits == bits
    assert 1 <= req.word_size <= 32
