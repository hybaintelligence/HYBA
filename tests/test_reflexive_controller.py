"""Unit, integration, and property tests for recursive structural learning."""

from __future__ import annotations

import importlib.util
import random
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.intelligence_fabric import (  # noqa: E402
    PhiResonanceFabric,
    SubstrateOrchestrator,
)
from hyba_genesis_api.core.substrate_interface import SubstrateContract  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import (  # noqa: E402
    CodebaseUmwelt,
    CounterfactualEngine,
    IITSystemHealth,
    ReflexiveController,
)


def write_sample_umwelt(root: Path, body: str | None = None) -> Path:
    pythia_root = root / "pythia_mining"
    pythia_root.mkdir()
    (pythia_root / "sample.py").write_text(
        body
        or """
PHI = (1 + 5 ** 0.5) / 2

def source():
    return bridge()

def bridge():
    return PHI

class PenroseWeights:
    def adjust(self):
        return bridge()
""".strip(),
        encoding="utf-8",
    )
    return pythia_root


class ReflexiveControllerUnitTests(unittest.TestCase):
    def test_phi_resonance_fabric_entropy_density_and_governance(self) -> None:
        fabric = PhiResonanceFabric()
        entropy = fabric.calculate_von_neumann_entropy([0.25, 0.25, 0.25, 0.25])
        density = fabric.compute_phi_density([complex(1, 0), complex(0, 1), complex(1, 1)])

        self.assertGreater(entropy, 0.0)
        self.assertGreaterEqual(density, 0.0)
        self.assertLessEqual(density, 1.0)
        mapped = fabric.map_to_complex_state("def test_func(): pass")
        self.assertEqual(mapped, fabric.map_to_complex_state("def test_func(): pass"))
        self.assertGreaterEqual(fabric.calculate_resonance(mapped), 0.0)
        self.assertLessEqual(fabric.calculate_resonance(mapped), 1.0)
        self.assertGreaterEqual(fabric.compute_von_neumann_proxy(mapped), 0.0)
        self.assertIn(
            fabric.generate_governance_tag(density),
            {"FRAGMENTED_LOGIC", "EMERGENT_STRUCTURE", "INTEGRATED_COHERENT_STATE"},
        )

    def test_unified_substrate_contract_envelope_is_bounded(self) -> None:
        class ProbeSubstrate(SubstrateContract):
            def evaluate(self, context):
                return self.create_telemetry_envelope(2.0, "probe", ["counterfactual"])

        envelope = ProbeSubstrate().evaluate({})
        self.assertLess(envelope["phi_density"], 1.0)
        self.assertEqual("stable", envelope["thermal_envelope"])
        self.assertIn("HIGH_COHERENCE", envelope["governance_tags"])

    def test_substrate_orchestrator_returns_ci_service_envelope(self) -> None:
        payload = SubstrateOrchestrator().evaluate({"problem": "semantic policy explanation"})
        self.assertIn("orchestrator", payload)
        self.assertEqual("causal-explanation-v1", payload["orchestrator"]["ci_service"])
        self.assertIn(payload["substrate"], {"penrose_or", "iit_4", "deutsch"})

    def test_umwelt_maps_ast_into_causal_topology(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            graph = CodebaseUmwelt(root).parse_structure()

        summary = graph.summary()
        self.assertGreaterEqual(summary["node_count"], 4)
        self.assertGreaterEqual(summary["edge_count"], 2)
        self.assertGreater(summary["phi_node_ratio"], 0.0)
        self.assertTrue(any("source" in node_id for node_id in graph.nodes))

    def test_iit_health_and_counterfactual_proposal_are_bounded_and_governed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            graph = CodebaseUmwelt(root).parse_structure()

        health = IITSystemHealth().evaluate_growth(graph)
        proposal = CounterfactualEngine().propose_bridge(
            CounterfactualEngine().identify_gaps(graph)[0], health
        )

        self.assertGreaterEqual(health.phi, 0.0)
        self.assertLessEqual(health.phi, 1.0)
        self.assertEqual("GROWTH", health.sentiment)
        self.assertEqual("proposal_only", proposal.apply_mode)
        self.assertIn("no_unattended_writes", proposal.governance)
        self.assertGreater(proposal.adjustment, 0.0)


class ReflexiveControllerIntegrationTests(unittest.TestCase):
    def test_reflexive_step_returns_proposal_without_mutating_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            before = (root / "sample.py").read_text(encoding="utf-8")
            controller = ReflexiveController(root)
            self.assertIn("sample.py", controller.observe_codebase())
            payload = controller.step()
            after = (root / "sample.py").read_text(encoding="utf-8")

        self.assertEqual(before, after)
        self.assertEqual("reflexive_structural_learning", payload["mode"])
        self.assertEqual("proposal_only", payload["apply_mode"])
        self.assertIn("health", payload)
        self.assertIn("telemetry", payload)
        self.assertIn("compression", payload)
        self.assertIn("knowledge_gaps", payload)
        self.assertIn("no unattended source rewrites", payload["claim_boundary"])
        self.assertIn(payload["action_taken"], {"ACCEPT_IN_MEMORY", "REJECT_FRAGMENTATION"})

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies are not installed in this Python environment",
    )
    def test_reflect_api_returns_reflexive_learning_payload(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        response = TestClient(app).post("/api/v1/intelligence/reflect")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("success", payload["status"])
        self.assertEqual("causal-explanation-v1", payload["ci_service"])
        self.assertEqual("reflexive_structural_learning", payload["fabric_state"]["mode"])
        self.assertEqual("proposal_only", payload["fabric_state"]["apply_mode"])


class ReflexiveControllerPropertyTests(unittest.TestCase):
    def test_dream_cycle_and_safety_valve_match_governance_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            controller = ReflexiveController(root)
            dream = controller.dream_cycle()

        self.assertIn("phi_density", dream)
        self.assertIn(dream["status"], {"GROWTH", "PAIN"})
        self.assertIn(
            dream["governance"],
            {"FRAGMENTED_LOGIC", "EMERGENT_STRUCTURE", "INTEGRATED_COHERENT_STATE"},
        )
        self.assertFalse(controller.commit_learning({"status": "PAIN", "phi_density": 0.1}))

    def test_generated_code_topologies_keep_phi_health_bounded(self) -> None:
        rng = random.Random(20260614)
        for index in range(40):
            function_count = rng.randint(2, 8)
            lines = ["PHI = (1 + 5 ** 0.5) / 2"]
            for fn in range(function_count):
                target = rng.randint(0, function_count - 1)
                if target == fn:
                    lines.append(f"def f_{fn}():\n    return PHI")
                else:
                    lines.append(f"def f_{fn}():\n    return f_{target}()")
            with tempfile.TemporaryDirectory() as tmp:
                root = write_sample_umwelt(Path(tmp), "\n\n".join(lines))
                graph = CodebaseUmwelt(root).parse_structure()
                health = IITSystemHealth().evaluate_growth(graph)
                controller = ReflexiveController(root)
                self.assertIn("sample.py", controller.observe_codebase())
                payload = controller.step()

            self.assertGreaterEqual(health.phi, 0.0, msg=f"case {index}")
            self.assertLessEqual(health.phi, 1.0, msg=f"case {index}")
            self.assertGreaterEqual(payload["compression"]["ratio"], 0.0)
            self.assertEqual("proposal_only", payload["apply_mode"])


if __name__ == "__main__":
    unittest.main()
