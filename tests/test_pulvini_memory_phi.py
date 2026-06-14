from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_manifold import PulviniManifold  # noqa: E402
from pythia_mining.pulvini_memory import HebbianMemoryKernel  # noqa: E402
from pythia_mining.pulvini_overlay import ADJACENCY_MAP  # noqa: E402
from pythia_mining.pulvini_phi_empirical import measure_phi_acceptance  # noqa: E402


class PulviniMemoryAndPhiTests(unittest.TestCase):
    def test_memory_kernel_detects_persistent_synaptic_history(self) -> None:
        kernel = HebbianMemoryKernel(window=8, decay=0.75)
        self.assertTrue(kernel.certificate().markovian)
        kernel.record_path(num_nodes=32, path=[0, 20, 25, 30, 31], reward=1.0)
        cert = kernel.certificate()
        self.assertFalse(cert.markovian)
        self.assertGreater(cert.kernel_norm, 0.0)
        self.assertEqual(1, cert.memory_events)

    def test_phi_sample_reports_one_measured_datapoint(self) -> None:
        manifold = PulviniManifold(ADJACENCY_MAP)
        result = measure_phi_acceptance(
            manifold, range(512), threshold=0.5, job_id="sample-job"
        )
        self.assertEqual(512, result.sample_size)
        self.assertGreaterEqual(result.acceptance_ratio, 0.0)
        self.assertLessEqual(result.acceptance_ratio, 1.0)
        self.assertEqual(0.5, result.baseline_uniform_ratio)
        self.assertIn("measured_datapoint", result.claim)


if __name__ == "__main__":
    unittest.main()
