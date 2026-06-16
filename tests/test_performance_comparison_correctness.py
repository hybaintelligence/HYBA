"""Performance Comparison: Classical Implementation Correctness

THESIS: Classical implementation of quantum mathematics is mathematically correct,
even if slower than quantum hardware. Performance (speed) and correctness (accuracy)
are independent dimensions.

These tests verify that classical implementations produce correct results
within acceptable error bounds, regardless of execution time.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

np.seterr(all="raise")

from pythia_mining.pulvini_bures import bures_certificate, density_state
from pythia_mining.pulvini_group import (
    a5_representation_certificate,
    coxeter_group_certificate,
)
from pythia_mining.pulvini_operator import ManifoldOperator
from pythia_mining.pulvini_topology import ADJACENCY_MAP, NUM_NODES
from pythia_mining.quantum_solver import DodecahedralQuantumSolver


class TestCorrectnessIndependentOfPerformance:
    """Correctness is independent of execution time."""

    def test_density_matrix_correctness_regardless_of_computation_time(self):
        """Density matrix axioms hold regardless of how long computation takes.
        
        Correctness: axioms satisfied
        Performance: computation time
        These are independent dimensions.
        """
        # Create a complex state
        psi = np.random.randn(32) + 1j * np.random.randn(32)
        psi /= np.linalg.norm(psi)
        
        # Measure computation time
        start = time.perf_counter()
        rho = density_state(np.outer(psi, np.conj(psi)))
        elapsed = time.perf_counter() - start
        
        # Verify correctness (independent of time)
        hermitian_error = np.linalg.norm(rho - np.conj(rho.T), "fro")
        eigenvalues = np.linalg.eigvalsh(rho)
        trace_val = np.trace(rho)
        purity = np.trace(rho @ rho)
        
        # Correctness holds regardless of elapsed time
        assert hermitian_error < 1e-10
        assert np.all(eigenvalues >= -1e-10)
        assert np.isclose(trace_val, 1.0)
        assert purity <= 1.0 + 1e-10
        
        # Time is just a performance metric, not a correctness metric
        assert elapsed > 0  # Took some time
        # But correctness is independent of that time

    def test_group_theory_correctness_regardless_of_computation_time(self):
        """Group theory results are exact regardless of computation time.
        
        Correctness: exact mathematical results
        Performance: computation time
        These are independent dimensions.
        """
        # Measure computation time
        start = time.perf_counter()
        cert = coxeter_group_certificate()
        elapsed = time.perf_counter() - start
        
        # Verify correctness (independent of time)
        assert cert.order == 120  # Exact result
        assert cert.rank == 3  # Exact result
        assert cert.coxeter_diagram == "o-5-o-3-o"  # Exact result
        
        # Time is just a performance metric
        assert elapsed > 0
        # But correctness is independent

    def test_unitary_evolution_correctness_regardless_of_computation_time(self):
        """Unitary evolution correctness is independent of computation time.
        
        Correctness: norm preservation, determinism
        Performance: matrix multiplication time
        These are independent dimensions.
        """
        dim = 16
        H = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        H = (H + H.conj().T) / 2
        
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        
        # Measure computation time
        start = time.perf_counter()
        U = np.linalg.expm(-1j * H * 0.01)
        psi_evolved = U @ psi
        elapsed = time.perf_counter() - start
        
        # Verify correctness (independent of time)
        assert np.isclose(np.linalg.norm(psi_evolved), 1.0, atol=1e-10)
        assert np.allclose(U @ U.conj().T, np.eye(dim), atol=1e-10)
        
        # Time is just a performance metric
        assert elapsed > 0
        # But correctness is independent


class TestErrorBoundsAreMathematicalNotPhysical:
    """Error bounds are determined by numerical precision, not physical substrate."""

    def test_error_bounds_determined_by_machine_precision(self):
        """Error bounds are determined by floating-point precision, not physics.
        
        Classical hardware: IEEE 754 double precision (~1e-15 relative error)
        Quantum hardware: physical noise and decoherence
        These are different error sources, but both have mathematical bounds.
        """
        # Test golden ratio computation
        phi = (1 + np.sqrt(5)) / 2
        phi_squared = phi ** 2
        phi_plus_one = phi + 1
        
        # Error bound is determined by machine precision
        error = abs(phi_squared - phi_plus_one)
        
        # Mathematical property: error < machine epsilon
        assert error < 1e-14  # IEEE 754 double precision
        
        # This is a numerical error bound, not a physical one

    def test_density_matrix_error_bounds_are_numerical(self):
        """Density matrix error bounds are numerical, not physical.
        
        Errors come from:
        - Floating-point rounding
        - Matrix decomposition precision
        - Numerical integration
        
        Not from:
        - Physical decoherence
        - Quantum noise
        - Hardware imperfections
        """
        psi = np.random.randn(32) + 1j * np.random.randn(32)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, np.conj(psi))
        
        rho_proc = density_state(rho)
        
        # Error bounds are numerical
        hermitian_error = np.linalg.norm(rho_proc - np.conj(rho_proc.T), "fro")
        trace_error = abs(np.trace(rho_proc) - 1.0)
        
        # Both errors are bounded by numerical precision
        assert hermitian_error < 1e-10
        assert trace_error < 1e-10
        
        # These are numerical bounds, not physical

    def test_bures_geometry_error_bounds_are_numerical(self):
        """Bures geometry error bounds are numerical, not physical.
        
        Errors come from eigenvalue decomposition precision,
        not from physical manifold curvature.
        """
        psi = np.random.randn(16) + 1j * np.random.randn(16)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, np.conj(psi))
        
        cert = bures_certificate(rho, 0.5)
        
        # Error bounds are numerical
        assert cert.closed  # Geometry closes within numerical precision
        assert cert.bures_norm >= 0  # Non-negative within numerical precision
        
        # These are numerical properties, not physical


class TestDeterminismVsPerformance:
    """Determinism is a correctness property, not a performance property."""

    def test_determinism_is_correctness_not_performance(self):
        """Determinism means same input → same output.
        
        This is a correctness property, not a performance property.
        A slow deterministic system is still correct.
        """
        # Create state
        psi = np.random.randn(32) + 1j * np.random.randn(32)
        psi /= np.linalg.norm(psi)
        
        # Evolve twice
        op = ManifoldOperator()
        rho = np.outer(psi, np.conj(psi))
        
        # First evolution
        start1 = time.perf_counter()
        result1 = op.ensure_density_state(psi)
        time1 = time.perf_counter() - start1
        
        # Second evolution (same input)
        start2 = time.perf_counter()
        result2 = op.ensure_density_state(psi)
        time2 = time.perf_counter() - start2
        
        # Determinism: same output
        assert np.allclose(result1, result2, atol=1e-14)
        
        # Performance: times may differ (system load, etc.)
        # But correctness (determinism) is independent

    def test_reproducibility_is_correctness_not_performance(self):
        """Reproducibility means same computation → same result across runs.
        
        This is a correctness property, not a performance property.
        """
        # Test reproducibility of group theory computation
        cert1 = coxeter_group_certificate()
        cert2 = coxeter_group_certificate()
        
        # Reproducibility: same results
        assert cert1.order == cert2.order
        assert cert1.rank == cert2.rank
        assert cert1.coxeter_diagram == cert2.coxeter_diagram
        
        # This is reproducibility (correctness), not performance


class TestMathematicalCorrectnessAcrossScales:
    """Mathematical correctness holds across different problem scales."""

    def test_correctness_at_small_scale(self):
        """Correctness holds at small scale (fast computation)."""
        dim = 4
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, np.conj(psi))
        
        # Fast computation (small scale)
        rho_proc = density_state(rho)
        
        # Correctness holds
        assert np.allclose(rho_proc, rho_proc.conj().T, atol=1e-14)
        assert np.isclose(np.trace(rho_proc), 1.0, atol=1e-14)

    def test_correctness_at_medium_scale(self):
        """Correctness holds at medium scale (moderate computation)."""
        dim = 32
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, np.conj(psi))
        
        # Moderate computation (medium scale)
        rho_proc = density_state(rho)
        
        # Correctness holds
        assert np.allclose(rho_proc, rho_proc.conj().T, atol=1e-10)
        assert np.isclose(np.trace(rho_proc), 1.0, atol=1e-10)

    def test_correctness_at_large_scale(self):
        """Correctness holds at large scale (slow computation)."""
        dim = 128
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, np.conj(psi))
        
        # Slow computation (large scale)
        rho_proc = density_state(rho)
        
        # Correctness holds (even though slower)
        assert np.allclose(rho_proc, rho_proc.conj().T, atol=1e-10)
        assert np.isclose(np.trace(rho_proc), 1.0, atol=1e-10)


class TestNumericalStabilityIsMathematicalProperty:
    """Numerical stability is a mathematical property of algorithms."""

    def test_numerical_stability_is_algorithm_property(self):
        """Numerical stability is determined by algorithm design, not hardware.
        
        Well-conditioned algorithms are stable on any substrate.
        Ill-conditioned algorithms are unstable on any substrate.
        """
        # Well-conditioned operation: norm preservation
        psi = np.random.randn(32) + 1j * np.random.randn(32)
        psi /= np.linalg.norm(psi)
        
        # Unitary evolution is numerically stable
        H = np.random.randn(32, 32) + 1j * np.random.randn(32, 32)
        H = (H + H.conj().T) / 2
        U = np.linalg.expm(-1j * H * 0.001)
        psi_evolved = U @ psi
        
        # Stable: norm preserved
        assert np.isclose(np.linalg.norm(psi_evolved), 1.0, atol=1e-10)
        
        # This stability is mathematical, not hardware-dependent

    def test_ill_conditioned_operations_show_numerical_instability(self):
        """Ill-conditioned operations show instability on any substrate.
        
        This is a mathematical property, not a hardware limitation.
        """
        # Ill-conditioned operation: nearly singular matrix
        A = np.random.randn(16, 16) + 1j * np.random.randn(16, 16)
        # Make nearly singular
        A[:, 0] = A[:, 1] * 1.0000001
        
        # Condition number is high (ill-conditioned)
        cond = np.linalg.cond(A)
        assert cond > 1e10  # Ill-conditioned
        
        # This ill-conditioning is mathematical, not hardware-dependent


class TestPrecisionScalingIsMathematical:
    """Precision scaling is determined by numerical analysis, not physics."""

    def test_higher_precision_improves_accuracy(self):
        """Higher numerical precision improves accuracy (mathematical fact).
        
        This is true on any substrate: better precision → better accuracy.
        """
        # Single precision
        psi_single = np.random.randn(32, dtype=np.float32) + 1j * np.random.randn(32, dtype=np.float32)
        psi_single /= np.linalg.norm(psi_single)
        rho_single = np.outer(psi_single, np.conj(psi_single)).astype(np.complex64)
        
        # Double precision
        psi_double = psi_single.astype(np.complex128)
        psi_double /= np.linalg.norm(psi_double)
        rho_double = np.outer(psi_double, np.conj(psi_double))
        
        # Double precision has lower error
        hermitian_error_single = np.linalg.norm(rho_single - np.conj(rho_single.T), "fro")
        hermitian_error_double = np.linalg.norm(rho_double - np.conj(rho_double.T), "fro")
        
        # Mathematical fact: higher precision → lower error
        assert hermitian_error_double < hermitian_error_single
        
        # This is numerical analysis, not physics

    def test_precision_requirements_are_problem_dependent(self):
        """Required precision depends on problem conditioning, not hardware.
        
        Well-conditioned problems need less precision.
        Ill-conditioned problems need more precision.
        """
        # Well-conditioned: simple state
        psi_well = np.zeros(32, dtype=complex)
        psi_well[0] = 1.0
        rho_well = np.outer(psi_well, np.conj(psi_well))
        
        # Ill-conditioned: superposition of many states
        psi_ill = np.random.randn(32) + 1j * np.random.randn(32)
        psi_ill /= np.linalg.norm(psi_ill)
        rho_ill = np.outer(psi_ill, np.conj(psi_ill))
        
        # Both satisfy axioms (correctness)
        assert np.allclose(rho_well, rho_well.conj().T, atol=1e-14)
        assert np.allclose(rho_ill, rho_ill.conj().T, atol=1e-14)
        
        # But ill-conditioned may need higher precision for some operations
        # This is numerical analysis, not hardware limitation


class TestPerformanceDoesNotAffectCorrectness:
    """Performance characteristics do not affect mathematical correctness."""

    def test_slow_computation_can_be_correct(self):
        """Slow computation can still be mathematically correct.
        
        Correctness ≠ Speed
        """
        # Intentionally slow operation (large matrix)
        dim = 256
        H = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        H = (H + H.conj().T) / 2
        
        psi = np.random.randn(dim) + 1j * np.random.randn(dim)
        psi /= np.linalg.norm(psi)
        
        # Slow computation
        start = time.perf_counter()
        U = np.linalg.expm(-1j * H * 0.001)
        psi_evolved = U @ psi
        elapsed = time.perf_counter() - start
        
        # Slow but correct
        assert elapsed > 0.01  # Slow
        assert np.isclose(np.linalg.norm(psi_evolved), 1.0, atol=1e-10)  # Correct

    def test_fast_computation_can_be_incorrect(self):
        """Fast computation can be mathematically incorrect if algorithm is wrong.
        
        Speed ≠ Correctness
        """
        # Fast but incorrect operation (wrong formula)
        psi = np.random.randn(32) + 1j * np.random.randn(32)
        psi /= np.linalg.norm(psi)
        
        # Fast: simple scaling (wrong unitary evolution)
        start = time.perf_counter()
        psi_wrong = 2.0 * psi  # Wrong: doesn't preserve norm
        elapsed = time.perf_counter() - start
        
        # Fast but incorrect
        assert elapsed < 0.001  # Fast
        assert not np.isclose(np.linalg.norm(psi_wrong), 1.0, atol=1e-10)  # Incorrect


class TestCorrectnessVerificationIsMathematical:
    """Correctness verification is mathematical, not physical."""

    def test_axiom_verification_is_mathematical(self):
        """Verifying mathematical axioms is a mathematical process.
        
        Check: does ρ satisfy ρ† = ρ?
        This is a mathematical check, not a physical measurement.
        """
        psi = np.random.randn(32) + 1j * np.random.randn(32)
        psi /= np.linalg.norm(psi)
        rho = np.outer(psi, np.conj(psi))
        
        # Mathematical verification
        hermitian_check = np.allclose(rho, rho.conj().T, atol=1e-10)
        trace_check = np.isclose(np.trace(rho), 1.0, atol=1e-10)
        
        # These are mathematical checks
        assert hermitian_check
        assert trace_check

    def test_theorem_verification_is_mathematical(self):
        """Verifying mathematical theorems is a mathematical process.
        
        Check: does ∑dᵢ² = |G| hold?
        This is a mathematical verification, not physical experiment.
        """
        cert = a5_representation_certificate()
        dims = cert.irreducible_dimensions
        sum_squares = sum(d**2 for d in dims)
        
        # Mathematical verification
        theorem_holds = (sum_squares == 60)
        
        # This is mathematical verification
        assert theorem_holds


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
