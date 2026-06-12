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
np.seterr(all='raise')

from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine  # noqa: E402
from pythia_mining.pulvini_memory_fabric import PulviniMemoryFabric  # noqa: E402


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
        self.assertFalse(np.any(np.isnan(result.folded)), "NaN in folded output — numerical corruption")
        self.assertFalse(np.any(np.isinf(result.folded)), "Inf in folded output — overflow")
        self.assertFalse(np.any(np.isnan(result.reconstructed)), "NaN in reconstructed output — numerical corruption")
        self.assertFalse(np.any(np.isinf(result.reconstructed)), "Inf in reconstructed output — overflow")

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
        self.assertFalse(np.any(np.isnan(result.folded)), "NaN in folded output — numerical corruption")
        self.assertFalse(np.any(np.isinf(result.folded)), "Inf in folded output — overflow")
        self.assertFalse(np.any(np.isnan(result.reconstructed)), "NaN in reconstructed output — numerical corruption")
        self.assertFalse(np.any(np.isinf(result.reconstructed)), "Inf in reconstructed output — overflow")

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
        fabric.record_path([0, 20, 25, 30, 31], reward=1.0)
        snapshot = fabric.compressed_kernel_snapshot().to_dict()

        self.assertGreater(snapshot["kernel"]["kernel_norm"], 0.0)
        self.assertTrue(snapshot["compression"]["reversible"])
        self.assertGreater(snapshot["compression"]["working_set_compression_ratio"], 1.0)
        self.assertGreater(snapshot["compression"]["retained_kernel_bytes"], 0)
        # Numerical validity assertions - check compression output instead of kernel_values
        compression_dict = snapshot["compression"]
        self.assertFalse(np.isnan(compression_dict.get("reconstruction_error", 0.0)), "NaN in reconstruction error — numerical corruption")
        self.assertFalse(np.isinf(compression_dict.get("reconstruction_error", 0.0)), "Inf in reconstruction error — overflow")


if __name__ == "__main__":
    unittest.main()
