import os
import sys
import unittest

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "python_backend"))

from pythia_mining.ai_optimizer_meta import MetaLearningOptimizer  # noqa: E402
from pythia_mining.pulvini_memory_fabric import EvolvingMemoryFabric  # noqa: E402


class MetaLearningOptimizerTests(unittest.TestCase):
    def test_accepted_share_increases_strategy_weight_from_observed_metrics(self):
        optimizer = MetaLearningOptimizer(
            learning_rate=0.1, initial_strategies=["phi_scaled"], rng_seed=7
        )
        before = optimizer.strategy_weights["phi_scaled"]

        event = optimizer.update_from_outcome(
            strategy_id="phi_scaled",
            accepted=True,
            phi_resonance=0.25,
            thermal_cost=0.5,
            solve_time=0.2,
        )

        self.assertGreater(optimizer.strategy_weights["phi_scaled"], before)
        self.assertEqual("phi_scaled", event["strategy"])
        self.assertTrue(event["accepted"])
        self.assertIn("phi_scaled", optimizer.snapshot()["strategy_probabilities"])

    def test_rejected_share_decreases_strategy_weight_but_stays_bounded(self):
        optimizer = MetaLearningOptimizer(
            learning_rate=0.5, initial_strategies=["phi_scaled"], min_weight=0.2
        )

        for _ in range(20):
            optimizer.update_from_outcome(
                strategy_id="phi_scaled",
                accepted=False,
                phi_resonance=0.0,
                thermal_cost=2.0,
            )

        self.assertGreaterEqual(optimizer.strategy_weights["phi_scaled"], 0.2)
        self.assertLess(optimizer.strategy_weights["phi_scaled"], 1.0)

    def test_evolving_memory_reinforces_and_prunes_successful_path(self):
        fabric = EvolvingMemoryFabric(num_nodes=4, fold_depth=1, hebbian_rate=0.5)

        fabric.reinforce_successful_path([0, 1, 3], reward=1.0)
        kernel = fabric.kernel.kernel_matrix()

        self.assertGreater(kernel[0, 1], 0.0)
        self.assertGreater(kernel[1, 3], 0.0)
        self.assertEqual(fabric.success_traces[(0, 1)], 1.0)

        fabric.prune_weak_connections(threshold=10.0)
        self.assertTrue(np.allclose(fabric.kernel.kernel_matrix(), 0.0))
        self.assertEqual({}, fabric.success_traces)


if __name__ == "__main__":
    unittest.main()
