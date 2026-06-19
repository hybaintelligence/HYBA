"""Tests for Φ-accelerated quantum mathematics utilities.

These tests verify the correctness and invariants of the golden ratio
accelerated functions provided in `phi_accelerated_quantum.py`.  We test
purification, folding compression, decoherence suppression, phase
modulation, unitary evolution, probability distributions, and Grover
diffusion.  Each test focuses on mathematical properties: trace
preservation, unitarity, normalization, and suppression of off-diagonal
terms.
"""

from __future__ import annotations

import numpy as np
import pytest

from python_backend.pythia_mining.phi_accelerated_quantum import (
    PhiAcceleratedDensityMatrix,
    PhiAcceleratedUnitaryEvolution,
    PhiAcceleratedGrover,
    PhiAcceleratedMeasurement,
)


def test_phi_weighted_purification_on_identity() -> None:
    """Purification of the maximally mixed state should return the same state."""
    # Identity density matrix for a single qubit (normalized)
    rho = np.eye(2, dtype=complex) / 2.0
    purified = PhiAcceleratedDensityMatrix.phi_weighted_purification(rho, iterations=3)
    # Should remain Hermitian and trace-normalized
    assert np.allclose(purified, purified.conj().T, atol=1e-10)
    assert pytest.approx(np.trace(purified), rel=1e-6) == 1.0
    # For identity, output should equal input
    assert np.allclose(purified, rho, atol=1e-6)


def test_phi_folding_compression_small_matrix() -> None:
    """Phi-folding compression reduces dimensionality and computes ratio correctly."""
    rho = np.array([[1, 0], [0, 0]], dtype=complex)
    compressed, ratio = PhiAcceleratedDensityMatrix.phi_folding_compression(rho)
    # 2×2 matrix should fold to 1×1
    assert compressed.shape == (1, 1)
    assert pytest.approx(ratio, rel=1e-6) == 2.0


def test_phi_decoherence_suppression_reduces_off_diagonal() -> None:
    """Decoherence suppression should reduce off-diagonal magnitude and preserve trace."""
    rho = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
    suppressed = PhiAcceleratedDensityMatrix.phi_decoherence_suppression(rho, strength=0.1)
    # Trace should remain 1
    assert np.isclose(np.trace(suppressed), 1.0, atol=1e-6)
    # Off-diagonals should be damped compared to original
    assert abs(suppressed[0, 1]) <= abs(rho[0, 1])
    assert abs(suppressed[1, 0]) <= abs(rho[1, 0])


def test_phi_phase_modulation_preserves_norm() -> None:
    """Phase modulation should not change the norm of the state vector."""
    psi = np.array([1.0, 1.0j], dtype=complex) / np.sqrt(2)
    modulated = PhiAcceleratedUnitaryEvolution.phi_phase_modulation(psi)
    assert np.isclose(np.linalg.norm(modulated), 1.0, atol=1e-6)


def test_phi_optimized_unitary_is_unitary() -> None:
    """Phi-optimized unitary evolution should produce a unitary matrix."""
    H = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=float)
    dt = 0.1
    U = PhiAcceleratedUnitaryEvolution.phi_optimized_unitary(H, dt)
    # U†U = I
    identity = np.eye(2, dtype=complex)
    assert np.allclose(U.conj().T @ U, identity, atol=1e-6)


def test_phi_diffusion_normalization() -> None:
    """Phi-enhanced diffusion should return a normalized state vector."""
    grover = PhiAcceleratedGrover(dim=4)
    state = np.ones(4, dtype=complex) / 2.0
    diffused = grover.phi_diffusion(state)
    assert np.isclose(np.linalg.norm(diffused), 1.0, atol=1e-6)


def test_phi_weighted_expectation_smoothed_distribution() -> None:
    """Phi-optimized probability distribution should remain normalized."""
    psi = np.array([1.0 + 0j, 1.0 + 0j], dtype=complex) / np.sqrt(2)
    dist = PhiAcceleratedMeasurement.phi_optimized_probability_distribution(psi)
    assert np.isclose(dist.sum(), 1.0, atol=1e-6)
