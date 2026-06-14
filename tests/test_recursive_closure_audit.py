"""Tests for recursive closure and semantic audit surfaces."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.audit_surface import generate_fields_medal_audit  # noqa: E402
from hyba_genesis_api.core.recursive_closure import (  # noqa: E402
    BufferBackedMiningLoop,
    RecursiveClosure,
    SubstrateBuffer,
    build_buffered_closure,
)
from hyba_genesis_api.core.reflexive_controller import ReflexiveController  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


class StubController:
    def __init__(self, phi: float, adjustment: float = 0.01):
        self.phi = phi
        self.adjustment = adjustment

    def step(self):
        return {
            "apply_mode": "proposal_only",
            "governance": "BOUNDED_BY_GEOMETRIC_INVARIANTS",
            "telemetry": {"phi_resonance": self.phi},
            "proposal": {"adjustment": self.adjustment},
            "manifold": {
                "fisher_curvature": 0.25,
                "topological_genus_proxy": -1,
                "predictive_free_energy": 0.05,
            },
            "predictive_status": "STABLE_EQUILIBRIUM",
        }


class RecursiveClosureUnitTests(unittest.TestCase):
    def test_closure_evolves_only_when_phi_floor_and_governance_pass(self) -> None:
        buffer = SubstrateBuffer()
        closure = RecursiveClosure(StubController(0.7), BufferBackedMiningLoop(buffer))
        result = closure.sync_learning()

        self.assertTrue(result["accepted"])
        self.assertEqual("EVOLVED", result["status"])
        self.assertIn("entropy_threshold_delta", buffer.parameters)
        self.assertEqual("in_memory_only", result["event"]["persistence"])

    def test_closure_stagnates_when_phi_is_insufficient(self) -> None:
        buffer = SubstrateBuffer()
        closure = RecursiveClosure(StubController(0.2), BufferBackedMiningLoop(buffer))
        result = closure.sync_learning()

        self.assertFalse(result["accepted"])
        self.assertEqual("STAGNATED", result["status"])
        self.assertEqual({}, buffer.parameters)

    def test_audit_surface_seals_deterministic_reflection(self) -> None:
        audit = generate_fields_medal_audit(StubController(0.7).step())

        self.assertEqual("CERTIFIED_DETERMINISTIC", audit["governance_seal"])
        self.assertEqual("STABLE", audit["ontological_integrity"])
        self.assertEqual(0.7, audit["phi_resonance"])


class RecursiveClosureIntegrationTests(unittest.TestCase):
    def test_buffered_closure_runs_against_reflexive_controller(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            closure, buffer = build_buffered_closure(ReflexiveController(root))
            result = closure.sync_learning()

        self.assertIn(result["status"], {"EVOLVED", "STAGNATED"})
        self.assertIn("reflection", result)
        self.assertIn("parameters", buffer.snapshot())
        self.assertEqual("in-memory runtime parameter evolution; no source writes", result["claim_boundary"])


if __name__ == "__main__":
    unittest.main()
