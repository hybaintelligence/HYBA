"""Production tests for HYBA folded mathematical primitives.

Run with:
    python -m pytest tests/test_production_math_primitives.py
"""
import math

import numpy as np
import pytest

from src.euclid.pythagoras.quantum.operators.folded_probability_amplifier import (
    FoldedAmplifierError,
    recommended_steps,
    run_amplifier,
    uniform_vector,
)
from src.euclid.pythagoras.quantum.operators.omega_tda_audit import (
    OmegaAuditError,
    compare_omega_signatures,
    compute_omega_signature,
)
from src.euclid.pythagoras.quantum.operators.symbolic_verifier import (
    verify_projector,
    verify_symbolic_phi_identity,
    verify_trace_preserved,
    verify_unitary,
)


def test_omega_signature_is_deterministic_for_fixed_input():
    data = np.linspace(-1.0, 1.0, 128)
    first = compute_omega_signature(data).to_dict()
    second = compute_omega_signature(data).to_dict()
    assert first == second


def test_omega_signature_rejects_nan_adversarial_input():
    with pytest.raises(OmegaAuditError):
        compute_omega_signature(np.array([1.0, np.nan, 3.0]))


def test_omega_comparison_identical_tensor_is_stable():
    rng = np.random.default_rng(7)
    data = rng.normal(size=256)
    result = compare_omega_signatures(data, data, threshold=0.01)
    assert result.stable
    assert result.score == pytest.approx(0.0, abs=1e-9)


def test_folded_amplifier_promotes_marked_index():
    result = run_amplifier(16, [3])
    assert result.best_index == 3
    assert result.best_probability > 0.80
    assert result.deterministic_capacity > 0


@pytest.mark.parametrize("dimension", [4, 8, 16, 32, 64])
def test_recommended_steps_are_positive_and_bounded(dimension):
    steps = recommended_steps(dimension, 1)
    assert steps >= 1
    assert steps <= dimension


def test_uniform_vector_has_unit_norm_property():
    for dimension in range(2, 40):
        vector = uniform_vector(dimension)
        assert np.linalg.norm(vector) == pytest.approx(1.0)


def test_folded_amplifier_rejects_bad_indices():
    with pytest.raises(FoldedAmplifierError):
        run_amplifier(8, [-1])
    with pytest.raises(FoldedAmplifierError):
        run_amplifier(8, [8])


def test_symbolic_phi_identity():
    result = verify_symbolic_phi_identity()
    assert result.passed


def test_unitary_verifier_accepts_hadamard():
    h = np.array([[1.0, 1.0], [1.0, -1.0]]) / math.sqrt(2.0)
    result = verify_unitary(h)
    assert result.passed
    assert result.residual < 1e-8


def test_projector_verifier_accepts_rank_one_projector():
    p = np.array([[1.0, 0.0], [0.0, 0.0]])
    assert verify_projector(p).passed


def test_trace_preservation_verifier():
    a = np.eye(3)
    b = np.diag([0.5, 1.0, 1.5])
    assert verify_trace_preserved(a, b).passed
