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
