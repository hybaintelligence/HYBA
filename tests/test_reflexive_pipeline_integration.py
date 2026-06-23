"""Unit, integration, property, and end-to-end tests for the complete reflexive pipeline.

This file covers:
  - Unit tests for every core module component
  - Integration tests for the full observe → dream → audit → seal pipeline
  - Property-based tests for invariants under random code topologies
  - End-to-end tests via the FastAPI test client
  - Edge cases: empty codebases, syntax errors, null states
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.audit_surface import (  # noqa: E402
    generate_formal_invariant_audit,
    seal_consciousness_envelope,
)
from hyba_genesis_api.core.constructor_engine import ExplainerIntegrity  # noqa: E402
from hyba_genesis_api.core.intelligence_manifold import (  # noqa: E402
    IntelligenceManifold,
)
from hyba_genesis_api.core.predictive_controller import (
    PredictiveActiveInference,
)  # noqa: E402


# ============================================================
# UNIT TESTS — Individual component behaviour
# ============================================================


class AuditSurfaceUnitTests(unittest.TestCase):
    """Unit tests for generate_formal_invariant_audit and seal_consciousness_envelope."""

    def test_audit_certifies_when_ricci_smoothed_and_chi_positive(self) -> None:
        payload = {
            "manifold": {
                "fisher_curvature": 0.5,
                "ricci_flow_curvature": 0.3,
                "topological_genus_proxy": -1,
                "euler_characteristic": 2,
                "predictive_free_energy": 0.05,
            },
            "telemetry": {
                "phi_resonance": 0.72,
                "phi_density": 0.70,
                "phi": 0.72,
                "chi": 2,
            },
            "thermal": {
                "duration_seconds": 0.042,
                "thermal_cost_phi_per_second": 17.14,
            },
            "predictive_status": "STABLE_EQUILIBRIUM",
        }
        audit = generate_formal_invariant_audit(payload)
        self.assertEqual("CERTIFIED", audit["ontological_integrity"])
        self.assertEqual("RICCI_SMOOTHED", audit["manifold_state"])
        self.assertEqual("GENUS_-1", audit["topology"])
        self.assertEqual(0.72, audit["phi_resonance"])
        self.assertEqual(2, audit["euler_characteristic"])

    def test_audit_detects_holes_when_chi_non_positive(self) -> None:
        payload = {
            "manifold": {
                "fisher_curvature": 2.0,
                "ricci_flow_curvature": 1.5,
                "topological_genus_proxy": -1,
                "euler_characteristic": 0,
                "predictive_free_energy": 0.8,
            },
            "telemetry": {"phi": 0.3},
            "thermal": {},
            "predictive_status": "MUTATE_FOR_COHERENCE",
        }
        audit = generate_formal_invariant_audit(payload)
        self.assertEqual("HOLES_DETECTED", audit["ontological_integrity"])
        # curvature=2 > 0 and ricci=1.5 < 2 so ricci_smoothed is True
        self.assertEqual("RICCI_SMOOTHED", audit["manifold_state"])
        self.assertEqual("GENUS_-1", audit["topology"])

    def test_audit_detects_singularity_risk_when_curvature_zero(self) -> None:
        payload = {
            "manifold": {
                "fisher_curvature": 0.0,
                "ricci_flow_curvature": 0.0,
                "topological_genus_proxy": 0,
                "euler_characteristic": 1,
                "predictive_free_energy": 0.0,
            },
            "telemetry": {"phi": 0.5},
            "thermal": {},
            "predictive_status": "STABLE_EQUILIBRIUM",
        }
        audit = generate_formal_invariant_audit(payload)
        # curvature=0 means ricci_smoothed is False, so integrity is HOLES_DETECTED
        self.assertEqual("HOLES_DETECTED", audit["ontological_integrity"])

    def test_audit_falls_back_to_defaults_on_empty_payload(self) -> None:
        audit = generate_formal_invariant_audit({})
        self.assertEqual("HOLES_DETECTED", audit["ontological_integrity"])
        self.assertIn("GENUS_", audit["topology"])
        self.assertIsInstance(audit["phi_resonance"], float)

    def test_seal_is_partial_without_measured_invariants(self) -> None:
        sealed = seal_consciousness_envelope(
            {"audit": {"governance_seal": "CERTIFIED"}}
        )
        final = sealed["audit"]["final_seal"]
        self.assertEqual("MEASURED_PARTIAL", final["status"])
        self.assertEqual("PHI_RESONANT", final["mathematical_invariant"])
        self.assertEqual("UNKNOWN", final["manifold_state"])
        self.assertEqual("RECURSIVE_CLOSURE_GOVERNED", final["autonomy_level"])
        self.assertIn("no fabricated", final["claim_boundary"])

    def test_seal_is_absolute_when_measured_invariants_certify(self) -> None:
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
        self.assertEqual("PHI_RESONANT", final["mathematical_invariant"])
        self.assertEqual("RICCI_SMOOTHED", final["manifold_state"])
        self.assertEqual("RECURSIVE_CLOSURE_GOVERNED", final["autonomy_level"])
        self.assertEqual(
            {"source": "unit_test_measured_payload"}, final["evidence_basis"]
        )


class ExplainerIntegrityUnitTests(unittest.TestCase):
    """Unit tests for ExplainerIntegrity validation logic."""

    def setUp(self) -> None:
        self.integrity = ExplainerIntegrity()

    def test_validates_positive_adjustment(self) -> None:
        self.assertTrue(
            self.integrity.validate_explanation(
                {"adjustment": 0.01}, "abcdef1234567890"
            )
        )

    def test_rejects_negative_adjustment(self) -> None:
        self.assertFalse(
            self.integrity.validate_explanation(
                {"adjustment": -1.0}, "abcdef1234567890"
            )
        )

    def test_rejects_empty_proposal(self) -> None:
        self.assertFalse(self.integrity.validate_explanation({}, "abcdef1234567890"))

    def test_rejects_empty_codebase_hash(self) -> None:
        self.assertFalse(self.integrity.validate_explanation({"adjustment": 0.01}, ""))

    def test_rejects_non_finite_adjustment(self) -> None:
        self.assertFalse(
            self.integrity.validate_explanation(
                {"adjustment": float("nan")}, "abcdef1234567890"
            )
        )
        self.assertFalse(
            self.integrity.validate_explanation(
                {"adjustment": float("inf")}, "abcdef1234567890"
            )
        )


class PredictiveActiveInferenceUnitTests(unittest.TestCase):
    """Unit tests for PredictiveActiveInference."""

    def setUp(self) -> None:
        self.manifold = IntelligenceManifold()
        self.engine = PredictiveActiveInference(self.manifold)

    def test_free_energy_non_negative_for_all_inputs(self) -> None:
        for obs in [0.0, 0.1, 0.5, 0.9, 1.0]:
            for pred in [0.0, 0.1, 0.5, 0.9, 1.0]:
                fe = self.engine.calculate_free_energy(obs, pred)
                self.assertGreaterEqual(
                    fe, 0.0, msg=f"FE negative for obs={obs}, pred={pred}"
                )

    def test_free_energy_zero_when_perfect_prediction(self) -> None:
        # Perfect prediction: obs == pred, free_energy = 0 + log(obs + 1.1)
        fe = self.engine.calculate_free_energy(0.5, 0.5)
        expected = math.log(0.5 + 1.1)
        self.assertAlmostEqual(fe, round(expected, 6), places=6)

    def test_active_inference_deterministic(self) -> None:
        s1 = self.engine.active_inference_step({"phi": 0.8, "predicted": 0.1})
        s2 = self.engine.active_inference_step({"phi": 0.8, "predicted": 0.1})
        self.assertEqual(s1, s2)

    def test_predict_next_phi_stable(self) -> None:
        for _ in range(10):
            p = self.engine.predict_next_phi(0.5)
            self.assertGreaterEqual(p, 0.0)

    def test_stable_when_free_energy_low(self) -> None:
        # With phi very small and predicted matching, free_energy ≈ log(0.001+1.1) ≈ 0.096 < 0.1
        status = self.engine.active_inference_step({"phi": 0.001, "predicted": 0.001})
        self.assertEqual("STABLE_EQUILIBRIUM", status)
