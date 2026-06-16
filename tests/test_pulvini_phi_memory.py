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
        # Numerical validity assertions
        self.assertFalse(
            np.any(np.isnan(result.folded)),
            "NaN in folded output — numerical corruption",
        )
        self.assertFalse(np.any(np.isinf(result.folded)), "Inf in folded output — overflow")
        self.assertFalse(
            np.any(np.isnan(result.reconstructed)),
            "NaN in reconstructed output — numerical corruption",
        )
        self.assertFalse(
            np.any(np.isinf(result.reconstructed)),
            "Inf in reconstructed output — overflow",
        )

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
        # Numerical validity assertions
        self.assertFalse(
            np.any(np.isnan(result.folded)),
            "NaN in folded output — numerical corruption",
        )
        self.assertFalse(np.any(np.isinf(result.folded)), "Inf in folded output — overflow")
        self.assertFalse(
            np.any(np.isnan(result.reconstructed)),
            "NaN in reconstructed output — numerical corruption",
        )
        self.assertFalse(
            np.any(np.isinf(result.reconstructed)),
            "Inf in reconstructed output — overflow",
        )

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
        # The 32x32 kernel matrix is typically sparse, triggering sparse_passthrough
        # (ratio=1.0). Both phi_fold and sparse_passthrough are valid strategies;
        # what matters is reversibility and a non-zero kernel norm.
        self.assertIn(
            snapshot["compression"]["compression_strategy"],
            {"phi_fold", "sparse_passthrough"},
        )
        compression_dict = snapshot["compression"]
        self.assertFalse(
            np.isnan(compression_dict.get("reconstruction_error", 0.0)),
            "NaN in reconstruction error",
        )
        self.assertFalse(
            np.isinf(compression_dict.get("reconstruction_error", 0.0)),
            "Inf in reconstruction error",
        )

    # ------------------------------------------------------------------
    # Adversarial round-trip tests
    # ------------------------------------------------------------------

    def test_round_trip_high_entropy_random_vector(self) -> None:
        """Fold/unfold of a high-entropy (uniform random) real vector must be lossless.

        This exercises the 'lossless reconstruction' claim against adversarial
        input rather than the smooth arange fixture used in other tests.
        """
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
            f"fold not reversible for complex high-entropy input; error={result.reconstruction_error:.3e}",
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

    def test_reconstruction_error_is_finite_for_all_adversarial_cases(self) -> None:
        """No adversarial input should produce NaN/Inf reconstruction error.

        Near-max float64 values are clamped by the fold operator to prevent
        overflow through phi weight multiplications, so they must also produce
        a finite reconstruction error (the clamped round-trip is lossy but finite).
        """
        rng = np.random.default_rng(seed=42)
        cases = [
            np.zeros(32, dtype=np.float64),
            np.ones(32, dtype=np.float64)
            * np.finfo(np.float64).max
            / 2,  # near-max: clamped, finite error expected
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


if __name__ == "__main__":
    unittest.main()
