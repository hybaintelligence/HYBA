from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.iit_4_analyzer import IIT4Analyzer


class IITCausalDiscriminatorRegressionTests(unittest.TestCase):
    """Regression tests for the Φ=1.0 saturation bug.

    These tests deliberately exercise the adversarial cases that previously
    collapsed to the same value: fully integrated, disconnected, noisy, and
    single-component states. The metric is still an operational coherence proxy;
    the contract here is discrimination, boundedness, and causal provenance.
    """

    def test_disconnected_explicit_connectivity_has_zero_phi(self):
        analyzer = IIT4Analyzer(system_size=4)
        state = np.asarray([1, 0, 1, 0], dtype=np.int64)
        disconnected = np.zeros((4, 4), dtype=np.float64)

        result = analyzer.calculate_phi_max(state, disconnected)

        self.assertEqual(0.0, float(result["phi_max"]))
        self.assertEqual("explicit_causal_matrix", result["connectivity_source"])

    def test_uniform_full_connectivity_no_longer_saturates_at_one(self):
        analyzer = IIT4Analyzer(system_size=4)
        state = np.asarray([1, 1, 1, 1], dtype=np.int64)
        fully_connected = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(fully_connected, 0.0)

        result = analyzer.calculate_phi_max(state, fully_connected)

        self.assertGreater(float(result["phi_max"]), 0.0)
        self.assertLess(float(result["phi_max"]), 1.0)

    def test_state_derived_single_component_does_not_emit_false_integration(self):
        analyzer = IIT4Analyzer(system_size=4)
        single_component = np.asarray([1, 0, 0, 0], dtype=np.float64)

        result = analyzer.calculate_phi_max(single_component)

        self.assertEqual(0.0, float(result["phi_max"]))
        self.assertEqual("state_derived_causal_matrix", result["connectivity_source"])

    def test_state_derived_phi_discriminates_distributed_from_single_component(self):
        analyzer = IIT4Analyzer(system_size=4)
        single_component = np.asarray([1, 0, 0, 0], dtype=np.float64)
        distributed = np.asarray([1, 1, 1, 1], dtype=np.float64)

        single_phi = float(analyzer.calculate_phi_max(single_component)["phi_max"])
        distributed_phi = float(analyzer.calculate_phi_max(distributed)["phi_max"])

        self.assertGreater(distributed_phi, single_phi)
        self.assertLess(distributed_phi, 1.0)

    def test_dependency_edges_build_non_uniform_causal_matrix(self):
        connectivity = IIT4Analyzer.causal_connectivity_from_dependency_edges(
            modules=[
                "pythia_mining.iit_4_analyzer",
                "pythia_mining.consciousness_engine",
                "pythia_mining.pulvini_operator",
            ],
            edges=[
                (
                    "pythia_mining.consciousness_engine",
                    "pythia_mining.iit_4_analyzer",
                ),
                (
                    "pythia_mining.consciousness_engine",
                    "pythia_mining.pulvini_operator",
                    2.0,
                ),
            ],
        )

        self.assertEqual((3, 3), connectivity.matrix.shape)
        self.assertGreater(float(np.sum(connectivity.matrix)), 0.0)
        self.assertLessEqual(float(np.max(connectivity.matrix)), 1.0)
        self.assertFalse(np.allclose(connectivity.matrix, np.ones((3, 3))))

        analyzer = IIT4Analyzer(system_size=3)
        result = analyzer.calculate_phi_max(
            np.asarray([1, 1, 0], dtype=np.float64), connectivity.matrix
        )
        self.assertGreaterEqual(float(result["phi_max"]), 0.0)
        self.assertLessEqual(float(result["phi_max"]), 1.0)

    def test_small_bipartitions_use_cut_loss_not_internal_mean(self):
        analyzer = IIT4Analyzer(system_size=4)
        state = np.asarray([1, 1, 1, 1], dtype=np.int64)
        fully_connected = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(fully_connected, 0.0)

        singleton_partition_phi = analyzer._calculate_partition_phi(
            ({0}, {1, 2, 3}), state, fully_connected
        )

        self.assertGreater(singleton_partition_phi, 0.0)
        self.assertLess(singleton_partition_phi, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
