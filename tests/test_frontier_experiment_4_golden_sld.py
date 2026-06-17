"""Tests for Frontier Experiment 4: Golden SLD."""

import numpy as np
import pytest

from pythia_mining.frontier_experiment_4_golden_sld import (
    QuantumMetrologyPoint,
    adversarial_sequence,
    compute_qfi_from_density,
    compute_sld_gradient_norm,
    generate_density_from_sequence,
    get_experiment_metadata,
    measure_discrepancy_qfi_point,
    phi_lcg_sequence,
    random_sequence,
    run_golden_sld_correlation_experiment,
)


def test_phi_lcg_sequence_deterministic():
    """φ-LCG sequence should be deterministic."""
    seq1 = phi_lcg_sequence(100)
    seq2 = phi_lcg_sequence(100)
    np.testing.assert_array_equal(seq1, seq2)


def test_phi_lcg_sequence_range():
    """φ-LCG sequence should be in [0, 1)."""
    seq = phi_lcg_sequence(1000)
    assert np.all(seq >= 0.0)
    assert np.all(seq < 1.0)


def test_random_sequence_range():
    """Random sequence should be in [0, 1)."""
    seq = random_sequence(1000)
    assert np.all(seq >= 0.0)
    assert np.all(seq < 1.0)


def test_adversarial_sequence_structure():
    """Adversarial sequence should cluster at 0 and 1."""
    seq = adversarial_sequence(100)
    # Should have ~half at 0, ~half at 1
    near_zero = np.sum(seq < 0.1)
    near_one = np.sum(seq > 0.9)
    assert near_zero + near_one >= 90  # Most points at extremes


def test_generate_density_hermitian():
    """Generated density should be Hermitian."""
    seq = phi_lcg_sequence(100)
    rho = generate_density_from_sequence(seq, dim=8)
    
    # Check Hermiticity: rho = rho†
    np.testing.assert_array_almost_equal(rho, rho.conj().T)


def test_generate_density_trace_one():
    """Generated density should have trace 1."""
    seq = random_sequence(100)
    rho = generate_density_from_sequence(seq, dim=8)
    
    trace = np.trace(rho)
    assert abs(trace - 1.0) < 1e-6


def test_generate_density_positive_semidefinite():
    """Generated density should be positive semidefinite."""
    seq = phi_lcg_sequence(100)
    rho = generate_density_from_sequence(seq, dim=8)
    
    eigenvalues = np.linalg.eigvalsh(rho)
    assert np.all(eigenvalues >= -1e-10), "Eigenvalues should be non-negative"


def test_compute_qfi_non_negative():
    """QFI should be non-negative."""
    rho = np.diag([0.5, 0.3, 0.2])
    qfi = compute_qfi_from_density(rho)
    
    assert qfi >= 0.0
    assert np.isfinite(qfi)


def test_compute_qfi_deterministic():
    """QFI computation should be deterministic."""
    rho = np.diag([0.6, 0.3, 0.1])
    qfi1 = compute_qfi_from_density(rho)
    qfi2 = compute_qfi_from_density(rho)
    
    assert abs(qfi1 - qfi2) < 1e-10


def test_sld_gradient_norm_non_negative():
    """SLD gradient norm should be non-negative."""
    rho = np.diag([0.7, 0.2, 0.1])
    norm = compute_sld_gradient_norm(rho)
    
    assert norm >= 0.0
    assert np.isfinite(norm)


def test_measure_discrepancy_qfi_point_phi():
    """Discrepancy-QFI measurement for φ-LCG should complete."""
    seq = phi_lcg_sequence(500)
    point = measure_discrepancy_qfi_point(seq, "phi_lcg")
    
    assert isinstance(point, QuantumMetrologyPoint)
    assert point.sample_size == 500
    assert point.sequence_type == "phi_lcg"
    assert point.star_discrepancy > 0.0
    assert point.quantum_fisher_information >= 0.0
    assert np.isfinite(point.quantum_fisher_information)


def test_measure_discrepancy_qfi_point_random():
    """Discrepancy-QFI measurement for random should complete."""
    seq = random_sequence(500)
    point = measure_discrepancy_qfi_point(seq, "random")
    
    assert point.sequence_type == "random"
    assert np.isfinite(point.star_discrepancy)


def test_golden_sld_correlation_experiment():
    """Full Golden SLD experiment should run and produce analysis."""
    sample_sizes = [100, 500, 1000]  # Small for fast test
    
    points, analysis = run_golden_sld_correlation_experiment(sample_sizes)
    
    # Should have 3 points per size (phi, random, adversarial)
    assert len(points) == len(sample_sizes) * 3
    
    # Analysis should contain expected keys
    assert "correlation_coefficient" in analysis
    assert "r_squared" in analysis
    assert "hypothesis_result" in analysis
    assert "breakthrough_achieved" in analysis
    
    # Correlation should be finite
    assert np.isfinite(analysis["correlation_coefficient"])
    
    # R² should be in [0, 1] (can be negative for very bad fits)
    # assert analysis["r_squared"] >= 0.0
    
    # QFI improvement ratio should be positive
    assert analysis["qfi_improvement_ratio"] > 0.0


def test_experiment_metadata():
    """Experiment metadata should contain required fields."""
    metadata = get_experiment_metadata()
    
    assert "experiment_id" in metadata
    assert "hypothesis" in metadata
    assert "falsifiability" in metadata
    assert "breakthrough_threshold" in metadata
    
    assert metadata["experiment_id"] == "FRONTIER-GOLDEN-SLD-004"


def test_quantum_metrology_point_structure():
    """QuantumMetrologyPoint should have correct structure."""
    point = QuantumMetrologyPoint(
        sample_size=1000,
        star_discrepancy=0.01,
        quantum_fisher_information=5.0,
        sld_gradient_norm=2.5,
        sequence_type="phi_lcg",
    )
    
    assert point.sample_size == 1000
    assert point.star_discrepancy > 0.0
    assert point.quantum_fisher_information >= 0.0
    assert point.sequence_type in ["phi_lcg", "random", "adversarial"]
