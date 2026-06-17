"""Tests for Frontier Experiment 2: QFI-Preserving MPS Truncation."""

import numpy as np
import pytest

from pythia_mining.frontier_experiment_2_qfi_truncation import (
    TruncationMetrics,
    compute_fidelity,
    compute_sld_sensitivity,
    compress_mps_with_method,
    get_experiment_metadata,
    measure_ground_state_energy,
    measure_total_entanglement,
    qfi_adaptive_truncation,
    run_comparative_truncation_benchmark,
    standard_svd_truncation,
)
from pythia_mining.tensor_network_1000qubit import MPS


def test_sld_sensitivity_normalization():
    """QFI sensitivity weights should be normalized."""
    schmidt_spectrum = np.array([0.7, 0.5, 0.3, 0.1])
    
    weights = compute_sld_sensitivity(schmidt_spectrum)
    
    assert len(weights) == len(schmidt_spectrum)
    assert np.abs(np.sum(weights) - 1.0) < 1e-6, "Weights should sum to 1"
    assert np.all(weights >= 0), "Weights should be non-negative"


def test_sld_sensitivity_deterministic():
    """QFI sensitivity should be deterministic."""
    schmidt_spectrum = np.array([0.8, 0.4, 0.2])
    
    weights1 = compute_sld_sensitivity(schmidt_spectrum)
    weights2 = compute_sld_sensitivity(schmidt_spectrum)
    
    np.testing.assert_array_almost_equal(weights1, weights2)


def test_qfi_adaptive_truncation():
    """QFI truncation should select top indices by combined score."""
    U = np.random.randn(10, 5) + 1j * np.random.randn(10, 5)
    S = np.array([1.0, 0.8, 0.6, 0.4, 0.2])
    Vh = np.random.randn(5, 8) + 1j * np.random.randn(5, 8)
    
    U_trunc, S_trunc, Vh_trunc = qfi_adaptive_truncation(U, S, Vh, max_bond=3)
    
    assert U_trunc.shape == (10, 3)
    assert len(S_trunc) == 3
    assert Vh_trunc.shape == (3, 8)
    assert np.all(S_trunc > 0)


def test_standard_svd_truncation():
    """Standard truncation should keep largest singular values."""
    U = np.random.randn(10, 5)
    S = np.array([1.0, 0.8, 0.6, 0.4, 0.2])
    Vh = np.random.randn(5, 8)
    
    U_trunc, S_trunc, Vh_trunc = standard_svd_truncation(U, S, Vh, max_bond=3)
    
    assert U_trunc.shape == (10, 3)
    assert len(S_trunc) == 3
    assert Vh_trunc.shape == (3, 8)
    # Should keep the three largest values
    np.testing.assert_array_equal(S_trunc, S[:3])


def test_compress_mps_standard():
    """Standard MPS compression should work without errors."""
    mps = MPS(num_sites=5, physical_dim=2, max_bond_dim=8)
    
    mps_compressed = compress_mps_with_method(mps, max_bond=4, method="standard")
    
    assert mps_compressed.num_sites == mps.num_sites
    assert max(mps_compressed.bond_dims) <= 4


def test_compress_mps_qfi_adaptive():
    """QFI-adaptive MPS compression should work without errors."""
    mps = MPS(num_sites=5, physical_dim=2, max_bond_dim=8)
    
    mps_compressed = compress_mps_with_method(mps, max_bond=4, method="qfi_adaptive")
    
    assert mps_compressed.num_sites == mps.num_sites
    assert max(mps_compressed.bond_dims) <= 4


def test_measure_ground_state_energy():
    """Ground state energy measurement should return finite value."""
    mps = MPS(num_sites=5, physical_dim=2, max_bond_dim=4)
    
    energy = measure_ground_state_energy(mps)
    
    assert np.isfinite(energy)
    assert isinstance(energy, float)


def test_measure_total_entanglement():
    """Total entanglement should be non-negative."""
    mps = MPS(num_sites=5, physical_dim=2, max_bond_dim=4)
    
    entanglement = measure_total_entanglement(mps)
    
    assert entanglement >= 0.0
    assert np.isfinite(entanglement)


def test_compute_fidelity_identity():
    """Fidelity of MPS with itself should be 1.0."""
    mps = MPS(num_sites=5, physical_dim=2, max_bond_dim=4)
    
    fidelity = compute_fidelity(mps, mps)
    
    assert 0.99 <= fidelity <= 1.0, f"Self-fidelity should be ~1.0, got {fidelity}"


def test_compute_fidelity_range():
    """Fidelity should be in [0, 1]."""
    mps1 = MPS(num_sites=5, physical_dim=2, max_bond_dim=4)
    mps2 = MPS(num_sites=5, physical_dim=2, max_bond_dim=4)
    
    fidelity = compute_fidelity(mps1, mps2)
    
    assert 0.0 <= fidelity <= 1.0


def test_comparative_truncation_benchmark():
    """Comparative benchmark should run and produce analysis."""
    qfi_metrics, standard_metrics, analysis = run_comparative_truncation_benchmark(
        num_sites=10,  # Small for fast test
        initial_bond=16,
        target_bond=4,
    )
    
    assert isinstance(qfi_metrics, TruncationMetrics)
    assert isinstance(standard_metrics, TruncationMetrics)
    assert isinstance(analysis, dict)
    
    # Metrics should have expected fields
    assert qfi_metrics.method_name == "qfi_adaptive"
    assert standard_metrics.method_name == "standard_svd"
    
    # Analysis should contain expected keys
    assert "energy_error_ratio" in analysis
    assert "fidelity_improvement" in analysis
    assert "hypothesis_result" in analysis
    assert "breakthrough_achieved" in analysis
    
    # Error ratio should be positive
    assert analysis["energy_error_ratio"] > 0.0
    
    # Both methods should have finite errors
    assert np.isfinite(qfi_metrics.energy_error)
    assert np.isfinite(standard_metrics.energy_error)


def test_experiment_metadata():
    """Experiment metadata should contain required fields."""
    metadata = get_experiment_metadata()
    
    assert "experiment_id" in metadata
    assert "hypothesis" in metadata
    assert "falsifiability" in metadata
    assert "breakthrough_threshold" in metadata
    assert "reproducibility" in metadata
    
    assert metadata["experiment_id"] == "FRONTIER-QFI-002"


def test_truncation_metrics_properties():
    """TruncationMetrics should satisfy basic properties."""
    metrics = TruncationMetrics(
        method_name="test",
        truncated_bond_dim=8,
        energy_error=0.01,
        entanglement_error=0.05,
        fidelity=0.95,
        qfi_preservation=0.9,
    )
    
    assert metrics.method_name == "test"
    assert metrics.truncated_bond_dim == 8
    assert 0.0 <= metrics.fidelity <= 1.0
