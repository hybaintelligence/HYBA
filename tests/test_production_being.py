"""Production integration tests for manifold facades and deployment bindings."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.manifold_logic import ManifoldLogic  # noqa: E402
from hyba_genesis_api.core.reflexive_agent import ReflexiveAgent  # noqa: E402


class ProductionBeingTests(unittest.TestCase):
    def test_free_energy_bounds(self) -> None:
        agent = ReflexiveAgent(ManifoldLogic())
        for obs in [0.1, 0.5, 1.0]:
            for pred in [0.1, 0.5, 1.0]:
                self.assertGreaterEqual(agent.calculate_free_energy(obs, pred), 0.0)

    def test_ricci_flow_convergence_without_volume_collapse(self) -> None:
        manifold = ManifoldLogic()
        c1 = 0.8
        c2 = manifold.ricci_flow_smoothing(c1, 10.0)
        self.assertLess(c2, c1)
        self.assertGreater(c2, 0.0)

    def test_manifold_facade_curvature_and_euler(self) -> None:
        manifold = ManifoldLogic()
        state = [complex(1, 0), complex(0, 1), complex(1, 1)]
        self.assertEqual(2, manifold.calculate_euler_characteristic(10, 9))
        self.assertGreaterEqual(manifold.calculate_fisher_curvature(state), 0.0)

    def test_reflexive_agent_thermal_and_elegance_are_bounded(self) -> None:
        agent = ReflexiveAgent(ManifoldLogic())
        agent.start_cognition()
        self.assertGreaterEqual(agent.landauer_thermal_cost(0.5), 0.0)
        elegance = agent.measure_elegance("def f():\n    return 1\n")
        self.assertGreaterEqual(elegance, 0.0)
        self.assertLessEqual(elegance, 1.0)

    def test_docker_compose_contains_reflexive_production_bindings(self) -> None:
        compose = (REPO_ROOT / "docker-compose.production.yml").read_text(encoding="utf-8")
        self.assertIn("HYBA_ENABLE_REFLEXIVE_DAEMON", compose)
        self.assertIn("HYBA_RICCI_STEP_SIZE", compose)
        self.assertIn("HYBA_ONTOLOGICAL_PERSISTENCE_PATH", compose)
        self.assertIn("hyba_persistence", compose)


if __name__ == "__main__":
    unittest.main()
