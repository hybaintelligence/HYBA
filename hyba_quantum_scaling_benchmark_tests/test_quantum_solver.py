"""Tests for the DodecahedralQuantumSolver.

This suite exercises the deterministic aspects of the quantum solver.  It
validates basis generation, input validation in `configure_search`, entropy
calculations for normalized amplitudes, hashrate scaling and power scaling,
and simple nonce projection behaviour.  The aim is to catch configuration
errors and ensure runtime metrics are finite and bounded.
"""

from __future__ import annotations

import numpy as np
import pytest

from python_backend.pythia_mining.quantum_solver import (
    DodecahedralQuantumSolver,
    QuantumSolverConfigurationError,
)


def test_basis_generation_shape_and_finiteness() -> None:
    """Basis states should be a 20×3 matrix of finite complex values."""
    solver = DodecahedralQuantumSolver()
    basis = solver.basis_states
    assert basis.shape == (20, 3)
    assert np.isfinite(basis).all()


def test_configure_search_and_nonce_validation() -> None:
    """Invalid nonce ranges should raise configuration errors and valid ranges configure correctly."""
    solver = DodecahedralQuantumSolver()
    # No ranges
    with pytest.raises(QuantumSolverConfigurationError):
        solver.configure_search(target=10, nonce_ranges=[])
    # Start > end
    with pytest.raises(QuantumSolverConfigurationError):
        solver.configure_search(target=10, nonce_ranges=[(5, 3)])
    # Negative range
    with pytest.raises(QuantumSolverConfigurationError):
        solver.configure_search(target=10, nonce_ranges=[(-1, 3)])
    # Valid range
    assert solver.configure_search(target=10, nonce_ranges=[(0, 5)]) is True
    assert solver.current_config["search_space_size"] == 6
    # Nonce projection from basis index should map into configured range
    assert solver._project_index_to_nonce(0) == 0
    assert solver._project_index_to_nonce(5) == 5


def test_integrated_entropy_for_uniform_distribution() -> None:
    """Uniform amplitudes should yield entropy equal to log2 of the dimension."""
    solver = DodecahedralQuantumSolver()
    amps = np.array([1.0, 1.0, 1.0], dtype=np.complex128) / np.sqrt(3)
    entropy = solver.calculate_integrated_entropy(amps)
    expected = np.log2(3)
    assert pytest.approx(entropy, rel=1e-6) == expected


def test_hashrate_calculation_and_power_scale() -> None:
    """Hashrate calculation should cap at 1 EH/s and scale according to power_scale."""
    solver = DodecahedralQuantumSolver(configured_capacity_ehs=0.5)
    # Default power scale yields 0.5 EH/s
    assert solver.calculate_integrated_hashrate() == pytest.approx(0.5, rel=1e-6)
    solver.set_power_scale(2.0)
    # Should cap at 1.0 EH/s due to governance limit
    assert solver.calculate_integrated_hashrate() == 1.0
    # Invalid power scale should raise error
    with pytest.raises(QuantumSolverConfigurationError):
        solver.set_power_scale(0.0)
