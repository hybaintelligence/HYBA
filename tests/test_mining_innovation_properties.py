from __future__ import annotations

import asyncio
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.phi_scaling_engine import (  # noqa: E402
    PHI,
    PhiResonanceAnalyzer,
    PhiScaledEnsemble,
    benchmark_vs_asic,
)
from pythia_mining.quantum_solver import (  # noqa: E402
    MAX_UINT32_NONCE,
    PULVINI_HASHRATE_CAP_EHS,
    DodecahedralQuantumSolver,
    QuantumSolverConfigurationError,
)


def _solve_nonce(target: int, start: int, end: int) -> int | None:
    async def _run() -> int | None:
        solver = DodecahedralQuantumSolver(configured_capacity_ehs=0.1)
        await solver.configure_search(target=target, nonce_ranges=[(start, end)])
        return await solver.solve(max_iterations=25, timeout=5.0)

    return asyncio.run(_run())


@pytest.mark.parametrize(
    ("target", "start", "end"),
    [
        (0x1D00FFFF, 0, 4095),
        (0x1A2B3C4D, 1024, 8191),
        (0x00ABCDEF, 50_000, 52_047),
        (2**128 + 1597, 900_000, 902_047),
    ],
)
def test_property_pythia_search_is_deterministic_for_same_target_and_range(
    target: int,
    start: int,
    end: int,
) -> None:
    """Capability invariant: same target/range must produce the same candidate nonce."""
    first = _solve_nonce(target, start, end)
    second = _solve_nonce(target, start, end)

    assert first is not None
    assert second is not None
    assert first == second
    assert start <= first <= end


@pytest.mark.parametrize(
    "nonce_ranges",
    [
        [],
        [(-1, 10)],
        [(100, 10)],
        [(0, MAX_UINT32_NONCE + 1)],
    ],
)
def test_property_pythia_rejects_invalid_nonce_ranges(
    nonce_ranges: list[tuple[int, int]],
) -> None:
    """Capability invariant: the solver must fail closed on invalid search spaces."""

    async def _run() -> None:
        solver = DodecahedralQuantumSolver()
        await solver.configure_search(target=0x1D00FFFF, nonce_ranges=nonce_ranges)

    with pytest.raises(QuantumSolverConfigurationError):
        asyncio.run(_run())


@pytest.mark.parametrize("configured_capacity", [0.01, 0.1, 1.0, 10.0, 10_000.0])
def test_property_pulvini_capacity_never_exceeds_governance_cap(
    configured_capacity: float,
) -> None:
    """Capability invariant: configured hashrate estimates remain capped at the PULVINI boundary."""
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=configured_capacity)
    assert solver.configured_capacity_ehs <= PULVINI_HASHRATE_CAP_EHS

    for scale in (0.25, 1.0, 4.0, 32.0):
        solver.set_power_scale(scale)
        metrics = solver.get_metrics()
        assert metrics["hashrate_ehs"] <= PULVINI_HASHRATE_CAP_EHS
        assert metrics["hashrate_cap_ehs"] == PULVINI_HASHRATE_CAP_EHS
        assert metrics["capacity_source"] == "configured_estimate"


def test_property_unconfigured_solver_does_not_fabricate_hashrate() -> None:
    """Capability invariant: absent measured/configured capacity, hashrate telemetry is None."""
    solver = DodecahedralQuantumSolver()
    metrics = solver.get_metrics()
    assert metrics["hashrate_ehs"] is None
    assert metrics["capacity_source"] == "not_configured"
    assert metrics["telemetry_source"] == "derived_runtime_state"


def test_property_benchmark_projection_is_not_reported_as_measured_performance() -> (
    None
):
    """Capability invariant: projection-only benchmark records cannot masquerade as measured mining performance."""
    projection = benchmark_vs_asic(measured_hashes_per_second=None)
    assert projection["benchmark_mode"] == "projection_only"
    assert projection["measured_hashes_per_second"] is None
    assert projection["effective_hashes_per_second"] is None
    assert projection["projected_vs_asic_ratio"] is None

    measured = benchmark_vs_asic(measured_hashes_per_second=110e12)
    assert measured["benchmark_mode"] == "measured_input"
    assert measured["measured_hashes_per_second"] == 110e12
    assert measured["effective_hashes_per_second"] is not None
    assert measured["projected_vs_asic_ratio"] is not None
    assert math.isfinite(measured["projected_vs_asic_ratio"])


def test_property_phi_scaled_ensemble_is_repeatable_and_normalized() -> None:
    """Capability invariant: phi-weighted local decisions are deterministic and normalized."""
    predictions = {
        "geometric": {"score": 0.61},
        "topological": {"score": 0.55},
        "causal": {"score": 0.58},
    }
    indicators = {
        "nonce_lane": {"a": 1.0, "b": PHI, "c": PHI**2},
        "share_health": {"x": 0.5, "y": 0.5 * PHI, "z": 0.5 * PHI**2},
    }

    first = PhiScaledEnsemble().predict_with_phi_scaling(predictions, indicators)
    second = PhiScaledEnsemble().predict_with_phi_scaling(predictions, indicators)

    assert first == second
    assert 0.0 <= first["phi_score"] <= 1.0
    assert 0.0 <= first["indicator_harmony"] <= 1.0
    assert 0.0 <= first["final_score"] <= 1.0
    assert 0.0 <= first["coherence"] <= 1.0
    assert abs(sum(first["phi_weights"]) - 1.0) < 1e-12


def test_property_phi_resonance_analyzer_outputs_bounded_capability_metrics() -> None:
    """Capability invariant: resonance telemetry remains bounded and interpretable."""
    series = [1.0, PHI, PHI**2, PHI**3, PHI**4, PHI**5]
    result = PhiResonanceAnalyzer().analyze_phi_resonance({"phi_lane": series})

    assert "phi_lane_resonance" in result
    resonance = result["phi_lane_resonance"]
    assert 0.0 <= resonance["harmony_score"] <= 1.0
    assert 0.0 <= resonance["resonance_strength"] <= 1.0
    assert resonance["is_fibonacci"] is True
