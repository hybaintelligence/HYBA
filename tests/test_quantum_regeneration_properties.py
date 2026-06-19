"""Property-based invariants for quantum_regeneration module.

These tests verify that the salamander-regeneration-inspired self-healing
module satisfies mathematical invariants across a vast range of inputs.

Key invariants tested:
- Density matrix properties (Hermitian, trace 1, positive semi-definite)
- Von Neumann entropy bounds (0 ≤ S(ρ) ≤ log(DIM))
- Born rule probability normalization
- Refractory period temporal consistency
- Lindblad decay trace preservation
- Regeneration pipeline state transitions

Run with:
    PYTHONPATH=python_backend python -m pytest tests/test_quantum_regeneration_properties.py -v -x --timeout=120
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = str(REPO_ROOT / "python_backend")
if PYTHON_BACKEND not in sys.path:
    sys.path.insert(0, PYTHON_BACKEND)

from pythia_mining.stateful_regeneration import (
    ModuleState,
    Role,
    DIM,
    apply_fault,
    quarantine_channel,
    measure_role,
    regeneration_fidelity,
    validate_collapse_or_quarantine,
    lindblad_decay_operator,
    joint_state,
    is_separable_approx,
)


# =============================================================================
# STRATEGIES
# =============================================================================


@given(st.floats(min_value=0.0, max_value=1.0))
def test_density_matrix_hermitian(severity):
    """ModuleState density matrices must be Hermitian."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Check Hermitian property: ρ = ρ†
    assert np.allclose(state.rho, state.rho.conj().T, atol=1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_density_matrix_trace_one(severity):
    """ModuleState density matrices must have trace = 1."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Check trace property: Tr(ρ) = 1
    trace = np.trace(state.rho).real
    assert np.isclose(trace, 1.0, atol=1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_density_matrix_positive_semi_definite(severity):
    """ModuleState density matrices must be positive semi-definite."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Check PSD property: all eigenvalues ≥ 0
    eigvals = np.linalg.eigvalsh(state.rho)
    assert np.all(eigvals >= -1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_von_neumann_entropy_bounds(severity):
    """Von Neumann entropy must be in [0, log(DIM)]."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    entropy = state.von_neumann_entropy()
    max_entropy = math.log(DIM)

    # Check entropy bounds: 0 ≤ S(ρ) ≤ log(DIM)
    assert 0.0 <= entropy <= max_entropy + 1e-8


@given(st.floats(min_value=0.0, max_value=1.0))
def test_role_probabilities_normalize(severity):
    """Role probabilities must sum to 1 (Born rule normalization)."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    probs = state.role_probabilities()
    prob_sum = sum(probs.values())

    # Check normalization: Σ P(role) = 1
    assert np.isclose(prob_sum, 1.0, atol=1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_role_probabilities_non_negative(severity):
    """Role probabilities must be non-negative."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    probs = state.role_probabilities()

    # Check non-negativity: P(role) ≥ 0
    for prob in probs.values():
        assert prob >= -1e-8


@given(st.floats(min_value=0.0, max_value=1.0))
def test_refractory_period_temporal_consistency(severity):
    """Refractory period must be temporally consistent."""
    state = ModuleState.healthy("test_module")
    state.enter_refractory_period(duration=60.0)

    # Check that refractory period is set
    assert state.refractory_period_end > 0.0

    # Check that module is in refractory period immediately after
    assert state.is_in_refractory_period()


@given(st.floats(min_value=0.0, max_value=1.0))
def test_refractory_period_expiration(severity):
    """Refractory period must expire after duration."""
    state = ModuleState.healthy("test_module")
    state.enter_refractory_period(duration=0.1)  # Short duration for testing

    # Check that module is in refractory period immediately after
    assert state.is_in_refractory_period()

    # Wait for expiration
    import time

    time.sleep(0.15)

    # Check that module is no longer in refractory period
    assert not state.is_in_refractory_period()


@given(st.floats(min_value=0.0, max_value=1.0))
def test_lindblad_decay_trace_preservation(severity):
    """Lindblad decay must preserve trace = 1."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Apply Lindblad decay
    state = lindblad_decay_operator(state, decay_rate=0.1)

    # Check trace preservation
    trace = np.trace(state.rho).real
    assert np.isclose(trace, 1.0, atol=1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_lindblad_decay_psd_preservation(severity):
    """Lindblad decay must preserve positive semi-definiteness."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Apply Lindblad decay
    state = lindblad_decay_operator(state, decay_rate=0.1)

    # Check PSD preservation
    eigvals = np.linalg.eigvalsh(state.rho)
    assert np.all(eigvals >= -1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_regeneration_fidelity_bounds(severity):
    """Regeneration fidelity must be in [0, 1]."""
    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    fidelity = regeneration_fidelity(state, Role.HEALTHY_SPECIALIZED)

    # Check fidelity bounds: 0 ≤ F ≤ 1
    assert 0.0 <= fidelity <= 1.0 + 1e-8


@given(st.floats(min_value=0.0, max_value=1.0))
def test_regeneration_pipeline_trace(severity):
    """Regeneration pipeline must preserve trace = 1 throughout."""
    import numpy as np

    state = ModuleState.healthy("test_module")
    trace = np.trace(state.rho).real
    assert np.isclose(trace, 1.0, atol=1e-8)

    state = apply_fault(state, severity)
    trace = np.trace(state.rho).real
    assert np.isclose(trace, 1.0, atol=1e-8)

    state = quarantine_channel(state)
    trace = np.trace(state.rho).real
    assert np.isclose(trace, 1.0, atol=1e-8)


@given(st.floats(min_value=0.0, max_value=1.0))
def test_joint_state_separability(severity):
    """Independent modules must have separable joint state."""
    state_a = ModuleState.healthy("module_a")
    state_b = ModuleState.healthy("module_b")

    # Uncorrelated joint state should be separable
    rho_joint = joint_state(state_a, state_b, correlated=False)

    # Check PPT criterion for separability
    # Note: PPT is necessary but not sufficient for separability in general
    # For 2xN systems, PPT is sufficient
    is_separable = is_separable_approx(rho_joint, atol=1e-6)

    # Uncorrelated states should be separable
    assert is_separable


@given(st.floats(min_value=0.0, max_value=1.0))
def test_correlated_joint_state_non_separability(severity):
    """Correlated modules should have non-separable joint state."""
    state_a = ModuleState.healthy("module_a")
    state_b = ModuleState.healthy("module_b")

    # Correlated joint state should be non-separable
    rho_joint = joint_state(state_a, state_b, correlated=True)

    # Check PPT criterion for separability
    is_separable = is_separable_approx(rho_joint, atol=1e-6)

    # Correlated states should be non-separable
    assert not is_separable


@given(st.floats(min_value=0.0, max_value=1.0))
def test_measure_role_state_collapse(severity):
    """Measurement must collapse state to pure role projector."""
    import numpy as np

    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Measure role
    rng = np.random.default_rng()
    collapsed_role, collapsed_state = measure_role(state, rng)

    # Check that collapsed state is pure (entropy = 0)
    entropy = collapsed_state.von_neumann_entropy()
    assert entropy < 1e-8


@given(st.floats(min_value=0.0, max_value=1.0))
def test_validate_collapse_or_quarantine(severity):
    """Malformed collapse must result in quarantined state."""

    state = ModuleState.healthy("test_module")
    state = apply_fault(state, severity)
    state = quarantine_channel(state)

    # Simulate malformed collapse (wrong role)
    target_role = Role.HEALTHY_SPECIALIZED
    collapsed_role = Role.BLASTEMA  # Wrong role

    state = validate_collapse_or_quarantine(collapsed_role, target_role, state)

    # Check that state is quarantined (MALFORMED role)
    probs = state.role_probabilities()
    malformed_prob = probs[Role.MALFORMED]

    # Should be in MALFORMED state
    assert malformed_prob > 0.99


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-x", "--timeout=120"])
