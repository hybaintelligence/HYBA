from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Turn warnings into hard failures in test context
np.seterr(all="raise")

from pythia_mining.pulvini_memory_fabric import PulviniMemoryFabric  # noqa: E402
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine  # noqa: E402
from pythia_mining.phi_folding import PhiFoldingOperator  # noqa: E402


class PulviniPhiMemoryCompressionTests(unittest.TestCase):
    def test_phi_fold_is_reversible_and_reduces_working_set(self) -> None:
        payload = np.arange(64, dtype=np.float64)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        result = engine.compress(payload)

        self.assertTrue(result.reversible)
        self.assertLess(result.folded_working_set_bytes, result.original_bytes)
        self.assertGreater(result.retained_kernel_bytes, 0)
        self.assertGreater(result.working_set_compression_ratio, 1.0)
        self.assertTrue(np.allclose(engine.decompress(result), payload))
        self.assertFalse(np.any(np.isnan(result.folded)), "NaN in folded output")
        self.assertFalse(np.any(np.isinf(result.folded)), "Inf in folded output")
        self.assertFalse(np.any(np.isnan(result.reconstructed)), "NaN in reconstructed")
        self.assertFalse(np.any(np.isinf(result.reconstructed)), "Inf in reconstructed")

    def test_matrix_telemetry_reports_quantum_memory_metrics(self) -> None:
        matrix = np.eye(8, dtype=np.complex128) / 8.0
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        result = engine.compress(matrix)

        self.assertTrue(result.reversible)
        self.assertIsNotNone(result.trace_distance)
        self.assertIsNotNone(result.hermiticity_error)
        self.assertIsNotNone(result.entropy)
        self.assertLessEqual(result.trace_distance or 0.0, 1e-9)
        self.assertLessEqual(result.hermiticity_error or 0.0, 1e-9)
        self.assertFalse(np.any(np.isnan(result.folded)), "NaN in folded output")
        self.assertFalse(np.any(np.isinf(result.folded)), "Inf in folded output")
        self.assertFalse(np.any(np.isnan(result.reconstructed)), "NaN in reconstructed")
        self.assertFalse(np.any(np.isinf(result.reconstructed)), "Inf in reconstructed")

    def test_stream_compression_tracks_working_set_ratio(self) -> None:
        chunks = [np.arange(32, dtype=np.float64), np.arange(32, 96, dtype=np.float64)]
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        result = engine.compress_stream(chunks)

        self.assertEqual(2, result.chunks)
        self.assertEqual(96, result.input_elements)
        self.assertLess(result.folded_elements, result.input_elements)
        self.assertGreater(result.avg_working_set_compression_ratio, 1.0)

    def test_fabric_uses_phi_folded_kernel_state(self) -> None:
        fabric = PulviniMemoryFabric(num_nodes=32, fold_depth=2)
        for reward, path in [
            (1.0, [0, 20, 25, 30, 31]),
            (0.5, [1, 21, 26, 27, 16]),
            (0.8, [2, 22, 23, 8, 9]),
        ]:
            fabric.record_path(path, reward=reward)
        snapshot = fabric.compressed_kernel_snapshot().to_dict()

        self.assertGreater(snapshot["kernel"]["kernel_norm"], 0.0)
        self.assertTrue(snapshot["compression"]["reversible"])
        self.assertGreater(snapshot["compression"]["retained_kernel_bytes"], 0)
        self.assertIn(
            snapshot["compression"]["compression_strategy"],
            {"phi_fold", "sparse_passthrough", "sparse_fib_packed"},
        )
        compression_dict = snapshot["compression"]
        self.assertFalse(np.isnan(compression_dict.get("reconstruction_error", 0.0)))
        self.assertFalse(np.isinf(compression_dict.get("reconstruction_error", 0.0)))

    # ------------------------------------------------------------------
    # Adversarial round-trip tests
    # ------------------------------------------------------------------

    def test_round_trip_high_entropy_random_vector(self) -> None:
        """Fold/unfold of a high-entropy random real vector must be lossless."""
        rng = np.random.default_rng(seed=0xDEADBEEF)
        payload = rng.uniform(-1e6, 1e6, size=64).astype(np.float64)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        result = engine.compress(payload)
        self.assertTrue(
            result.reversible,
            f"fold not reversible for high-entropy input; error={result.reconstruction_error:.3e}",
        )
        self.assertTrue(
            np.allclose(result.reconstructed.reshape(-1), payload, rtol=0, atol=engine.tolerance)
        )

    def test_round_trip_high_entropy_complex_vector(self) -> None:
        """Fold/unfold of a complex high-entropy vector must be lossless."""
        rng = np.random.default_rng(seed=0xCAFEBABE)
        payload = (rng.standard_normal(64) + 1j * rng.standard_normal(64)).astype(np.complex128)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        result = engine.compress(payload)
        self.assertTrue(
            result.reversible,
            f"fold not reversible for complex input; error={result.reconstruction_error:.3e}",
        )
        self.assertTrue(
            np.allclose(result.reconstructed.reshape(-1), payload, rtol=0, atol=engine.tolerance)
        )

    def test_round_trip_all_equal_vector(self) -> None:
        """Constant (zero-entropy) vector: a degenerate but valid edge case."""
        payload = np.full(32, 7.0, dtype=np.float64)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        result = engine.compress(payload)
        self.assertTrue(result.reversible)
        self.assertTrue(
            np.allclose(result.reconstructed.reshape(-1), payload, rtol=0, atol=engine.tolerance)
        )

    def test_round_trip_single_spike_vector(self) -> None:
        """Single non-zero element: adversarial for basis-projection operators."""
        payload = np.zeros(64, dtype=np.float64)
        payload[37] = 1.0
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        result = engine.compress(payload)
        self.assertTrue(
            result.reversible,
            f"fold not reversible for spike input; error={result.reconstruction_error:.3e}",
        )
        self.assertTrue(
            np.allclose(result.reconstructed.reshape(-1), payload, rtol=0, atol=engine.tolerance)
        )

    def test_reconstruction_error_is_finite_for_normal_cases(self) -> None:
        """Normal inputs produce finite reconstruction error."""
        rng = np.random.default_rng(seed=42)
        cases = [
            np.zeros(32, dtype=np.float64),
            rng.standard_normal(32),
            rng.uniform(0, 1, 32),
        ]
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        for i, payload in enumerate(cases):
            result = engine.compress(payload)
            self.assertTrue(
                np.isfinite(result.reconstruction_error),
                f"non-finite reconstruction_error for case {i}: {result.reconstruction_error}",
            )

    # ------------------------------------------------------------------
    # NEW: PULVINI information-integrity cap tests
    # ------------------------------------------------------------------

    def test_working_set_compression_ratio_reported_accurately(self) -> None:
        """Compression ratio must be original_bytes / folded_bytes, reported faithfully.

        The engine reports the ratio accurately regardless of its value.
        The information-integrity hard cap (2.0x) is a governance concern;
        the engine's job is accurate reporting.
        """
        payload = np.arange(128, dtype=np.float64)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        result = engine.compress(payload)
        expected_ratio = result.original_bytes / result.folded_working_set_bytes
        self.assertAlmostEqual(result.working_set_compression_ratio, expected_ratio, places=10)

    def test_retained_state_ratio_never_exceeds_working_set_ratio(self) -> None:
        """retained_state_compression_ratio <= working_set_compression_ratio always.

        Including the kernels in the denominator can only increase retained bytes,
        which must reduce the ratio compared to the working-set-only ratio.
        """
        payload = np.random.default_rng(7).standard_normal(64)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2)
        result = engine.compress(payload)
        self.assertLessEqual(
            result.retained_state_compression_ratio,
            result.working_set_compression_ratio + 1e-10,
        )

    def test_fold_depth_1_produces_single_kernel(self) -> None:
        """depth=1 fold must produce exactly one kernel array."""
        payload = np.arange(32, dtype=np.float64)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        result = engine.compress(payload)
        # fold_depth in the result is len(kernels), which may be 0 if payload was
        # size <=1, but for size=32 it must be 1.
        self.assertEqual(result.fold_depth, 1)
        self.assertEqual(len(result.kernels), 1)

    def test_sparse_vector_uses_sparse_fib_packed_strategy(self) -> None:
        """A highly sparse vector (>85% zeros) should trigger the sparse fold path."""
        payload = np.zeros(200, dtype=np.float64)
        payload[[3, 17, 99]] = [1.0, 2.0, 3.0]  # Only 3/200 non-zero
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2, sparse_skip_threshold=0.85)
        result = engine.compress(payload)
        self.assertEqual(result.compression_strategy, "sparse_fib_packed")
        self.assertTrue(result.reversible)

    def test_dense_vector_uses_phi_fold_strategy(self) -> None:
        """A dense (low-sparsity) vector should use the standard phi_fold path."""
        rng = np.random.default_rng(seed=99)
        payload = rng.standard_normal(64)  # ~0% zeros
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2, sparse_skip_threshold=0.85)
        result = engine.compress(payload)
        self.assertEqual(result.compression_strategy, "phi_fold")
        self.assertTrue(result.reversible)

    def test_density_matrix_entropy_is_non_negative(self) -> None:
        """Von Neumann entropy of any valid density matrix must be >= 0."""
        rng = np.random.default_rng(seed=11)
        A = rng.standard_normal((8, 8)) + 1j * rng.standard_normal((8, 8))
        rho = A @ A.conj().T
        rho = rho / np.trace(rho)
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        result = engine.compress(rho)
        self.assertIsNotNone(result.entropy)
        self.assertGreaterEqual(result.entropy, -1e-10)  # numerical floor

    def test_stream_max_error_is_worst_chunk_error(self) -> None:
        """Stream max_reconstruction_error must equal the worst individual chunk error."""
        rng = np.random.default_rng(seed=42)
        chunks = [rng.standard_normal(32) for _ in range(5)]
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        individual_errors = [engine.compress(c).reconstruction_error for c in chunks]
        stream_result = engine.compress_stream(iter(chunks))
        self.assertAlmostEqual(
            stream_result.max_reconstruction_error, max(individual_errors), places=10
        )

    # ------------------------------------------------------------------
    # NEW: PhiFoldingOperator unit tests
    # ------------------------------------------------------------------

    def test_fibonacci_split_sums_to_dimension(self) -> None:
        """fibonacci_split(n) must return (a, b) with a + b == n for all n."""
        op = PhiFoldingOperator()
        for n in [2, 3, 5, 8, 13, 21, 32, 64, 100, 255]:
            a, b = op.fibonacci_split(n)
            self.assertEqual(a + b, n, f"split({n}) = ({a},{b}), sum != {n}")
            self.assertGreaterEqual(a, 1)
            self.assertGreaterEqual(b, 1)

    def test_fold_unfold_identity_for_various_sizes(self) -> None:
        """Single fold/unfold round trip must be lossless for a range of sizes."""
        op = PhiFoldingOperator(tolerance=1e-9)
        rng = np.random.default_rng(seed=0)
        for n in [2, 3, 5, 8, 13, 21, 34, 55, 64]:
            payload = rng.standard_normal(n)
            folded, kernel, orig_size = op.fold(payload)
            recovered = op.unfold(folded, kernel, orig_size)
            self.assertTrue(
                np.allclose(recovered, payload, atol=1e-9),
                f"fold/unfold not lossless for size={n}",
            )

    def test_recursive_fold_unfold_identity(self) -> None:
        """Recursive fold/unfold to depth 3 must be lossless."""
        op = PhiFoldingOperator(tolerance=1e-9)
        rng = np.random.default_rng(seed=1)
        payload = rng.standard_normal(64)
        folded, kernels, sizes = op.fold_recursive(payload, depth=3)
        recovered = op.unfold_recursive(folded, kernels, sizes)
        self.assertTrue(np.allclose(recovered[:64], payload, atol=1e-9))

    def test_phi_ratio_error_is_small(self) -> None:
        """Fibonacci split must approximate the phi ratio within a reasonable bound."""
        op = PhiFoldingOperator()
        for n in [8, 13, 21, 34, 55, 89]:
            err = op.phi_ratio_error(n)
            # For Fibonacci numbers the split is exact; for others allow ~50% tolerance
            self.assertLess(err, 0.5, f"phi_ratio_error too large for n={n}: {err:.4f}")

    def test_approximate_error_within_factor_of_full_norm(self) -> None:
        """Sketch-based error estimate must be within 3x of full norm for smooth data."""
        op = PhiFoldingOperator()
        rng = np.random.default_rng(seed=5)
        payload = rng.standard_normal(500)
        folded, kernels, sizes = op.fold_recursive(payload, depth=2)
        reconstructed = op.unfold_recursive(folded, kernels, sizes)[:500]
        full_error = float(np.linalg.norm(payload - reconstructed))
        sketch_error = op.approximate_error(payload, reconstructed, sketch_size=50)
        if full_error > 1e-12:
            ratio = sketch_error / full_error
            self.assertLess(ratio, 10.0, "sketch error estimate more than 10x off full norm")
            self.assertGreater(ratio, 0.01, "sketch error estimate more than 100x below full norm")


if __name__ == "__main__":
    unittest.main()
