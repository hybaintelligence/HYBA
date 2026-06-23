"""CTD formalism tests for substrate-agnostic Hilbert-space mathematics."""

from __future__ import annotations

import math

import pytest

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover - minimal dependency environments
    np = None

pytestmark_numpy = pytest.mark.skipif(np is None, reason="numpy is not installed")

try:
    from hypothesis import given, settings
    from hypothesis import strategies as st
except ImportError:  # pragma: no cover - minimal dependency environments
    given = settings = st = None

from pythia_mining.ctd_formalism import (
    HilbertState,
    dense_state_bytes,
    golden_phase_state,
    golden_ratio_unitary,
    phi_log_bond_dimension,
    review_ctd_claims,
    run_deutsch_pulvini_benchmark,
    run_ctd_formalism_experiment,
)
from pythia_mining.phi_config import PHI


@pytestmark_numpy
def test_hilbert_state_born_density_and_unitary_invariants() -> None:
    state = golden_phase_state(32)
    evolved = state.evolve(golden_ratio_unitary(32))
    density = evolved.density_matrix()

    assert np.isclose(np.linalg.norm(state.amplitudes), 1.0)
    assert np.isclose(np.linalg.norm(evolved.amplitudes), 1.0)
    assert np.isclose(np.sum(evolved.born_probabilities()), 1.0)
    assert np.isclose(np.trace(density).real, 1.0)
    assert np.linalg.norm(density - density.conj().T, ord="fro") < 1e-12
    assert np.min(np.linalg.eigvalsh(density).real) > -1e-12


@pytestmark_numpy
def test_invalid_non_unitary_evolution_is_rejected() -> None:
    state = HilbertState.from_amplitudes([1.0, 1.0])
    with pytest.raises(ValueError, match="unitary"):
        state.evolve(np.array([[1.0, 1.0], [0.0, 1.0]], dtype=np.complex128))


@pytestmark_numpy
def test_pulvini_phi_ctd_experiment_compresses_and_keeps_claim_boundary() -> None:
    packet = run_ctd_formalism_experiment(32, fold_depth=2)
    review = packet.claim_review

    assert packet.dimension == 32
    assert packet.compression_ratio > 1.0
    assert packet.reversible_compression is True
    assert packet.reconstruction_error < 1e-8
    assert math.isclose(
        packet.phi * packet.phi, packet.phi + 1.0, rel_tol=0.0, abs_tol=1e-12
    )
    assert review.rigorous is True
    assert review.implements_hilbert_space_math is True
    assert review.uses_pulvini_phi_compression is True
    assert review.claims_physical_quantum_hardware is False
    assert review.claims_universal_quantum_speedup is False
    assert review.claims_rsa_break is False
    assert review.claims_physical_quantum_computers_unnecessary is False


def test_claim_review_recommendation_fails_when_unproven_claims_are_enabled() -> None:
    review = review_ctd_claims(
        {
            "claims_universal_quantum_speedup": True,
            "claims_physical_quantum_hardware": True,
        }
    )

    assert review.rigorous is False
    assert review.as_dict()["rigorous"] is False


if given is not None:

    @pytestmark_numpy
    @given(
        dimension=st.integers(min_value=1, max_value=64),
        phase_seed=st.floats(
            min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False
        ),
    )
    @settings(max_examples=40, deadline=None)
    def test_golden_phase_state_property_invariants(
        dimension: int, phase_seed: float
    ) -> None:
        state = golden_phase_state(dimension, phase_seed=phase_seed)
        evolved = state.evolve(golden_ratio_unitary(dimension))
        probabilities = evolved.born_probabilities()

        assert state.dimension == dimension
        assert np.isclose(np.linalg.norm(evolved.amplitudes), 1.0, atol=1e-12)
        assert np.all(probabilities >= 0.0)
        assert np.isclose(np.sum(probabilities), 1.0, atol=1e-12)
        assert abs(PHI * PHI - (PHI + 1.0)) < 1e-12

else:

    @pytest.mark.skip(reason="hypothesis is not installed")
    def test_golden_phase_state_property_invariants() -> None:
        pass


@pytestmark_numpy
def test_ctd_formalism_microbenchmark_is_bounded_and_replayable() -> None:
    samples = [run_ctd_formalism_experiment(16, phase_seed=float(i)) for i in range(5)]

    assert all(sample.reversible_compression for sample in samples)
    assert all(sample.compression_ratio > 1.0 for sample in samples)
    assert max(sample.elapsed_seconds for sample in samples) < 1.0
    assert {sample.dimension for sample in samples} == {16}


def test_deutsch_pulvini_benchmark_validates_exponential_wall_not_breakthrough() -> (
    None
):
    report = run_deutsch_pulvini_benchmark((30, 50, 100, 1000))
    rows = report.rows

    assert report.rigorous is True
    assert report.validates_exponential_wall is True
    assert report.claims_exponential_breakthrough is False
    assert report.claims_quantum_hardware_obsolete is False
    assert [row.qubits for row in rows] == [30, 50, 100, 1000]
    assert rows[-1].structured_state_class == "low_entanglement_phi_log_mps"
    assert rows[-1].dense_state_bytes == dense_state_bytes(1000)
    assert rows[-1].structured_state_bytes < 10_000_000
    assert rows[-1].unstructured_parameter_ratio > rows[0].unstructured_parameter_ratio


def test_phi_bond_dimension_scales_logarithmically_for_structured_subset() -> None:
    dimensions = [phi_log_bond_dimension(n) for n in (30, 50, 100, 200, 1000)]

    assert dimensions == sorted(dimensions)
    assert dimensions[-1] < 20
    assert dense_state_bytes(31) == 2 * dense_state_bytes(30)
