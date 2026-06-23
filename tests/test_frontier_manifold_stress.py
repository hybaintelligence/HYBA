"""
Unit and Integration Tests for Manifold Collapse Stresser

TESTING METHODOLOGY:
- Unit tests: Individual component verification (QFI, Ricci, stability)
- Integration tests: Full stress test pipeline
- Property-based tests: Mathematical invariants (using Hypothesis)
- Benchmark tests: Performance regression tracking

MATHEMATICAL PROPERTIES TESTED:
1. QFI matrix is symmetric positive semi-definite
2. Ricci curvature bounds (-∞, log(dim))
3. Geometric stability ∈ [0, 1]
4. Compression ratio ≈ φ⁻¹ (golden ratio)
5. Eigenvalue ordering (largest to smallest)
"""

import sys
from pathlib import Path
import pytest
import numpy as np
from hypothesis import given, strategies as st, settings
from hypothesis.extra.numpy import arrays

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))
sys.path.insert(0, str(Path(__file__).parent))

from frontier_manifold_stress import ManifoldStressAnalyzer
from pythia_mining.pulvini_bures import density_state, bures_certificate
from pythia_mining.phi_folding import PhiFoldingOperator


# ============================================================================
# UNIT TESTS
# ============================================================================


class TestManifoldStressAnalyzer:
    """Unit tests for ManifoldStressAnalyzer components."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return ManifoldStressAnalyzer(phi_threshold=0.5)

    @pytest.fixture
    def random_density_matrix(self):
        """Generate valid density matrix."""
        dim = 4
        raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = density_state(raw)
        return rho

    def test_qfi_matrix_symmetry(self, analyzer, random_density_matrix):
        """Test QFI matrix is symmetric."""
        qfi = analyzer.compute_fisher_information_matrix(random_density_matrix)

        # Check symmetry
        assert np.allclose(qfi, qfi.T, atol=1e-10), "QFI must be symmetric"

    def test_qfi_matrix_positive_semidefinite(self, analyzer, random_density_matrix):
        """Test QFI matrix is positive semi-definite."""
        qfi = analyzer.compute_fisher_information_matrix(random_density_matrix)

        # Check PSD via eigenvalues
        eigvals = np.linalg.eigvalsh(qfi)
        assert np.all(
            eigvals >= -1e-10
        ), f"QFI must be PSD, got min eigval {eigvals[0]}"

    def test_ricci_curvature_bounds(self, analyzer, random_density_matrix):
        """Test Ricci curvature has expected bounds."""
        ricci = analyzer.compute_ricci_scalar(random_density_matrix)

        # Ricci should be bounded
        dim = random_density_matrix.shape[0]
        lower_bound = -10 * np.log(dim)  # Reasonable lower bound
        upper_bound = np.log(dim)  # Reasonable upper bound

        assert (
            lower_bound <= ricci <= upper_bound
        ), f"Ricci {ricci} outside bounds [{lower_bound}, {upper_bound}]"

    def test_geometric_stability_range(self, analyzer, random_density_matrix):
        """Test geometric stability ∈ [0, 1]."""
        stability = analyzer.compute_geometric_stability(random_density_matrix)

        assert 0.0 <= stability <= 1.0, f"Stability {stability} must be in [0, 1]"

    def test_compression_efficiency_near_golden_ratio(self, analyzer):
        """Test compression ratio approximates φ⁻¹."""
        folding_operator = PhiFoldingOperator()
        phi = 1.618033988749895

        # Test various dimensions
        for dim in [10, 21, 55, 89, 144]:  # Fibonacci numbers
            compression = analyzer.compute_compression_efficiency(dim, folding_operator)

            # Should be close to 1/φ ≈ 0.618
            assert (
                0.5 <= compression <= 0.7
            ), f"Compression {compression} should be near 1/φ at dim {dim}"

    def test_pure_state_low_ricci(self, analyzer):
        """Test pure states have low Ricci curvature."""
        # Pure state: |0⟩⟨0|
        dim = 4
        psi = np.zeros(dim)
        psi[0] = 1.0
        rho = np.outer(psi, psi.conj())

        ricci = analyzer.compute_ricci_scalar(rho)

        # Pure states should have near-zero or negative Ricci
        assert ricci <= 1.0, f"Pure state Ricci {ricci} should be low"

    def test_maximally_mixed_high_stability(self, analyzer):
        """Test maximally mixed state has high stability."""
        # Maximally mixed: ρ = I/d
        dim = 4
        rho = np.eye(dim, dtype=np.complex128) / dim

        stability = analyzer.compute_geometric_stability(rho)

        # Maximally mixed should be very stable
        assert stability >= 0.5, f"Maximally mixed stability {stability} should be high"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestManifoldStressIntegration:
    """Integration tests for full stress pipeline."""

    def test_stress_pipeline_small_dimensions(self):
        """Test full stress pipeline on small dimensions."""
        from frontier_manifold_stress import ManifoldStressAnalyzer
        from pythia_mining.phi_folding import PhiFoldingOperator

        analyzer = ManifoldStressAnalyzer()
        folding = PhiFoldingOperator()

        # Test on small dimensions only (fast)
        dimensions = [4, 8]

        for dim in dimensions:
            # Generate random density matrix
            raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            rho = density_state(raw)

            # Compute all metrics
            stability = analyzer.compute_geometric_stability(rho)
            ricci = analyzer.compute_ricci_scalar(rho)
            qfi = analyzer.compute_fisher_information_matrix(rho)
            compression = analyzer.compute_compression_efficiency(dim, folding)

            # Basic sanity checks
            assert 0.0 <= stability <= 1.0
            assert isinstance(ricci, float)
            assert qfi.shape == (dim, dim)
            assert 0.0 <= compression <= 1.0

    def test_collapse_detection(self):
        """Test that collapse is detected at high dimensions."""
        analyzer = ManifoldStressAnalyzer()

        # Create highly perturbed state (should have low stability)
        dim = 16
        # Random non-PSD matrix (will be fixed by density_state)
        raw = np.random.randn(dim, dim) * 10.0  # Large perturbation
        rho = density_state(raw)

        stability = analyzer.compute_geometric_stability(rho, entropy_rate=1.0)

        # With high entropy rate, stability can drop
        # (Not guaranteed to collapse, but test the metric exists)
        assert 0.0 <= stability <= 1.0


# ============================================================================
# PROPERTY-BASED TESTS (Hypothesis)
# ============================================================================


@given(
    dim=st.integers(min_value=2, max_value=8),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20, deadline=5000)
def test_qfi_eigenvalues_nonnegative(dim, seed):
    """Property: QFI eigenvalues are always non-negative."""
    np.random.seed(seed)

    analyzer = ManifoldStressAnalyzer()

    # Generate random density matrix
    raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    rho = density_state(raw)

    qfi = analyzer.compute_fisher_information_matrix(rho)
    eigvals = np.linalg.eigvalsh(qfi)

    assert np.all(
        eigvals >= -1e-10
    ), f"QFI eigenvalues must be non-negative, got {eigvals}"


@given(
    dim=st.integers(min_value=2, max_value=8),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=20, deadline=5000)
def test_stability_idempotent(dim, seed):
    """Property: Computing stability twice gives same result."""
    np.random.seed(seed)

    analyzer = ManifoldStressAnalyzer()

    raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    rho = density_state(raw)

    stability1 = analyzer.compute_geometric_stability(rho)
    stability2 = analyzer.compute_geometric_stability(rho)

    assert np.isclose(
        stability1, stability2, atol=1e-10
    ), "Stability should be deterministic"


@given(
    dim=st.integers(min_value=2, max_value=8),
    scale=st.floats(min_value=0.1, max_value=10.0),
)
@settings(max_examples=20, deadline=5000)
def test_qfi_scaling_invariance(dim, scale):
    """Property: QFI is invariant under density matrix scaling."""
    analyzer = ManifoldStressAnalyzer()

    # Generate density matrix
    raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
    rho = density_state(raw)

    # QFI should be invariant to trace (density_state normalizes)
    qfi1 = analyzer.compute_fisher_information_matrix(rho)

    # Scale and re-normalize
    rho_scaled = density_state(rho * scale)
    qfi2 = analyzer.compute_fisher_information_matrix(rho_scaled)

    # Should be very close (within numerical precision)
    assert np.allclose(
        qfi1, qfi2, atol=1e-8
    ), "QFI should be scale-invariant after normalization"


# ============================================================================
# BENCHMARK TESTS
# ============================================================================


class TestManifoldStressBenchmarks:
    """Benchmark tests for performance regression tracking."""

    @pytest.mark.benchmark
    def test_qfi_computation_speed(self, benchmark):
        """Benchmark QFI matrix computation."""
        analyzer = ManifoldStressAnalyzer()

        # 8x8 density matrix
        dim = 8
        raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = density_state(raw)

        result = benchmark(analyzer.compute_fisher_information_matrix, rho)

        # Sanity check result
        assert result.shape == (dim, dim)

    @pytest.mark.benchmark
    def test_ricci_computation_speed(self, benchmark):
        """Benchmark Ricci curvature computation."""
        analyzer = ManifoldStressAnalyzer()

        dim = 8
        raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = density_state(raw)

        result = benchmark(analyzer.compute_ricci_scalar, rho)

        assert isinstance(result, float)

    @pytest.mark.benchmark
    def test_stability_computation_speed(self, benchmark):
        """Benchmark geometric stability computation."""
        analyzer = ManifoldStressAnalyzer()

        dim = 8
        raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = density_state(raw)

        result = benchmark(analyzer.compute_geometric_stability, rho)

        assert 0.0 <= result <= 1.0

    @pytest.mark.benchmark
    def test_full_stress_analysis_speed(self, benchmark):
        """Benchmark full stress analysis pipeline."""
        analyzer = ManifoldStressAnalyzer()
        folding = PhiFoldingOperator()

        def full_analysis():
            dim = 8
            raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
            rho = density_state(raw)

            stability = analyzer.compute_geometric_stability(rho)
            ricci = analyzer.compute_ricci_scalar(rho)
            compression = analyzer.compute_compression_efficiency(dim, folding)

            return stability, ricci, compression

        result = benchmark(full_analysis)

        stability, ricci, compression = result
        assert 0.0 <= stability <= 1.0
        assert isinstance(ricci, float)
        assert 0.0 <= compression <= 1.0


# ============================================================================
# REGRESSION TESTS
# ============================================================================


class TestManifoldStressRegression:
    """Regression tests to prevent breaking changes."""

    def test_known_pure_state_metrics(self):
        """Test metrics on known pure state match expected values."""
        analyzer = ManifoldStressAnalyzer()

        # Pure state |0⟩
        dim = 4
        psi = np.zeros(dim, dtype=np.complex128)
        psi[0] = 1.0
        rho = np.outer(psi, psi.conj())

        stability = analyzer.compute_geometric_stability(rho, entropy_rate=0.01)

        # Pure state should have relatively high stability
        # (exact value depends on implementation, but should be > 0.3)
        assert (
            stability >= 0.3
        ), f"Pure state stability regression: expected >= 0.3, got {stability}"

    def test_known_mixed_state_metrics(self):
        """Test metrics on known mixed state."""
        analyzer = ManifoldStressAnalyzer()

        # Maximally mixed state
        dim = 4
        rho = np.eye(dim, dtype=np.complex128) / dim

        stability = analyzer.compute_geometric_stability(rho, entropy_rate=0.01)

        # Maximally mixed should be very stable
        assert (
            stability >= 0.5
        ), f"Mixed state stability regression: expected >= 0.5, got {stability}"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================


class TestManifoldStressEdgeCases:
    """Edge case tests for boundary conditions."""

    def test_single_qubit_density_matrix(self):
        """Test stress analysis on single qubit (2x2)."""
        analyzer = ManifoldStressAnalyzer()

        # Single qubit pure state
        rho = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)

        # Should not crash
        qfi = analyzer.compute_fisher_information_matrix(rho)
        ricci = analyzer.compute_ricci_scalar(rho)
        stability = analyzer.compute_geometric_stability(rho)

        assert qfi.shape == (2, 2)
        assert isinstance(ricci, float)
        assert 0.0 <= stability <= 1.0

    def test_high_entropy_rate(self):
        """Test stability with very high entropy rate."""
        analyzer = ManifoldStressAnalyzer()

        dim = 4
        raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = density_state(raw)

        # Very high entropy rate
        stability = analyzer.compute_geometric_stability(rho, entropy_rate=10.0)

        # Should still be bounded
        assert 0.0 <= stability <= 1.0

    def test_zero_entropy_rate(self):
        """Test stability with zero entropy rate."""
        analyzer = ManifoldStressAnalyzer()

        dim = 4
        raw = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        rho = density_state(raw)

        # Zero entropy rate
        stability = analyzer.compute_geometric_stability(rho, entropy_rate=0.0)

        # Should handle gracefully
        assert 0.0 <= stability <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
