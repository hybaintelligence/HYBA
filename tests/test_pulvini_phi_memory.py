from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

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

    def test_stream_compression_tracks_working_set_ratio(self) -> None:
        chunks = [np.arange(32, dtype=np.float64), np.arange(32, 96, dtype=np.float64)]
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=1)
        result = engine.compress_stream(chunks)

        self.assertEqual(2, result.chunks)
        self.assertEqual(96, result.input_elements)
        self.assertLess(result.folded_elements, result.input_elements)
        self.assertGreater(result.avg_working_set_compression_ratio, 1.0)


if __name__ == "__main__":
    unittest.main()
