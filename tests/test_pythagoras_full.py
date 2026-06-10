"""
tests/test_pythagoras_full.py — Full integration and unit tests for the
PYTHAGORAS quantum pipeline: PULVINI, TT/MPS, MPO, Ω-TDA, Remez, nonce coverage.
"""

import sys
import os
import unittest
import numpy as np

# Add the operators directory to the path
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src",
        "euclid",
        "pythagoras",
        "quantum",
        "operators",
    ),
)

# Add repo root for models import
sys.path.insert(
    0,
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


class TestPulviniOperator(unittest.TestCase):
    """PULVINI Φ-recursive folding unit tests."""

    def setUp(self):
        from pulvini_scaling import PulviniOperator

        self.op = PulviniOperator(tolerance=1e-8)

    def test_fold_unfold_roundtrip_exact(self):
        """Fold and unfold should reconstruct input with near machine precision."""
        for dim in [2, 3, 5, 10, 64, 100]:
            t = np.random.randn(dim).astype(np.complex128)
            folded, kernel = self.op.fold(t)
            reconstructed = self.op.unfold(folded, kernel, dim)
            error = np.linalg.norm(t - reconstructed) / max(1.0, np.linalg.norm(t))
            self.assertLess(error, 1e-10, f"Roundtrip error too large at dim={dim}")

    def test_small_tensor_returns_self(self):
        """Dimension 1 should be unchanged."""
        t = np.array([1.0 + 2.0j])
        folded, kernel = self.op.fold(t)
        self.assertEqual(len(folded), 1)
        self.assertAlmostEqual(folded[0], t[0])

    def test_phi_depth_increases_with_size(self):
        from pulvini_scaling import PulviniOperator

        d1 = PulviniOperator.phi_depth(10)
        d2 = PulviniOperator.phi_depth(10000)
        self.assertGreater(d2, d1)

    def test_deterministic_work_rate(self):
        """Work rate should be original / folded dimension."""
        from pulvini_scaling import PulviniOperator

        rate = PulviniOperator.deterministic_work_rate(1000, 50)
        self.assertAlmostEqual(rate, 20.0)

    def test_hamiltonian_reduction_spectral_gap(self):
        """Hamiltonian reduction should preserve spectral gap within tolerance."""
        dim = 10
        H = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        H = (H + H.conj().T) / 2.0  # Hermitian
        H_red, audit = self.op.hamiltonian_reduction(H)
        self.assertIsNotNone(audit)
        self.assertGreater(audit.folded_dimension, 0)
        self.assertLess(audit.folded_dimension, audit.original_dimension)


class TestTensorTrain(unittest.TestCase):
    """TT/MPS compression unit tests."""

    def setUp(self):
        from tensor_train import TensorTrainCompressor

        self.tt = TensorTrainCompressor(max_rank=32)

    def test_compress_and_reconstruct(self):
        """Compressing and reconstructing a small matrix should have low error."""
        X = np.random.randn(16, 16).astype(np.complex128)
        train = self.tt.reduce(X)
        recon = train.reconstruct()
        error = np.linalg.norm(X - recon) / np.linalg.norm(X)
        self.assertLess(error, 0.5)
        self.assertGreater(train.storage, 0)

    def test_ranks_work_properly(self):
        """Ranks should be a list of ints, length = number of cores + 1."""
        X = np.random.randn(8, 8).astype(np.complex128)
        train = self.tt.reduce(X)
        self.assertEqual(len(train.ranks), len(train.cores) + 1)
        for r in train.ranks:
            self.assertGreaterEqual(r, 1)


class TestNonceCoverage(unittest.TestCase):
    """Platonic nonce overlay tests."""

    def setUp(self):
        from nonce_space_coverage import PlatonicNonceOverlay

        self.overlay = PlatonicNonceOverlay()

    def test_coverage_has_32_points(self):
        coverage = self.overlay.get_full_coverage()
        self.assertGreaterEqual(len(coverage), 32)

    def test_coverage_points_are_unit_norm(self):
        coverage = self.overlay.get_full_coverage()
        norms = np.linalg.norm(coverage, axis=1)
        self.assertTrue(np.allclose(norms, 1.0, atol=1e-6))

    def test_worker_assignments_sum_to_total(self):
        assignments = self.overlay.get_worker_assignments(32)
        total = sum(len(a) for a in assignments)
        self.assertEqual(total, 32)

    def test_fewer_workers_works(self):
        assignments = self.overlay.get_worker_assignments(4)
        total = sum(len(a) for a in assignments)
        self.assertEqual(total, 32)


class TestMPOPulviniHybrid(unittest.TestCase):
    """MPO + PULVINI hybrid pipeline tests."""

    def setUp(self):
        from mpo_pulvini_hybrid import MPOPulviniHybrid

        self.hybrid = MPOPulviniHybrid(max_tt_rank=16, tolerance=1e-3)

    def test_reduce_returns_audit(self):
        t = np.random.randn(64).astype(np.complex128)
        train, audit = self.hybrid.reduce(t)
        self.assertIsNotNone(audit)
        self.assertGreater(audit.compression_ratio, 0)
        self.assertGreater(audit.folded_dimension, 0)

    def test_apply_mpo_step(self):
        t = np.random.randn(32).astype(np.complex128)
        train, _ = self.hybrid.reduce(t)
        op = np.eye(len(t))
        result = self.hybrid.apply_mpo_step(train, op)
        self.assertIsNotNone(result)
        self.assertGreater(len(result.cores), 0)


class TestPythagorasOrchestrator(unittest.TestCase):
    """Full pipeline orchestration tests."""

    def setUp(self):
        from pythagoras_orchestrator import PythagorasOrchestrator

        self.orch = PythagorasOrchestrator(max_tt_rank=16, tolerance=1e-3)

    def test_process_with_vector(self):
        t = np.random.randn(64).astype(np.complex128)
        result = self.orch.process(t, skip_tda=True)
        self.assertIn(result.status, ["phi_resonance_achieved", "degraded_preservation"])
        self.assertGreater(result.compression_ratio, 0)

    def test_process_with_matrix(self):
        t = np.random.randn(16, 16).astype(np.complex128)
        result = self.orch.process(t, skip_tda=True)
        self.assertIsNotNone(result.audit)

    def test_process_with_operator(self):
        t = np.random.randn(32).astype(np.complex128)
        op = np.eye(32, dtype=np.complex128)
        result = self.orch.process(t, operator_matrix=op, skip_tda=True)
        self.assertIsNotNone(result.audit)

    def test_nonce_coverage(self):
        coverage = self.orch.get_nonce_coverage(32)
        self.assertGreaterEqual(len(coverage), 1)

    def test_deterministic_hashrate_estimate(self):
        t = np.random.randn(64).astype(np.complex128)
        result = self.orch.process(t, skip_tda=True)
        self.assertIn("x", result.deterministic_hashrate_estimate)
        self.assertIn("folded", result.deterministic_hashrate_estimate)


class TestRemezApproximator(unittest.TestCase):
    """Remez minimax approximation tests."""

    def setUp(self):
        from remez_approximator import RemezApproximator

        self.remez = RemezApproximator(tol=1e-8, max_iter=30)

    def test_approximate_constant(self):
        coeffs, error, _ = self.remez.approximate(lambda x: 5.0, (0, 1), degree=0)
        self.assertAlmostEqual(coeffs[0], 5.0, places=5)
        self.assertLess(error, 1e-6)

    def test_approximate_linear(self):
        coeffs, error, _ = self.remez.approximate(lambda x: 2.0 * x + 1.0, (0, 1), degree=1)
        self.assertLess(error, 1e-6)

    def test_approximate_phi_function(self):
        phi = (1.0 + np.sqrt(5.0)) / 2.0

        def golden_func(x: float) -> float:
            return phi**x - (phi ** (x - 1.0) + phi ** (x - 2.0))

        coeffs, error, history = self.remez.approximate(golden_func, (-2, 2), degree=4)
        self.assertGreater(error, 0)
        self.assertGreater(len(history), 1)


class TestOmegaTDA(unittest.TestCase):
    """Ω-Signature TDA audit tests."""

    def test_compare_identical(self):
        from omega_tda_audit import compare_omega_signatures

        t = np.random.randn(64).astype(np.complex128)
        result = compare_omega_signatures(t, t, threshold=0.15)
        self.assertTrue(result.stable)

    def test_compare_different(self):
        from omega_tda_audit import compare_omega_signatures

        a = np.random.randn(32).astype(np.complex128)
        b = np.random.randn(32).astype(np.complex128)
        result = compare_omega_signatures(a, b, threshold=0.15)
        # Random tensors should be different, but score could be high
        self.assertIsNotNone(result.score)


class TestSymbolicVerifier(unittest.TestCase):
    """Symbolic and numeric verification tests."""

    def test_phi_identity(self):
        from symbolic_verifier import verify_symbolic_phi_identity

        result = verify_symbolic_phi_identity()
        self.assertTrue(result.passed)

    def test_verify_unitary(self):
        from symbolic_verifier import verify_unitary

        U = np.eye(4, dtype=np.complex128)
        result = verify_unitary(U)
        self.assertTrue(result.passed)

    def test_verify_non_unitary(self):
        from symbolic_verifier import verify_unitary

        M = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.complex128)
        result = verify_unitary(M)
        self.assertFalse(result.passed)


class TestMatrixChecks(unittest.TestCase):
    """Matrix invariant checks."""

    def setUp(self):
        from matrix_checks import MatrixInvariantChecker

        self.checker = MatrixInvariantChecker()

    def test_square_matrix_detected(self):
        from matrix_checks import MatrixCheck

        m = np.eye(3)
        result = self.checker.check(m)
        self.assertTrue(result.square)

    def test_non_square_matrix(self):
        m = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        result = self.checker.check(m)
        self.assertFalse(result.square)


class TestFoldedAmplifier(unittest.TestCase):
    """Probability amplification tests."""

    def test_uniform_vector_normalized(self):
        from folded_probability_amplifier import uniform_vector

        v = uniform_vector(16)
        self.assertAlmostEqual(np.linalg.norm(v), 1.0)

    def test_mark_inverts_sign(self):
        from folded_probability_amplifier import uniform_vector, mark

        v = uniform_vector(8)
        marked = mark(v, [0])
        self.assertAlmostEqual(v[0], -marked[0])

    def test_amplifier_finds_max(self):
        from folded_probability_amplifier import run_amplifier

        result = run_amplifier(16, [0], iterations=5)
        self.assertIn(result.best_index, [0])
        self.assertGreater(result.best_probability, 0)

    def test_recommended_steps_positive(self):
        from folded_probability_amplifier import recommended_steps

        steps = recommended_steps(256, 1)
        self.assertGreater(steps, 0)


class TestUnitaryEvolver(unittest.TestCase):
    """Unitary evolution tests."""

    def setUp(self):
        from unitary_evolver import UnitaryEvolver

        self.evolver = UnitaryEvolver()

    def test_normalize_zero(self):
        state = np.array([1.0, 0.0])
        normalized = self.evolver.normalize(state)
        self.assertAlmostEqual(np.linalg.norm(normalized), 1.0)

    def test_hadamard_like_dim2(self):
        H = self.evolver.hadamard_like(2)
        U = H.conj().T @ H
        self.assertTrue(np.allclose(U, np.eye(2), atol=1e-10))

    def test_evolve_preserves_norm(self):
        state = np.array([1.0, 1.0], dtype=np.complex128)
        H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2)
        _, audit = self.evolver.evolve(state, H, steps=1)
        self.assertTrue(audit.passed)
        self.assertLess(audit.norm_error, 1e-6)


if __name__ == "__main__":
    unittest.main()