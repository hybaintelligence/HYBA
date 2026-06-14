from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.phi_scaling_engine import PHI, PhiScaledEnsemble, benchmark_vs_asic  # noqa: E402
from pythia_mining.pulvini_memory_compression_proof import (  # noqa: E402
    prove_lane_surface_coverage,
    prove_phi_folding_reversibility,
)
from pythia_mining.quantum_solver import DodecahedralQuantumSolver  # noqa: E402


def _phi_resonance_strength(value: int, scale: float = PHI**15) -> float:
    """Return [0, 1] distance-to-nearest-Phi^15-multiple score."""
    if value <= 0:
        return 0.0
    k = round(value / scale)
    diff = abs(value - (k * scale))
    return float(max(0.0, 1.0 - diff / (scale / 2.0)))


def _structured_order(candidates: list[int]) -> list[int]:
    """Deterministic structure-first ordering used only for benefit assessment tests."""
    return sorted(
        candidates,
        key=lambda nonce: (
            -_phi_resonance_strength(nonce),
            abs((nonce % 89) - round(89 / PHI)),
            nonce,
        ),
    )


def _first_hit_rank(order: list[int], target_set: set[int]) -> int:
    for index, item in enumerate(order, start=1):
        if item in target_set:
            return index
    return len(order) + 1


def test_benefit_pulvini_reduces_active_working_space_without_information_loss() -> None:
    """Benefit test: compression should reduce active working space while preserving reconstruction."""
    for size in (32, 64, 128, 256):
        data = np.linspace(0.0, 1.0, size, dtype=np.float64)
        proof = prove_phi_folding_reversibility(data, fold_depth=1)

        assert proof.reversible is True
        assert proof.complete_coverage is True
        assert proof.deterministic is True
        assert proof.folded_size < proof.original_size
        assert proof.compression_ratio > 1.0
        assert proof.reconstruction_error <= 1e-9


def test_benefit_pulvini_32_lane_surface_aligns_with_dodecahedral_working_set() -> None:
    """Benefit test: the 32-lane surface compresses to the 20-state PYTHIA basis scale."""
    proof = prove_lane_surface_coverage(32, fold_depth=1)
    solver = DodecahedralQuantumSolver()

    assert proof.reversible is True
    assert proof.folded_size == solver.basis_states.shape[0]
    assert proof.original_size == 32
    assert proof.compression_ratio == 1.6


def test_benefit_structure_aware_order_finds_injected_signal_earlier_than_linear_baseline() -> None:
    """Benefit test: if a Phi^15 signal exists, structure-aware ordering should see it early."""
    base = 1_000_000
    candidates = list(range(base, base + 4096))
    injected_signal = int(round(735 * (PHI**15)))
    candidates.append(injected_signal)
    target_set = {injected_signal}

    baseline_rank = _first_hit_rank(candidates, target_set)
    structured_rank = _first_hit_rank(_structured_order(candidates), target_set)

    assert structured_rank < baseline_rank
    assert structured_rank <= max(5, int(0.01 * len(candidates)))


def test_benefit_structure_order_is_deterministic_and_complete() -> None:
    """Benefit test: structure-aware ranking may reorder but must not drop candidates."""
    candidates = [100_000 + i * 37 for i in range(512)]
    first = _structured_order(candidates)
    second = _structured_order(candidates)

    assert first == second
    assert set(first) == set(candidates)
    assert len(first) == len(candidates)


def test_benefit_phi_scaled_decision_improves_when_indicators_are_structured() -> None:
    """Benefit test: structured indicators should produce higher harmony than unstructured indicators."""
    predictions = {
        "geometric": {"score": 0.58},
        "topological": {"score": 0.61},
        "empirical": {"score": 0.60},
    }
    structured = {
        "nonce_lane": {"a": 1.0, "b": PHI, "c": PHI**2, "d": PHI**3},
    }
    unstructured = {
        "nonce_lane": {"a": 1.0, "b": 1.07, "c": 1.29, "d": 1.41},
    }

    structured_decision = PhiScaledEnsemble().predict_with_phi_scaling(predictions, structured)
    unstructured_decision = PhiScaledEnsemble().predict_with_phi_scaling(predictions, unstructured)

    assert structured_decision["indicator_harmony"] > unstructured_decision["indicator_harmony"]
    assert structured_decision["final_score"] >= unstructured_decision["final_score"]
    assert 0.0 <= structured_decision["final_score"] <= 1.0


def test_benefit_capacity_scaling_requires_measured_input_before_performance_claim() -> None:
    """Benefit test: scaling can project capacity only after measured input exists."""
    projection_only = benchmark_vs_asic(measured_hashes_per_second=None, compression_factor=1.86)
    measured = benchmark_vs_asic(measured_hashes_per_second=1_000_000.0, compression_factor=1.86)

    assert projection_only["benchmark_mode"] == "projection_only"
    assert projection_only["effective_hashes_per_second"] is None
    assert projection_only["projected_vs_asic_ratio"] is None

    assert measured["benchmark_mode"] == "measured_input"
    assert measured["effective_hashes_per_second"] is not None
    assert measured["effective_hashes_per_second"] > measured["measured_hashes_per_second"]
    assert math.isfinite(measured["projected_vs_asic_ratio"])


def test_benefit_candidate_budget_can_be_reduced_when_structure_prior_exists() -> None:
    """Benefit test: structure gives a measurable candidate-budget reduction on structured fixtures."""
    candidates = list(range(5_000, 10_000))
    structured_targets = {nonce for nonce in candidates if _phi_resonance_strength(nonce) >= 0.995}
    assert structured_targets, "fixture should contain at least one high-resonance target"

    baseline_rank = _first_hit_rank(candidates, structured_targets)
    structured_rank = _first_hit_rank(_structured_order(candidates), structured_targets)

    candidate_budget_reduction = 1.0 - (structured_rank / baseline_rank)
    assert structured_rank <= baseline_rank
    assert candidate_budget_reduction >= 0.5
