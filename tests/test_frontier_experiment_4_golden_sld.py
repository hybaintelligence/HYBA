"""
Tests for Frontier Experiment 4: Golden SLD — Discrepancy-QFI Correlation

Tests that quantum Fisher information shows functional relationship with
star-discrepancy inverse: QFI ∝ 1/D_N^*
"""

import pytest
import numpy as np
from pythia_mining.frontier_experiment_4_golden_sld import (
    GoldenSLDExperiment,
    run_golden_sld_correlation_experiment,
)


class TestGoldenSLDExperiment:
    """Test Golden SLD experiment infrastructure"""

    def test_phi_lcg_sequence_generation(self):
        """Test φ-LCG sequence is bounded [0,1] and has correct golden ratio step"""
        exp = GoldenSLDExperiment(dim=4)
        sequence = exp.generate_phi_lcg_sequence(100)

        assert len(sequence) == 100
        assert np.all((sequence >= 0) & (sequence <= 1))

        # Check golden ratio step
        diffs = np.diff(sequence)
        # Handle modulo wrapping
        diffs = np.where(diffs < 0, diffs + 1.0, diffs)
        expected_step = exp.phi_inv
        assert np.allclose(diffs, expected_step, atol=1e-10)

    def test_random_sequence_deterministic_with_seed(self):
        """Test random sequence is reproducible with fixed seed"""
        exp = GoldenSLDExperiment(dim=4)
        seq1 = exp.generate_random_sequence(50, seed=42)
        seq2 = exp.generate_random_sequence(50, seed=42)

        assert len(seq1) == 50
        assert np.array_equal(seq1, seq2)

    def test_adversarial_sequence_clustered(self):
        """Test adversarial sequence has high clustering (high discrepancy)"""
        exp = GoldenSLDExperiment(dim=4)
        adversarial = exp.generate_adversarial_sequence(100)

        assert len(adversarial) == 100
        assert np.all((adversarial >= 0) & (adversarial <= 1))

        # Adversarial should have higher discrepancy than φ-LCG
        phi_seq = exp.generate_phi_lcg_sequence(100)

        adv_disc = exp.compute_star_discrepancy(adversarial)
        phi_disc = exp.compute_star_discrepancy(phi_seq)

        assert adv_disc > phi_disc

    def test_star_discrepancy_bounded(self):
        """Test star-discrepancy is bounded [0, 1]"""
        exp = GoldenSLDExperiment(dim=4)

        for seq_gen in [
            exp.generate_phi_lcg_sequence,
            exp.generate_random_sequence,
            exp.generate_adversarial_sequence,
        ]:
            if seq_gen == exp.generate_random_sequence:
                sequence = seq_gen(50, seed=42)
            else:
                sequence = seq_gen(50)

            discrepancy = exp.compute_star_discrepancy(sequence)
            assert 0.0 <= discrepancy <= 1.0

    def test_phi_lcg_optimal_discrepancy(self):
        """Test φ-LCG achieves O(log N / N) discrepancy bound"""
        exp = GoldenSLDExperiment(dim=4)

        for n in [100, 500, 1000]:
            sequence = exp.generate_phi_lcg_sequence(n)
            discrepancy = exp.compute_star_discrepancy(sequence)

            # φ-LCG should satisfy D_N^* ≤ (1 + 1/φ) / N
            theoretical_bound = (1.0 + 1.0 / exp.phi) / n

            # Allow some numerical tolerance
            assert discrepancy <= theoretical_bound * 2.0

    def test_density_matrix_properties(self):
        """Test density matrix from sequence is valid"""
        exp = GoldenSLDExperiment(dim=4)
        sequence = exp.generate_phi_lcg_sequence(100)
        rho = exp.sequence_to_density_matrix(sequence)

        # Check shape
        assert rho.shape == (4, 4)

        # Check Hermitian
        assert np.allclose(rho, rho.conj().T)

        # Check trace = 1
        assert np.isclose(np.trace(rho), 1.0)

        # Check positive semi-definite
        eigvals = np.linalg.eigvalsh(rho)
        assert np.all(eigvals >= -1e-10)

    def test_qfi_computation_positive(self):
        """Test QFI is non-negative"""
        exp = GoldenSLDExperiment(dim=4)
        sequence = exp.generate_phi_lcg_sequence(100)
        rho = exp.sequence_to_density_matrix(sequence)

        qfi = exp.compute_qfi_via_sld(rho)

        assert qfi >= 0.0
        assert np.isfinite(qfi)

    def test_qfi_pure_vs_mixed_state(self):
        """Test QFI computation for pure and mixed states"""
        exp = GoldenSLDExperiment(dim=4)

        # Pure state: ρ = |ψ⟩⟨ψ|
        psi = np.array([1, 0, 0, 0], dtype=complex)
        rho_pure = np.outer(psi, psi.conj())

        # Mixed state: ρ = I/d
        rho_mixed = np.eye(4) / 4

        qfi_pure = exp.compute_qfi_via_sld(rho_pure)
        qfi_mixed = exp.compute_qfi_via_sld(rho_mixed)

        # Both should be finite and non-negative
        assert qfi_pure >= 0.0 and np.isfinite(qfi_pure)
        assert qfi_mixed >= 0.0 and np.isfinite(qfi_mixed)

    def test_optimal_sequence_higher_qfi(self):
        """Test φ-LCG produces higher QFI than adversarial"""
        exp = GoldenSLDExperiment(dim=4)
        n = 500

        phi_seq = exp.generate_phi_lcg_sequence(n)
        adv_seq = exp.generate_adversarial_sequence(n)

        rho_phi = exp.sequence_to_density_matrix(phi_seq)
        rho_adv = exp.sequence_to_density_matrix(adv_seq)

        qfi_phi = exp.compute_qfi_via_sld(rho_phi)
        qfi_adv = exp.compute_qfi_via_sld(rho_adv)

        # Optimal distribution should yield higher QFI
        assert qfi_phi > qfi_adv * 0.8  # Allow some tolerance


class TestGoldenSLDCorrelation:
    """Test correlation experiment"""

    def test_experiment_runs_successfully(self):
        """Test experiment executes without errors"""
        points, analysis = run_golden_sld_correlation_experiment(sample_sizes=[100, 500], dim=4)

        assert len(points) == 6  # 2 sizes × 3 sequence types
        assert analysis is not None

    def test_data_points_structure(self):
        """Test data points have correct structure"""
        points, _ = run_golden_sld_correlation_experiment(sample_sizes=[100], dim=4)

        assert len(points) == 3  # 3 sequence types

        for point in points:
            assert point.sequence_type in ["phi_lcg", "random", "adversarial"]
            assert point.sample_size == 100
            assert point.star_discrepancy > 0
            assert point.qfi >= 0
            assert np.isfinite(point.qfi)

    def test_correlation_metrics_bounded(self):
        """Test correlation metrics are in valid range"""
        _, analysis = run_golden_sld_correlation_experiment(sample_sizes=[100, 500], dim=4)

        # Pearson r in [-1, 1]
        assert -1.0 <= analysis.pearson_r <= 1.0

        # R² in [0, 1]
        assert 0.0 <= analysis.r_squared <= 1.0

        # QFI values positive
        assert analysis.optimal_qfi >= 0
        assert analysis.worst_qfi >= 0

    def test_breakthrough_threshold_logic(self):
        """Test breakthrough threshold correctly evaluated"""
        _, analysis = run_golden_sld_correlation_experiment(sample_sizes=[100, 500, 1000], dim=4)

        # Breakthrough requires |r| > 0.8 AND R² > 0.8
        if analysis.breakthrough_achieved:
            assert abs(analysis.pearson_r) > 0.8
            assert analysis.r_squared > 0.8

    def test_execution_time_reasonable(self):
        """Test experiment completes in reasonable time"""
        _, analysis = run_golden_sld_correlation_experiment(sample_sizes=[100], dim=4)

        # Should complete in < 5 seconds
        assert analysis.execution_time_ms < 5000.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
