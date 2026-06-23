"""Unit, integration, and property tests for the φ-resonance intelligence fabric."""

from __future__ import annotations

import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.intelligence_fabric import (  # noqa: E402
    MAX_CONTEXT_DIMENSION,
    PHI,
    SubstrateName,
    context_state,
    density_matrix,
    evaluate_substrate,
    explain,
    phi_density,
    phi_resonance,
    route_substrates,
)


class IntelligenceFabricUnitTests(unittest.TestCase):
    def test_context_state_is_normalized_and_density_matrix_is_physical(self) -> None:
        state = context_state({"problem": "coherence stability", "depth": 3})
        rho = density_matrix(state)

        self.assertEqual(MAX_CONTEXT_DIMENSION, len(state))
        self.assertAlmostEqual(
            1.0, math.sqrt(sum(abs(value) ** 2 for value in state)), places=12
        )
        self.assertAlmostEqual(
            1.0, sum(rho[idx][idx].real for idx in range(len(rho))), places=12
        )
        self.assertTrue(all(rho[idx][idx].real >= -1e-12 for idx in range(len(rho))))

    def test_substrate_contract_contains_telemetry_explanation_counterfactuals_governance(
        self,
    ) -> None:
        result = evaluate_substrate(
            SubstrateName.DEUTSCH,
            {"intent": "explain counterfactual policy", "risk": "review"},
        )

        self.assertEqual("deutsch", result.substrate)
        self.assertEqual(64, len(result.context_digest))
        self.assertIn("deterministic", result.explanation)
        self.assertGreaterEqual(len(result.counterfactuals), 2)
        self.assertIn("hardware_agnostic_math", result.governance)
        self.assertIn("no_quantum_speedup_claim", result.governance)

    def test_router_uses_semantic_intent_and_explicit_requests(self) -> None:
        routed = route_substrates({"task": "integrated cause effect partition"})
        self.assertEqual([SubstrateName.IIT_4], routed)
        explicit = route_substrates({"task": "anything"}, ["penrose_or", "deutsch"])
        self.assertEqual([SubstrateName.PENROSE_OR, SubstrateName.DEUTSCH], explicit)


class IntelligenceFabricIntegrationTests(unittest.TestCase):
    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies are not installed in this Python environment",
    )
    def test_explain_api_returns_auditable_fabric_envelope(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/intelligence/explain",
            json={
                "context": {
                    "problem": "semantic counterfactual explanation for stability policy",
                    "difficulty": 0.72,
                }
            },
        )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("phi_resonance_intelligence_fabric", payload["fabric"])
        self.assertIn(payload["selected_substrate"], payload["routing"])
        self.assertGreaterEqual(len(payload["raw_metrics"]), 1)
        self.assertIn("no quantum-speedup claim", payload["claim_boundary"])


class IntelligenceFabricPropertyTests(unittest.TestCase):
    def test_context_seeding_is_order_independent(self) -> None:
        left = context_state({"a": 1, "b": [2, 3]})
        right = context_state({"b": [2, 3], "a": 1})
        self.assertEqual(left, right)

    def test_phi_metrics_remain_bounded_for_generated_contexts(self) -> None:
        rng = random.Random(1337)
        for index in range(128):
            context = {
                "index": index,
                "value": rng.random(),
                "token": rng.choice(
                    ["coherence", "partition", "counterfactual", "policy"]
                ),
                "vector": [rng.randint(0, 255) for _ in range(5)],
            }
            state = context_state(context)
            rho = density_matrix(state)
            density = phi_density(state)
            resonance = phi_resonance(rho)
            envelope = explain(context)

            self.assertTrue(math.isfinite(density))
            self.assertTrue(math.isfinite(resonance))
            self.assertGreaterEqual(density, 0.0)
            self.assertLessEqual(density, 1.0)
            self.assertGreaterEqual(resonance, 0.0)
            self.assertLessEqual(resonance, 1.0)
            self.assertAlmostEqual(PHI, envelope["phi_constant"], places=12)
            for metrics in envelope["raw_metrics"]:
                for key in (
                    "phi_density",
                    "phi_resonance",
                    "thermal_envelope",
                    "latency_weight",
                    "difficulty",
                    "cause_effect_richness",
                    "counterfactual_depth",
                    "stability",
                    "explanation_quality",
                ):
                    self.assertGreaterEqual(metrics[key], 0.0)
                    self.assertLessEqual(metrics[key], 1.0)


if __name__ == "__main__":
    unittest.main()
