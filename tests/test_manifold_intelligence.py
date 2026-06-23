"""Unit, integration, and property tests for manifold intelligence."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.intelligence_manifold import (
    IntelligenceManifold,
)  # noqa: E402
from hyba_genesis_api.core.predictive_controller import (
    PredictiveActiveInference,
)  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import ReflexiveController  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


class ManifoldUnitTests(unittest.TestCase):
    def test_topological_integrity(self) -> None:
        manifold = IntelligenceManifold()
        self.assertEqual(2, manifold.compute_euler_characteristic(10, 9))

    def test_causal_impact_and_counterfactual_possibility(self) -> None:
        manifold = IntelligenceManifold()
        manifold.update_causal_graph([("source", "bridge"), ("source", "sink")])
        self.assertGreater(manifold.infer_causal_impact("source"), 0.0)
        self.assertTrue(manifold.check_task_possibility("abc_target", "cat"))
        self.assertFalse(manifold.check_task_possibility("abc", "target"))
        self.assertEqual("source", manifold.identify_critical_functions()[0]["node_id"])

    def test_predictive_active_inference_actions_are_deterministic(self) -> None:
        manifold = IntelligenceManifold()
        engine = PredictiveActiveInference(manifold)
        self.assertEqual(0.09531, engine.calculate_free_energy(0.0, 0.0))
        self.assertEqual(
            "MUTATE_FOR_COHERENCE",
            engine.active_inference_step({"phi": 0.8, "predicted": 0.1}),
        )
        self.assertGreaterEqual(engine.predict_next_phi(0.5), 0.0)


class ManifoldIntegrationTests(unittest.TestCase):
    def test_reflexive_step_includes_five_dimensional_synthesis(self) -> None:
        with self.subTest("temporary codebase"):
            import tempfile

            with tempfile.TemporaryDirectory() as tmp:
                root = write_sample_umwelt(Path(tmp))
                payload = ReflexiveController(root).step()

        self.assertIn("manifold", payload)
        self.assertIn("predictive_status", payload)
        self.assertIn("causal_hubs", payload)
        self.assertEqual("BOUNDED_BY_GEOMETRIC_INVARIANTS", payload["governance"])
        self.assertIn("fisher_curvature", payload["manifold"])
        self.assertIn("euler_characteristic", payload["manifold"])


class ManifoldPropertyTests(unittest.TestCase):
    def test_geometric_curvature_is_non_negative_and_scale_invariant(self) -> None:
        rng = random.Random(314159)
        manifold = IntelligenceManifold()
        for _ in range(128):
            weights = [rng.uniform(0.1, 10.0) for _ in range(rng.randint(2, 12))]
            curvature = manifold.calculate_fisher_curvature(weights)
            scaled = manifold.calculate_fisher_curvature(
                [weight * 2.0 for weight in weights]
            )
            self.assertGreaterEqual(curvature, 0.0)
            self.assertAlmostEqual(curvature, scaled, places=7)

    def test_manifold_synthesis_remains_bounded_for_generated_inputs(self) -> None:
        rng = random.Random(271828)
        manifold = IntelligenceManifold()
        for _ in range(64):
            nodes = rng.randint(1, 100)
            edges = rng.randint(0, nodes * 2)
            weights = [rng.uniform(0.1, 5.0) for _ in range(5)]
            telemetry = manifold.synthesize(
                nodes=nodes,
                edges=edges,
                weights=weights,
                current_logic="optimization_target_phi",
                target_transformation="phi",
                observed_phi=rng.random(),
                predicted_phi=rng.random(),
            )
            self.assertGreaterEqual(telemetry.predictive_free_energy, 0.0)
            self.assertGreaterEqual(telemetry.fisher_curvature, 0.0)
            self.assertGreaterEqual(telemetry.geometric_stability, 0.0)
            self.assertLessEqual(telemetry.geometric_stability, 1.0)


if __name__ == "__main__":
    unittest.main()
