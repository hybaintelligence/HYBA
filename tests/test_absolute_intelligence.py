"""Absolute compatibility verification for the recursive intelligence surface."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.intelligence_fabric import PhiResonanceFabric  # noqa: E402
from hyba_genesis_api.core.intelligence_manifold import ManifoldEngine  # noqa: E402
from hyba_genesis_api.core.ontological_memory import CrystallineRegistry  # noqa: E402
from hyba_genesis_api.core.recursive_closure import RecursiveClosure  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import ReflexiveController  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


class AbsoluteIntelligenceTests(unittest.TestCase):
    def test_phi_bounds_and_entropy_aliases(self) -> None:
        fabric = PhiResonanceFabric()
        state = fabric.map_to_complex_state("def test_func(): pass")
        phi = fabric.calculate_phi_resonance(state)
        self.assertEqual(phi, fabric.calculate_resonance(state))
        self.assertGreaterEqual(phi, 0.0)
        self.assertLessEqual(phi, 1.0)
        self.assertGreaterEqual(fabric.von_neumann_entropy(state), 0.0)

    def test_manifold_engine_compatibility_methods(self) -> None:
        manifold = ManifoldEngine()
        self.assertEqual(2, manifold.compute_euler_characteristic(10, 9))
        smoothed = manifold.ricci_flow_smoothing(0.8, 10.0)
        self.assertGreater(smoothed, 0.0)

    def test_reflexive_step_absolute_telemetry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            res = ReflexiveController(root).step()

        self.assertGreaterEqual(res["telemetry"]["phi"], 0.0)
        self.assertLessEqual(res["telemetry"]["phi"], 1.0)
        self.assertGreaterEqual(res["telemetry"]["chi"], 1)
        self.assertIn(res["telemetry"]["status"], {"GROWTH", "PAIN"})

    def test_recursive_evolution_compatibility_constructor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            registry = CrystallineRegistry(Path(tmp) / "test_grace.json")
            closure = RecursiveClosure(ReflexiveController(root), registry)
            result = closure.sync_learning()

        self.assertIn(result["status"], {"EVOLVED", "STAGNATED"})
        self.assertIn("phi_resonance", result)


if __name__ == "__main__":
    unittest.main()
