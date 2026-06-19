"""Tests for QuantumProgramBenchmark and golden ratio scaling benchmarks.

These tests cover the helper functions inside `benchmark_quantum_programs.py` that
should behave predictably for small input sizes.  Because full tensor network
benchmarks are expensive, we restrict to small numbers of qubits to ensure
the functions return without exhausting resources.  We validate golden ratio
bond dimension calculations, mass gap checks, naive state memory calculations,
simple density matrix benchmarks, and PULVINI compression tests.
"""

from __future__ import annotations


from python_backend.pythia_mining.benchmark_quantum_programs import (
    QuantumProgramBenchmark,
)


def test_compute_phi_bond_dim_non_power_of_two() -> None:
    """The computed bond dimension should not be a power of two and be within [2,64]."""
    for n in [10, 50, 100]:
        chi = QuantumProgramBenchmark.compute_phi_bond_dim(n)
        assert 2 <= chi <= 64
        # chi is not a power of two
        assert (chi & (chi - 1)) != 0


def test_verify_phi_scaling_returns_reasonable_results() -> None:
    """Verify phi scaling results are irrational and errors within bounds."""
    results = QuantumProgramBenchmark.verify_phi_scaling(max_qubits=100)
    assert results
    for r in results:
        assert r.is_irrational is True
        assert 0.0 <= r.phi_approximation_error < 1.0


def test_verify_mass_gap_trivial_spectrum_passes() -> None:
    """A small spectrum should pass the mass gap verification with default confidence."""
    spectrum = [0.1, 0.2, 0.3]
    result = QuantumProgramBenchmark.verify_mass_gap(spectrum)
    assert result.passed is True
    assert result.measured_alignment == 1.0


def test_calculate_naive_state_vector_memory_small_qubits() -> None:
    """Calculating memory for a small qubit count should return finite TB values."""
    res = QuantumProgramBenchmark.calculate_naive_state_vector_memory(5)
    assert res["success"] is False
    assert "memory_tb" in res
    assert res["memory_tb"] > 0.0


def test_benchmark_density_matrix_construction_small_qubits() -> None:
    """Density matrix construction benchmark should succeed for small qubit counts."""
    res = QuantumProgramBenchmark.benchmark_density_matrix_construction(
        num_qubits=2, use_phi_acceleration=True
    )
    assert res.success is True
    assert res.method == "Φ-Accelerated TN"
    # mass_gap_alignment should be between 0 and 1
    assert 0.0 <= res.mass_gap_alignment <= 1.0


def test_verify_pulvini_compression_small_qubits() -> None:
    """PULVINI compression test should report reversible compression with ratio ≥1."""
    result = QuantumProgramBenchmark.verify_pulvini_compression(num_qubits=5)
    assert result.reversible is True
    assert result.compression_ratio >= 1.0
    # phi fold efficiency should be ≤1 and non-negative
    assert 0.0 <= result.phi_fold_efficiency <= 1.0
