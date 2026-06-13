import os
import sys
import unittest

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "python_backend"))
sys.path.insert(0, os.path.join(ROOT, "implementation_patches"))

from pythia_mining.phi_config import PHI, DEFAULT_ENSEMBLE_MEMORY_LIMIT  # noqa: E402
from pythia_mining.phi_folding import PhiFoldingOperator  # noqa: E402
from pythia_mining.phi_scaling_engine import PhiScaledEnsemble  # noqa: E402
from pythia_mining.pulvini_memory_fabric import PulviniMemoryFabric  # noqa: E402
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine  # noqa: E402


class PhiConfigAndMemoryRefactorTests(unittest.TestCase):
    def test_shared_folding_operator_round_trips_multiple_dimensions(self) -> None:
        operator = PhiFoldingOperator(tolerance=1e-10)
        for dimension in range(2, 65):
            payload = np.linspace(-1.0, 1.0, dimension)
            folded, kernels, sizes = operator.fold_recursive(payload, depth=3)
            restored = operator.unfold_recursive(folded, kernels, sizes)[:dimension]
            self.assertTrue(np.allclose(payload, restored, atol=1e-9), dimension)
            self.assertLess(operator.phi_ratio_error(dimension), PHI)

    def test_ensemble_memory_is_bounded_and_thresholds_are_configurable(self) -> None:
        engine = PhiScaledEnsemble({"memory_limit": 3, "low_variance_threshold": 0.01, "high_variance_threshold": 0.03})
        predictions = {"a": {"score": 0.1}, "b": {"score": 0.9}}
        indicators = {"lane": {"x": 1.0, "y": PHI, "z": PHI * PHI}}
        for _ in range(8):
            engine.predict_with_phi_scaling(predictions, indicators)
        self.assertEqual(len(engine.memory), 3)
        self.assertLessEqual(DEFAULT_ENSEMBLE_MEMORY_LIMIT, 4096)

    def test_sparse_payload_uses_passthrough_without_losing_reversibility(self) -> None:
        payload = np.zeros((8, 8), dtype=np.float64)
        payload[0, 0] = 42.0
        engine = PulviniPhiMemoryCompressionEngine(fold_depth=2, sparse_skip_threshold=0.80)
        result = engine.compress(payload)
        self.assertEqual(result.compression_strategy, "sparse_passthrough")
        self.assertTrue(result.sparse_optimized)
        self.assertTrue(result.reversible)
        self.assertTrue(np.array_equal(engine.decompress(result), payload))

    def test_memory_fabric_accepts_injected_kernel_and_tolerance(self) -> None:
        class KernelStub:
            def __init__(self) -> None:
                self.delta = np.eye(4)

            def record_path(self, num_nodes, path, reward):
                pass

            def record_delta(self, delta_matrix):
                self.delta = np.asarray(delta_matrix)

            def kernel_matrix(self):
                return self.delta

            def certificate(self):
                class Cert:
                    def to_dict(self):
                        return {"stub": True}

                return Cert()

        fabric = PulviniMemoryFabric(num_nodes=4, kernel=KernelStub(), fold_depth=1, tolerance=1e-6)
        snapshot = fabric.compressed_kernel_snapshot().to_dict()
        self.assertEqual(snapshot["kernel"], {"stub": True})
        self.assertLessEqual(snapshot["compression"]["reconstruction_error"], 1e-6)


if __name__ == "__main__":
    unittest.main()
