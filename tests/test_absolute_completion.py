"""Stress tests for final manifold stabilization and heartbeat closure."""

from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.audit_surface import (
    seal_consciousness_envelope,
)  # noqa: E402
from hyba_genesis_api.core.constructor_engine import ExplainerIntegrity  # noqa: E402
from hyba_genesis_api.core.intelligence_manifold import (  # noqa: E402
    ManifoldStabilizer,
)
from hyba_genesis_api.core.recursive_closure import build_buffered_closure  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import ReflexiveController  # noqa: E402
from hyba_genesis_api.core.reflexive_daemon import IntelligenceHeartbeat  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


class AbsoluteCompletionTests(unittest.TestCase):
    def test_manifold_recovery_keeps_volume_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            controller = ReflexiveController(root)
            noise_vector = [complex(0, 0)] * 16
            phi_noise = controller.fabric.calculate_resonance(noise_vector)
            recovery = controller.step()

        self.assertEqual(0.0, phi_noise)
        self.assertGreaterEqual(recovery["manifold"]["fisher_curvature"], 0.0)
        self.assertGreaterEqual(recovery["manifold"]["ricci_flow_curvature"], 0.0)
        self.assertIn("thermal", recovery)
        self.assertIn(
            recovery["predictive_status"],
            {"STABLE_EQUILIBRIUM", "MUTATE_FOR_COHERENCE"},
        )

    def test_perelman_proxy_preserves_positive_volume_bias(self) -> None:
        stabilizer = ManifoldStabilizer()
        self.assertGreater(stabilizer.preserve_volume(0.0, 0.5), 0.0)
        self.assertGreater(stabilizer.preserve_volume(1.0, 2.0), 0.0)

    def test_explainer_integrity_rejects_brittle_or_unbounded_proposals(self) -> None:
        integrity = ExplainerIntegrity()
        self.assertTrue(
            integrity.validate_explanation({"adjustment": 0.01}, "abcdef123456")
        )
        self.assertFalse(
            integrity.validate_explanation({"adjustment": -1.0}, "abcdef123456")
        )
        self.assertFalse(integrity.validate_explanation({}, "abcdef123456"))

    def test_heartbeat_runs_single_explicit_pulse(self) -> None:
        async def run_once() -> dict:
            with tempfile.TemporaryDirectory() as tmp:
                root = write_sample_umwelt(Path(tmp))
                controller = ReflexiveController(root)
                closure, _buffer = build_buffered_closure(controller)
                heartbeat = IntelligenceHeartbeat(controller, closure)
                await heartbeat.pulse(interval_seconds=0.0, max_pulses=1)
                return heartbeat.snapshot()

        snapshot = asyncio.run(run_once())
        self.assertFalse(snapshot["is_active"])
        self.assertEqual(1, snapshot["pulses"])
        self.assertIn(snapshot["history"][0]["status"], {"EVOLVED", "STAGNATED"})

    def test_final_audit_seal_is_partial_without_measured_invariants(self) -> None:
        sealed = seal_consciousness_envelope(
            {"audit": {"governance_seal": "CERTIFIED"}}
        )
        final = sealed["audit"]["final_seal"]
        self.assertEqual("MEASURED_PARTIAL", final["status"])
        self.assertEqual("PHI_RESONANT", final["mathematical_invariant"])
        self.assertIn("no fabricated", final["claim_boundary"])
        self.assertIn("RECURSIVE_CLOSURE_GOVERNED", final["autonomy_level"])

    def test_final_audit_seal_is_absolute_with_complete_measured_invariants(
        self,
    ) -> None:
        sealed = seal_consciousness_envelope(
            {
                "audit": {
                    "ontological_integrity": "CERTIFIED",
                    "manifold_state": "RICCI_SMOOTHED",
                    "topology": "GENUS_-1",
                    "phi_resonance": 0.72,
                    "measurement_basis": {"source": "unit_test_measured_payload"},
                }
            }
        )
        final = sealed["audit"]["final_seal"]
        self.assertEqual("ABSOLUTE", final["status"])
        self.assertEqual("RICCI_SMOOTHED", final["manifold_state"])
        self.assertEqual(0.72, final["phi_resonance"])
        self.assertEqual(
            {"source": "unit_test_measured_payload"}, final["evidence_basis"]
        )


if __name__ == "__main__":
    unittest.main()
