from __future__ import annotations

import pytest

from pythia_mining.ai_optimizer import OptimizationResult
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.stratum_client import MiningJob


def _job() -> MiningJob:
    return MiningJob(
        job_id="unit-job",
        prevhash="00" * 32,
        coinbase_parts=("", ""),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="5f5e1000",
        target=2**240,
        extranonce1="abcd",
        extranonce2_size=4,
    )


async def _fake_optimise(job: MiningJob) -> OptimizationResult:
    return OptimizationResult(
        nonce=None,
        search_time=0.001,
        quantum_used=True,
        confidence=0.8,
        phi_resonance_score=0.7,
        strategy_used="phi_scaled_compressed_solver_search",
        search_space_size=2**32,
    )


@pytest.mark.asyncio
async def test_unified_engine_starts_as_one_powerhouse_stack() -> None:
    engine = UnifiedMiningEngine()
    engine.optimizer.optimize_nonce_search = _fake_optimise  # type: ignore[method-assign]

    result = await engine.search(_job())
    state = engine.get_unified_state()

    assert result.strategy_used == "phi_scaled_compressed_solver_search"
    assert state["engine"] == "PYTHIA/PULVINI Unified Mining Engine"
    assert state["m32_domains"] == 32
    assert state["state"]["m32_domains_covered"] == 32
    assert state["state"]["solve_count"] == 1
    assert state["state"]["effective_search_dim_bits"] < 23.0
    assert state["proofs"]["phi_folding_lossless"] is True
    assert state["proofs"]["grover_structured_advantage"] >= 35.5
    assert engine.optimizer.current_strategy.phi_resonance_enabled is True
    assert engine.optimizer.current_strategy.adaptive_difficulty is True
    assert engine.optimizer.current_strategy.max_search_time == 30.0


@pytest.mark.asyncio
async def test_rejected_share_drives_conservative_regime_without_faking_acceptance() -> None:
    engine = UnifiedMiningEngine()
    engine.optimizer.optimize_nonce_search = _fake_optimise  # type: ignore[method-assign]

    await engine.on_share_result(
        {
            "job_id": "unit-job",
            "nonce": 123,
            "strategy_used": "phi_scaled_compressed_solver_search",
            "phi_resonance_score": 0.2,
            "error_code": 23,
            "error_msg": "low difficulty share",
        },
        accepted=False,
    )

    await engine.search(_job())
    state = engine.get_unified_state()

    assert state["state"]["accepted_shares"] == 0
    assert state["state"]["rejected_shares"] == 1
    assert engine.optimizer.current_strategy.phi_resonance_enabled is True
    assert engine.optimizer.current_strategy.adaptive_difficulty is False
    assert engine.optimizer.current_strategy.max_search_time == 120.0
    assert state["state"]["autonomic_event"]["action"] == "reduced_search_aggressiveness"
    assert state["consciousness"]["integration_regime"] in {"critical", "fragmented"}


@pytest.mark.asyncio
async def test_accepted_share_closes_feedback_loop_and_preserves_meta_event() -> None:
    engine = UnifiedMiningEngine()

    await engine.on_share_result(
        {
            "job_id": "unit-job",
            "nonce": 987654,
            "strategy_used": "phi_scaled_compressed_solver_search",
            "phi_resonance_score": 0.9,
            "solve_time": 0.2,
            "thermal_cost": 0.1,
        },
        accepted=True,
    )

    state = engine.get_unified_state()

    assert state["state"]["accepted_shares"] == 1
    assert state["state"]["rejected_shares"] == 0
    assert state["state"]["meta_learning_event"] is not None
    assert engine.consciousness.coherence_meter >= 0.7
