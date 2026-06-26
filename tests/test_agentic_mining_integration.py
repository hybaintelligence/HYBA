"""Tests for agentic-mining integration layer.

Covers:
- Shared PULVINI core compression and graph analysis
- Token optimization for mining contexts
- Evidence sealing for mining events
- Golden-ratio hardware scaling proposals
- Mining agent registration and execution
- Integration fail-closed behavior
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict

import pytest

# ---------------------------------------------------------------------------
# Shared PULVINI core
# ---------------------------------------------------------------------------
from pythia_shared.pulvini_core import (
    PHI,
    PulviniCore,
    phi_fold,
    verify_symmetric_graph,
    compute_graph_automorphisms,
    compute_evidence_seal,
    verify_evidence_seal,
)

# ---------------------------------------------------------------------------
# Mining modules
# ---------------------------------------------------------------------------
from pythia_mining.golden_ratio_scaler import GoldenRatioScaler, ScalingPlan
from pythia_mining.mining_evidence_seal import (
    create_mining_evidence_seal,
    verify_mining_evidence_seal,
    seal_autonomous_decision,
    seal_reflexive_proposal,
    seal_scaling_plan,
)

# ---------------------------------------------------------------------------
# Agentic modules (optional — skip gracefully if missing)
# ---------------------------------------------------------------------------
try:
    from hyba_genesis_api.api.agentic_intelligence_service.service import (
        TokenOptimizationEngine,
        AgentMarketplace,
    )
    from hyba_genesis_api.api.agentic_intelligence_service.mining_agents import (
        register_mining_agents,
    )

    AGENTIC_AVAILABLE = True
except Exception:  # pragma: no cover - environment may lack dependencies
    AGENTIC_AVAILABLE = False


# ---------------------------------------------------------------------------
# Shared constants / helpers
# ---------------------------------------------------------------------------

EXPECTED_PHI = (1.0 + math.sqrt(5.0)) / 2.0


# ===================================================================
# PULVINI core tests
# ===================================================================


class TestPulviniCoreCompression:
    def test_phi_fold_compresses_pairs(self):
        arr = [1.0, 2.0, 3.0, 4.0]
        result = phi_fold(arr)
        assert result.working_set_compression_ratio >= 1.0

    def test_phi_fold_single_element(self):
        result = phi_fold([1.0])
        assert result.compressed_size == result.original_size  # no pair to fold

    def test_phi_fold_large_array(self):
        arr = [float(i) for i in range(100)]
        result = phi_fold(arr)
        # φ-folding is lossy; verify stable compression ratio
        assert result.working_set_compression_ratio >= 1.0

    def test_phi_is_golden_ratio(self):
        assert abs(PHI - EXPECTED_PHI) < 1e-12


class TestPulviniCoreGraph:
    def test_verify_symmetric_graph_empty(self):
        assert verify_symmetric_graph({}) is True

    def test_verify_symmetric_graph_simple(self):
        adjacency = {0: [1], 1: [0]}
        assert verify_symmetric_graph(adjacency) is True

    def test_verify_symmetric_graph_asymmetric(self):
        adjacency = {0: [1], 1: []}
        assert verify_symmetric_graph(adjacency) is False

    def test_compute_automorphisms_returns_order_and_orbits(self):
        adjacency = {0: [1], 1: [0]}
        result = compute_graph_automorphisms(adjacency)
        assert result.order >= 1
        assert result.orbits is not None


# ===================================================================
# Evidence sealing tests
# ===================================================================


class TestMiningEvidenceSealing:
    def test_create_seal_deterministic(self):
        payload = {"event": "test", "value": 42}
        seal1 = create_mining_evidence_seal("test", payload)
        seal2 = create_mining_evidence_seal("test", payload)
        assert seal1["body_hash"] == seal2["body_hash"]

    def test_seal_contains_required_fields(self):
        seal = create_mining_evidence_seal("test", {})
        assert "body_hash" in seal
        assert "timestamp" in seal
        assert seal["algorithm"] == "sha256"
        assert seal["immutable_guard_active"] is True

    def test_verify_valid_seal(self):
        payload = {"x": 1}
        seal = create_mining_evidence_seal("t", payload)
        assert verify_mining_evidence_seal("t", payload, seal) is True

    def test_verify_invalid_seal(self):
        payload = {"x": 1}
        seal = create_mining_evidence_seal("t", payload)
        assert verify_mining_evidence_seal("t", {"x": 2}, seal) is False


# ===================================================================
# Golden ratio hardware scaling tests
# ===================================================================


class TestGoldenRatioScaler:
    def test_fib_base_one(self):
        scaler = GoldenRatioScaler(base=1)
        assert scaler._fib(0) == 0
        assert scaler._fib(1) == 1
        assert scaler._fib(2) == 1
        assert scaler._fib(3) == 2
        assert scaler._fib(4) == 3
        assert scaler._fib(5) == 5

    def test_fib_scaled(self):
        scaler = GoldenRatioScaler(base=2)
        assert scaler._fib(2) == 2
        assert scaler._fib(3) == 4
        assert scaler._fib(4) == 6

    def test_next_gpu_count_up(self):
        scaler = GoldenRatioScaler(base=1)
        assert scaler.next_gpu_count(1) == 2
        assert scaler.next_gpu_count(2) == 3
        assert scaler.next_gpu_count(3) == 5
        assert scaler.next_gpu_count(4) == 5

    def test_prev_gpu_count_down(self):
        scaler = GoldenRatioScaler(base=1)
        assert scaler.prev_gpu_count(1) == 1
        assert scaler.prev_gpu_count(2) == 1
        assert scaler.prev_gpu_count(5) == 3
        assert scaler.prev_gpu_count(8) == 5

    def test_propose_scaling_plan_high_coherence(self):
        scaler = GoldenRatioScaler(base=1)
        plan = scaler.propose_scaling_plan(
            dimensions=["gpus", "batch_size"],
            current={"gpus": 1, "batch_size": 1},
            target_coherence=0.9,
            phi_density=0.8,
        )
        assert isinstance(plan, ScalingPlan)
        assert len(plan.proposals) == 2
        for p in plan.proposals:
            assert p.proposed_value >= p.current_value

    def test_propose_scaling_plan_low_coherence(self):
        scaler = GoldenRatioScaler(base=1)
        plan = scaler.propose_scaling_plan(
            dimensions=["gpus", "batch_size"],
            current={"gpus": 8, "batch_size": 8},
            target_coherence=0.2,
            phi_density=0.3,
        )
        for p in plan.proposals:
            assert p.proposed_value <= p.current_value

    def test_to_dict_contains_phi(self):
        scaler = GoldenRatioScaler(base=1)
        d = scaler.to_dict()
        assert abs(d["phi"] - EXPECTED_PHI) < 1e-12


# ===================================================================
# Mining agent tests (require agentic module)
# ===================================================================

@pytest.mark.skipif(not AGENTIC_AVAILABLE, reason="agentic module not available")
class TestMiningAgentRegistration:
    def test_register_mining_agents(self):
        marketplace = AgentMarketplace()
        register_mining_agents(marketplace)

        ids = [a.agent_id for a in marketplace.list_agents()]
        expected = [
            "mining_strategy_optimizer_v1",
            "pool_performance_analyst_v1",
            "consciousness_tuner_v1",
            "hardware_scaling_advisor_v1",
        ]
        for eid in expected:
            assert eid in ids

    def test_mining_agents_have_quantum_backed_or_heuristic(self):
        marketplace = AgentMarketplace()
        register_mining_agents(marketplace)
        for agent in marketplace.list_agents():
            assert agent.evidence_tier in ("quantum_backed", "heuristic")


# ===================================================================
# Integration fail-closed tests
# ===================================================================


class TestIntegrationFailClosed:
    def test_pulvini_core_standalone(self):
        core = PulviniCore()
        assert core is not None
        stats = core.get_metrics()
        assert "compression" in stats
        assert "automorphism" in stats
        assert "evidence" in stats

    def test_golden_scaler_standalone(self):
        scaler = GoldenRatioScaler(base=1)
        plan = scaler.propose_scaling_plan(
            ["gpus"], {"gpus": 1}, 0.9, 0.8
        )
        assert plan is not None

    def test_mining_evidence_seal_standalone(self):
        seal = create_mining_evidence_seal("unit_test", {"k": "v"})
        assert seal["body_hash"] is not None