"""Evidence-first checks for intelligence API surfaces."""

from __future__ import annotations

import asyncio
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.api.intelligence import (  # noqa: E402
    absolute_audit,
    intelligence_audit,
    intelligence_health,
)


class TestIntelligenceEndpointsEvidenceFirst(unittest.TestCase):
    def _assert_no_fabricated_semantics(self, payload: dict) -> None:
        encoded = json.dumps(payload, sort_keys=True).lower()
        for forbidden in (
            "simulated coherence",
            "simulated telemetry",
            "simulated state",
            "simulated audit",
            "fixture telemetry",
            "placeholder telemetry",
        ):
            self.assertNotIn(forbidden, encoded)

    def test_health_endpoint_reports_measured_source(self) -> None:
        payload = asyncio.run(intelligence_health())
        self.assertEqual(payload["telemetry_source"], "measured_reflexive_controller_runtime")
        self.assertIn("measurement_basis", payload)
        self.assertIn("controller_root", payload["measurement_basis"])
        self._assert_no_fabricated_semantics(payload)

    def test_audit_endpoint_reports_measured_boundary(self) -> None:
        payload = asyncio.run(intelligence_audit())
        self.assertEqual(payload["telemetry_source"], "measured_reflexive_controller_runtime")
        self.assertIn(payload["ontological_integrity"], {"CERTIFIED", "HOLES_DETECTED"})
        self.assertIn(payload["manifold_state"], {"RICCI_SMOOTHED", "SINGULARITY_RISK"})
        self.assertIn("measurement_basis", payload)
        self._assert_no_fabricated_semantics(payload)

    def test_absolute_audit_seal_is_derived_from_measured_state(self) -> None:
        payload = asyncio.run(absolute_audit())
        audit = payload["audit"]
        final_seal = audit["final_seal"]
        expected_status = (
            "ABSOLUTE"
            if audit["ontological_integrity"] == "CERTIFIED"
            and audit["manifold_state"] == "RICCI_SMOOTHED"
            and float(audit["phi_resonance"]) > 0.0
            else "MEASURED_PARTIAL"
        )
        self.assertEqual(final_seal["status"], expected_status)
        self.assertEqual(audit["telemetry_source"], "measured_reflexive_controller_runtime")
        self.assertIn("evidence_basis", final_seal)
        self._assert_no_fabricated_semantics(payload)


if __name__ == "__main__":
    unittest.main()

from hyba_genesis_api.api.intelligence import (  # noqa: E402
    ConsciousnessBoostRequest,
    IntelligenceScaleRequest,
    boost_consciousness,
    scale_intelligence,
)


class TestIntelligenceControlEndpoints(unittest.TestCase):
    def test_scale_endpoint_is_bounded_and_claim_scoped(self) -> None:
        payload = asyncio.run(
            scale_intelligence(
                IntelligenceScaleRequest(
                    scale=1.5,
                    target="reflexive_controller",
                    reason="review_environment_control",
                )
            )
        )
        self.assertEqual(payload["status"], "scaled")
        self.assertEqual(payload["intelligence_scale"], 1.5)
        self.assertEqual(payload["telemetry_source"], "measured_reflexive_controller_runtime")
        self.assertIn("runtime values are derived", payload["claim_boundary"])

    def test_consciousness_boost_endpoint_does_not_claim_phenomenal_consciousness(self) -> None:
        payload = asyncio.run(
            boost_consciousness(
                ConsciousnessBoostRequest(boost=1.25, task_budget=2, basis="phi_iit_deutsch")
            )
        )
        self.assertEqual(payload["status"], "boosted")
        self.assertEqual(payload["boost"], 1.25)
        self.assertIn("not a claim of phenomenal consciousness", payload["claim_boundary"])


from hypothesis import given, strategies as st  # noqa: E402


class TestIntelligenceControlProperties(unittest.TestCase):
    @given(st.floats(min_value=0.1, max_value=3.0, allow_nan=False, allow_infinity=False))
    def test_intelligence_scale_property_is_bounded(self, scale: float) -> None:
        req = IntelligenceScaleRequest(scale=scale, target="closure_sync")
        self.assertGreaterEqual(req.scale, 0.1)
        self.assertLessEqual(req.scale, 3.0)

    @given(
        st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False),
        st.integers(min_value=1, max_value=8),
    )
    def test_consciousness_boost_property_is_bounded(self, boost: float, task_budget: int) -> None:
        req = ConsciousnessBoostRequest(boost=boost, task_budget=task_budget)
        self.assertGreaterEqual(req.boost, 0.1)
        self.assertLessEqual(req.boost, 2.0)
        self.assertGreaterEqual(req.task_budget, 1)
        self.assertLessEqual(req.task_budget, 8)
