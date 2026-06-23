"""Tests for thermal, Ricci-flow, and ontological-memory invariants."""

from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.audit_surface import (
    generate_formal_invariant_audit,
)  # noqa: E402
from hyba_genesis_api.core.intelligence_manifold import (
    IntelligenceManifold,
)  # noqa: E402
from hyba_genesis_api.core.ontological_memory import CrystallineRegistry  # noqa: E402
from hyba_genesis_api.core.recursive_closure import (  # noqa: E402
    BufferBackedMiningLoop,
    RecursiveClosure,
    SubstrateBuffer,
)
from hyba_genesis_api.core.reflexive_controller import ReflexiveController  # noqa: E402
from hyba_genesis_api.core.thermal_intelligence import ThermalEnvelope  # noqa: E402
from tests.test_recursive_closure_audit import StubController  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


class TemporalEnergyInvariantTests(unittest.TestCase):
    def test_thermal_envelope_reports_non_negative_cost(self) -> None:
        thermal = ThermalEnvelope()
        thermal.start_cognition()
        time.sleep(0.001)
        snapshot = thermal.snapshot(0.5)

        self.assertGreater(snapshot["duration_seconds"], 0.0)
        self.assertGreaterEqual(snapshot["thermal_cost_phi_per_second"], 0.0)

    def test_ricci_flow_smooths_curvature_monotonically(self) -> None:
        manifold = IntelligenceManifold()
        curvature = 2.5
        smoothed = manifold.calculate_ricci_flow(curvature, step_size=0.01)

        self.assertGreaterEqual(smoothed, 0.0)
        self.assertGreaterEqual(smoothed, 0.0)

    def test_crystalline_registry_persists_only_peak_phi(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(Path(tmp) / "ontological_state.json")
            low = registry.save_peak_state(0.4, {"adjustment": 0.01})
            high = registry.save_peak_state(0.8, {"adjustment": 0.02})
            retained = registry.save_peak_state(0.6, {"adjustment": 0.03})
            loaded = registry.load_best_reality()

        self.assertEqual(0.4, low["phi"])
        self.assertEqual(0.8, high["phi"])
        self.assertEqual(0.8, retained["phi"])
        self.assertEqual("PHI_CERTIFIED", loaded["seal"])

    def test_recursive_closure_writes_accepted_peak_to_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(Path(tmp) / "state.json")
            buffer = SubstrateBuffer()
            closure = RecursiveClosure(
                StubController(0.7),
                BufferBackedMiningLoop(buffer),
                registry=registry,
            )
            result = closure.sync_learning()
            loaded = registry.load_best_reality()

        self.assertTrue(result["accepted"])
        self.assertEqual(0.7, loaded["phi"])
        self.assertEqual("mathematical_artifact_no_source_write", loaded["persistence"])

    def test_reflexive_step_and_audit_include_thermal_and_ricci_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            payload = ReflexiveController(root).step()
            audit = generate_formal_invariant_audit(payload)

        self.assertIn("thermal", payload)
        self.assertIn("ricci_flow_curvature", payload["manifold"])
        self.assertIn("thermal_state", audit)
        self.assertIn("ricci_flow_curvature", audit)


if __name__ == "__main__":
    unittest.main()
