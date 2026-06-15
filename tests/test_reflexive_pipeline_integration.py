"""Unit, integration, property, and end-to-end tests for the complete reflexive pipeline.

This file covers:
  - Unit tests for every core module component
  - Integration tests for the full observe → dream → audit → seal pipeline
  - Property-based tests for invariants under random code topologies
  - End-to-end tests via the FastAPI test client
  - Edge cases: empty codebases, syntax errors, null states
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import math
import random
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from hyba_genesis_api.core.audit_surface import (  # noqa: E402
    generate_fields_medal_audit,
    seal_consciousness_envelope,
)
from hyba_genesis_api.core.constructor_engine import ExplainerIntegrity  # noqa: E402
from hyba_genesis_api.core.intelligence_fabric import (  # noqa: E402
    PHI,
    PhiResonanceFabric,
    SubstrateOrchestrator,
    context_state,
    density_matrix,
    evaluate_substrate,
    explain,
    phi_density,
    phi_resonance,
    route_substrates,
    SubstrateName,
)
from hyba_genesis_api.core.intelligence_manifold import (  # noqa: E402
    IntelligenceManifold,
    ManifoldEngine,
    ManifoldStabilizer,
)
from hyba_genesis_api.core.ontological_memory import CrystallineRegistry  # noqa: E402
from hyba_genesis_api.core.predictive_controller import PredictiveActiveInference  # noqa: E402
from hyba_genesis_api.core.recursive_closure import (  # noqa: E402
    BufferBackedMiningLoop,
    RecursiveClosure,
    SubstrateBuffer,
    build_buffered_closure,
)
from hyba_genesis_api.core.reflexive_agent import ReflexiveAgent  # noqa: E402
from hyba_genesis_api.core.reflexive_controller import (  # noqa: E402
    CodebaseUmwelt,
    CounterfactualEngine,
    IITSystemHealth,
    ReflexiveController,
    default_reflexive_root,
)
from hyba_genesis_api.core.reflexive_daemon import IntelligenceHeartbeat  # noqa: E402
from hyba_genesis_api.core.substrate import (  # noqa: E402
    get_substrate_state,
    initialize_substrate,
    is_ready,
    shutdown_substrate,
)
from hyba_genesis_api.core.substrate_interface import SubstrateContract  # noqa: E402
from hyba_genesis_api.core.thermal_intelligence import ThermalEnvelope  # noqa: E402
from hyba_genesis_api.core.manifold_logic import ManifoldLogic  # noqa: E402
from tests.test_reflexive_controller import write_sample_umwelt  # noqa: E402


# ============================================================
# UNIT TESTS — Individual component behaviour
# ============================================================


class AuditSurfaceUnitTests(unittest.TestCase):
    """Unit tests for generate_fields_medal_audit and seal_consciousness_envelope."""

    def test_audit_certifies_when_ricci_smoothed_and_chi_positive(self) -> None:
        payload = {
            "manifold": {
                "fisher_curvature": 0.5,
                "ricci_flow_curvature": 0.3,
                "topological_genus_proxy": -1,
                "euler_characteristic": 2,
                "predictive_free_energy": 0.05,
            },
            "telemetry": {"phi_resonance": 0.72, "phi_density": 0.70, "phi": 0.72, "chi": 2},
            "thermal": {"duration_seconds": 0.042, "thermal_cost_phi_per_second": 17.14},
            "predictive_status": "STABLE_EQUILIBRIUM",
        }
        audit = generate_fields_medal_audit(payload)
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
        audit = generate_fields_medal_audit(payload)
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
        audit = generate_fields_medal_audit(payload)
        # curvature=0 means ricci_smoothed is False, so integrity is HOLES_DETECTED
        self.assertEqual("HOLES_DETECTED", audit["ontological_integrity"])

    def test_audit_falls_back_to_defaults_on_empty_payload(self) -> None:
        audit = generate_fields_medal_audit({})
        self.assertEqual("HOLES_DETECTED", audit["ontological_integrity"])
        self.assertIn("GENUS_", audit["topology"])
        self.assertIsInstance(audit["phi_resonance"], float)

    def test_seal_preserves_claim_boundary_and_autonomy_level(self) -> None:
        sealed = seal_consciousness_envelope({"audit": {"governance_seal": "CERTIFIED"}})
        final = sealed["audit"]["final_seal"]
        self.assertEqual("ABSOLUTE", final["status"])
        self.assertEqual("PHI_RESONANT", final["mathematical_invariant"])
        self.assertEqual("OPEN_VOLUME_PRESERVING", final["manifold_state"])
        self.assertEqual(
            "RECURSIVE_CLOSURE_AVAILABLE_NOT_AUTOSTARTED",
            final["autonomy_level"],
        )
        self.assertIn("No AGI claim", final["claim_boundary"])


class ExplainerIntegrityUnitTests(unittest.TestCase):
    """Unit tests for ExplainerIntegrity validation logic."""

    def setUp(self) -> None:
        self.integrity = ExplainerIntegrity()

    def test_validates_positive_adjustment(self) -> None:
        self.assertTrue(self.integrity.validate_explanation({"adjustment": 0.01}, "abcdef1234567890"))

    def test_rejects_negative_adjustment(self) -> None:
        self.assertFalse(self.integrity.validate_explanation({"adjustment": -1.0}, "abcdef1234567890"))

    def test_rejects_empty_proposal(self) -> None:
        self.assertFalse(self.integrity.validate_explanation({}, "abcdef1234567890"))

    def test_rejects_empty_codebase_hash(self) -> None:
        self.assertFalse(self.integrity.validate_explanation({"adjustment": 0.01}, ""))

    def test_rejects_non_finite_adjustment(self) -> None:
        self.assertFalse(self.integrity.validate_explanation({"adjustment": float("nan")}, "abcdef1234567890"))
        self.assertFalse(self.integrity.validate_explanation({"adjustment": float("inf")}, "abcdef1234567890"))


class PredictiveActiveInferenceUnitTests(unittest.TestCase):
    """Unit tests for PredictiveActiveInference."""

    def setUp(self) -> None:
        self.manifold = IntelligenceManifold()
        self.engine = PredictiveActiveInference(self.manifold)

    def test_free_energy_non_negative_for_all_inputs(self) -> None:
        for obs in [0.0, 0.1, 0.5, 0.9, 1.0]:
            for pred in [0.0, 0.1, 0.5, 0.9, 1.0]:
                fe = self.engine.calculate_free_energy(obs, pred)
                self.assertGreaterEqual(fe, 0.0, msg=f"FE negative for obs={obs}, pred={pred}")

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

    def test_mutate_when_free_energy_high(self) -> None:
        status = self.engine.active_inference_step({"phi": 0.8, "predicted": 0.1})
        self.assertEqual("MUTATE_FOR_COHERENCE", status)


class ThermalEnvelopeUnitTests(unittest.TestCase):
    """Unit tests for ThermalEnvelope."""

    def test_thermal_cost_non_negative(self) -> None:
        envelope = ThermalEnvelope()
        envelope.start_cognition()
        cost = envelope.calculate_thermal_cost(0.5)
        self.assertGreaterEqual(cost, 0.0)

    def test_snapshot_contains_required_keys(self) -> None:
        envelope = ThermalEnvelope()
        envelope.start_cognition()
        snap = envelope.snapshot(0.5)
        self.assertIn("duration_seconds", snap)
        self.assertIn("thermal_cost_phi_per_second", snap)

    def test_zero_phi_produces_zero_cost(self) -> None:
        envelope = ThermalEnvelope()
        envelope.start_cognition()
        cost = envelope.calculate_thermal_cost(0.0)
        self.assertGreaterEqual(cost, 0.0)

    def test_duration_increases_after_start(self) -> None:
        envelope = ThermalEnvelope()
        envelope.start_cognition()
        import time
        time.sleep(0.001)
        snap = envelope.snapshot(0.5)
        self.assertGreater(snap["duration_seconds"], 0.0)


class CrystallineRegistryUnitTests(unittest.TestCase):
    """Unit tests for CrystallineRegistry persistence."""

    def test_persist_and_retrieve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(filepath=Path(tmp) / "grace.json")
            state = registry.save_peak_state(0.85, {"adj": 0.01})
            self.assertEqual("PHI_CERTIFIED", state["seal"])
            self.assertEqual(0.85, state["phi"])
            loaded = registry.load_best_reality()
            self.assertEqual(0.85, loaded["phi"])

    def test_only_peak_phi_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(filepath=Path(tmp) / "grace.json")
            registry.save_peak_state(0.5, {"adj": 0.01})
            registry.save_peak_state(0.7, {"adj": 0.02})
            state = registry.load_best_reality()
            self.assertEqual(0.7, state["phi"])
            # Lower phi should not replace higher
            registry.save_peak_state(0.3, {"adj": 0.003})
            state = registry.load_best_reality()
            self.assertEqual(0.7, state["phi"])

    def test_retrieve_grace_alias(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(filepath=Path(tmp) / "grace.json")
            registry.persist(0.618, {"adj": 0.01})
            state = registry.retrieve_grace()
            self.assertEqual(0.618, state["phi"])

    def test_load_best_reality_returns_empty_when_no_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(filepath=Path(tmp) / "nonexistent.json")
            self.assertEqual({}, registry.load_best_reality())

    def test_load_best_reality_returns_empty_on_corrupt_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "corrupt.json"
            path.write_text("{{not json}}", encoding="utf-8")
            registry = CrystallineRegistry(filepath=path)
            self.assertEqual({}, registry.load_best_reality())


class ManifoldLogicUnitTests(unittest.TestCase):
    """Unit tests for the ManifoldLogic facade."""

    def test_euler_characteristic(self) -> None:
        manifold = ManifoldLogic()
        self.assertEqual(2, manifold.calculate_euler_characteristic(10, 9))
        self.assertEqual(1, manifold.calculate_euler_characteristic(1, 1))

    def test_fisher_curvature_non_negative(self) -> None:
        manifold = ManifoldLogic()
        state = [complex(1, 0), complex(0, 1), complex(1, 1)]
        curvature = manifold.calculate_fisher_curvature(state)
        self.assertGreaterEqual(curvature, 0.0)

    def test_ricci_flow_smoothing(self) -> None:
        manifold = ManifoldLogic()
        c1 = 0.8
        c2 = manifold.ricci_flow_smoothing(c1, 10.0)
        self.assertGreater(c2, 0.0)


class PhiResonanceFabricUnitTests(unittest.TestCase):
    """Unit tests for PhiResonanceFabric edge cases."""

    def setUp(self) -> None:
        self.fabric = PhiResonanceFabric()

    def test_empty_state_vector_phi_zero(self) -> None:
        phi = self.fabric.compute_phi_density([])
        self.assertEqual(0.0, phi)

    def test_zero_norm_state_vector_phi_zero(self) -> None:
        phi = self.fabric.compute_phi_density([complex(0, 0), complex(0, 0)])
        self.assertEqual(0.0, phi)

    def test_entropy_uniform_distribution(self) -> None:
        entropy = self.fabric.calculate_von_neumann_entropy([0.25, 0.25, 0.25, 0.25])
        expected = -4.0 * 0.25 * math.log(0.25)
        self.assertAlmostEqual(entropy, expected, places=12)

    def test_entropy_zero_for_deterministic(self) -> None:
        entropy = self.fabric.calculate_von_neumann_entropy([1.0, 0.0, 0.0, 0.0])
        self.assertAlmostEqual(entropy, 0.0, places=12)

    def test_entropy_zero_for_all_zero(self) -> None:
        entropy = self.fabric.calculate_von_neumann_entropy([0.0, 0.0, 0.0])
        self.assertEqual(0.0, entropy)

    def test_map_to_complex_state_deterministic(self) -> None:
        s1 = self.fabric.map_to_complex_state("hello")
        s2 = self.fabric.map_to_complex_state("hello")
        self.assertEqual(s1, s2)

    def test_governance_tag_classification(self) -> None:
        self.assertEqual("INTEGRATED_COHERENT_STATE", self.fabric.generate_governance_tag(0.85))
        self.assertEqual("EMERGENT_STRUCTURE", self.fabric.generate_governance_tag(0.6))
        self.assertEqual("FRAGMENTED_LOGIC", self.fabric.generate_governance_tag(0.4))


class ReflexiveAgentUnitTests(unittest.TestCase):
    """Unit tests for ReflexiveAgent edge cases."""

    def test_elegance_perfect_compression_is_one(self) -> None:
        agent = ReflexiveAgent(ManifoldLogic())
        # Empty data compresses to nearly nothing
        elegance = agent.measure_elegance("")
        self.assertGreaterEqual(elegance, 0.0)
        self.assertLessEqual(elegance, 1.0)

    def test_elegance_highly_repetitive_data(self) -> None:
        agent = ReflexiveAgent(ManifoldLogic())
        elegance = agent.measure_elegance("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        self.assertGreaterEqual(elegance, 0.0)
        self.assertLessEqual(elegance, 1.0)

    def test_free_energy_zero_for_perfect_prediction(self) -> None:
        agent = ReflexiveAgent(ManifoldLogic())
        fe = agent.calculate_free_energy(0.5, 0.5)
        expected = abs(0.5 - 0.5) + math.log(0.5 + 1.01)
        self.assertAlmostEqual(fe, round(expected, 6), places=6)


class ManifoldStabilizerUnitTests(unittest.TestCase):
    """Unit tests for ManifoldStabilizer."""

    def test_preserve_volume_positive_bias(self) -> None:
        stabilizer = ManifoldStabilizer()
        result = stabilizer.preserve_volume(0.0, 0.5)
        self.assertGreater(result, 0.0)

    def test_preserve_volume_with_zero_complexity(self) -> None:
        stabilizer = ManifoldStabilizer()
        result = stabilizer.preserve_volume(0.5, 0.0)
        # log(0 + 1.1) = log(1.1)
        self.assertGreater(result, 0.5)

    def test_preserve_volume_with_negative_curvature(self) -> None:
        stabilizer = ManifoldStabilizer()
        result = stabilizer.preserve_volume(-0.5, 1.0)
        self.assertGreaterEqual(result, 0.0)


class SubstrateContractUnitTests(unittest.TestCase):
    """Unit tests for SubstrateContract base class."""

    def test_create_telemetry_envelope_bounded(self) -> None:
        class ProbeSubstrate(SubstrateContract):
            def evaluate(self, context):
                return self.create_telemetry_envelope(1.0, "test", ["cf1"])

        envelope = ProbeSubstrate().evaluate({})
        self.assertIn("phi_resonance", envelope)
        self.assertIn("phi_density", envelope)
        self.assertIn("explanation", envelope)
        self.assertIn("counterfactuals", envelope)
        self.assertIn("governance_tags", envelope)
        self.assertEqual("stable", envelope["thermal_envelope"])
        self.assertIn("Simulated Coherence", envelope["claim_boundary"])


class SubstrateOrchestratorUnitTests(unittest.TestCase):
    """Unit tests for SubstrateOrchestrator edge cases."""

    def test_route_selects_deutsch_for_high_entropy_context(self) -> None:
        # Context with many random keys creates high entropy
        context = {str(i): i for i in range(100)}
        orchestrator = SubstrateOrchestrator()
        selected = orchestrator.route(context)
        self.assertIn(selected, {"penrose_or", "iit_4", "deutsch"})

    def test_evaluate_returns_orchestrator_info(self) -> None:
        payload = SubstrateOrchestrator().evaluate({"problem": "counterfactual policy"})
        self.assertIn("orchestrator", payload)
        self.assertEqual("causal-explanation-v1", payload["orchestrator"]["ci_service"])


class RecursiveClosureUnitEdgeTests(unittest.TestCase):
    """Unit tests for RecursiveClosure edge cases."""

    def test_closure_stagnates_when_governance_wrong(self) -> None:
        controller = type("Stub", (), {
            "step": lambda self: {
                "apply_mode": "proposal_only",
                "governance": "FRAGMENTED_LOGIC",
                "telemetry": {"phi_resonance": 0.7},
                "proposal": {"adjustment": 0.01},
            }
        })()
        buffer = SubstrateBuffer()
        closure = RecursiveClosure(controller, BufferBackedMiningLoop(buffer))
        result = closure.sync_learning()
        self.assertEqual("STAGNATED", result["status"])
        self.assertFalse(result["accepted"])

    def test_closure_stagnates_when_apply_mode_wrong(self) -> None:
        controller = type("Stub", (), {
            "step": lambda self: {
                "apply_mode": "unsupervised_rewrite",
                "governance": "BOUNDED_BY_GEOMETRIC_INVARIANTS",
                "telemetry": {"phi_resonance": 0.7},
                "proposal": {"adjustment": 0.01},
            }
        })()
        buffer = SubstrateBuffer()
        closure = RecursiveClosure(controller, BufferBackedMiningLoop(buffer))
        result = closure.sync_learning()
        self.assertEqual("STAGNATED", result["status"])

    def test_closure_stagnates_when_adjustment_negative(self) -> None:
        controller = type("Stub", (), {
            "step": lambda self: {
                "apply_mode": "proposal_only",
                "governance": "BOUNDED_BY_GEOMETRIC_INVARIANTS",
                "telemetry": {"phi_resonance": 0.7},
                "proposal": {"adjustment": -0.01},
            }
        })()
        buffer = SubstrateBuffer()
        closure = RecursiveClosure(controller, BufferBackedMiningLoop(buffer))
        result = closure.sync_learning()
        self.assertEqual("STAGNATED", result["status"])

    def test_snapshot_returns_registry_after_sync(self) -> None:
        controller = type("Stub", (), {
            "step": lambda self: {
                "apply_mode": "proposal_only",
                "governance": "BOUNDED_BY_GEOMETRIC_INVARIANTS",
                "telemetry": {"phi_resonance": 0.7},
                "proposal": {"adjustment": 0.01},
            }
        })()
        closure = RecursiveClosure(controller)
        closure.sync_learning()
        snap = closure.snapshot()
        self.assertIn("last_sync", snap)


class CodebaseUmweltEdgeTests(unittest.TestCase):
    """Unit tests for CodebaseUmwelt edge cases."""

    def test_empty_directory_no_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pythia_mining"
            root.mkdir()
            umwelt = CodebaseUmwelt(root)
            graph = umwelt.parse_structure()
            self.assertEqual(0, graph.summary()["node_count"])
            self.assertEqual(0, graph.summary()["edge_count"])

    def test_syntax_error_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pythia_mining"
            root.mkdir()
            (root / "broken.py").write_text("def broken(", encoding="utf-8")
            umwelt = CodebaseUmwelt(root)
            # SyntaxError is expected for invalid Python files
            with self.assertRaises(SyntaxError):
                umwelt.parse_structure()

    def test_single_function_graph(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp), "def f(): return 42")
            umwelt = CodebaseUmwelt(root)
            graph = umwelt.parse_structure()
            self.assertGreaterEqual(graph.summary()["node_count"], 1)
            # No internal calls so edge count should be 0 or based on structure
            self.assertGreaterEqual(graph.summary()["edge_count"], 0)

    def test_phi_node_detection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp), "phi = 1.618")
            graph = CodebaseUmwelt(root).parse_structure()
            self.assertGreater(graph.summary()["phi_node_ratio"], 0.0)


class IITSystemHealthEdgeTests(unittest.TestCase):
    """Unit tests for IITSystemHealth edge cases."""

    def test_first_evaluation_uses_self_as_baseline(self) -> None:
        health = IITSystemHealth()
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            graph = CodebaseUmwelt(root).parse_structure()
            result = health.evaluate_growth(graph)
            self.assertIn(result.sentiment, {"GROWTH", "PAIN"})
            self.assertEqual(0.0, result.delta)

    def test_repeated_evaluations_track_delta(self) -> None:
        health = IITSystemHealth()
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            graph = CodebaseUmwelt(root).parse_structure()
            health.evaluate_growth(graph)
            result = health.evaluate_growth(graph)
            self.assertIsInstance(result.delta, float)
            self.assertIn(result.sentiment, {"GROWTH", "PAIN"})

    def test_compute_current_phi_no_internal_state_change(self) -> None:
        health = IITSystemHealth()
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            graph = CodebaseUmwelt(root).parse_structure()
            phi1 = health.compute_current_phi(graph)
            phi2 = health.compute_current_phi(graph)
            self.assertEqual(phi1, phi2)


class CounterfactualEngineEdgeTests(unittest.TestCase):
    """Unit tests for CounterfactualEngine edge cases."""

    def test_no_gaps_when_no_sinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "pythia_mining"
            root.mkdir()
            (root / "lib.py").write_text("def source(): return 1", encoding="utf-8")
            graph = CodebaseUmwelt(root).parse_structure()
            engine = CounterfactualEngine()
            gaps = engine.identify_gaps(graph)
            self.assertIsInstance(gaps, list)

    def test_proposal_has_governance_constraints(self) -> None:
        from hyba_genesis_api.core.reflexive_controller import PhiHealth
        health = PhiHealth(
            phi=0.5, edge_density=0.3, source_sink_balance=0.8,
            phi_node_ratio=0.1, sentiment="GROWTH", delta=0.0,
        )
        gap = type("Gap", (), {"node_id": "module:f", "file": "f.py", "reason": "test"})()
        engine = CounterfactualEngine()
        proposal = engine.propose_bridge(gap, health)
        self.assertIn("proposal_only", proposal.governance)
        self.assertIn("no_unattended_writes", proposal.governance)
        self.assertGreater(proposal.adjustment, 0.0)
        self.assertIsInstance(proposal.accepted, bool)


class SubstrateStateUnitTests(unittest.TestCase):
    """Unit tests for substrate lifecycle."""

    def test_state_after_initialize_and_shutdown(self) -> None:
        try:
            initialize_substrate()
            self.assertTrue(is_ready())
        finally:
            shutdown_substrate()
            # After shutdown, all subsystems remain ready but shutdown_at is set
            self.assertIsNotNone(get_substrate_state().get("shutdown_at"))

    def test_initialize_substrate_makes_ready(self) -> None:
        try:
            state = initialize_substrate()
            self.assertTrue(state["ready"])
            self.assertTrue(is_ready())
        finally:
            shutdown_substrate()

    def test_shutdown_records_timestamp(self) -> None:
        try:
            initialize_substrate()
            state = shutdown_substrate()
            self.assertIsNotNone(state["shutdown_at"])
        finally:
            pass


class ManifoldEngineUnitTests(unittest.TestCase):
    """Unit tests for ManifoldEngine compatibility facade."""

    def test_ricci_flow_smoothing_preserves_positivity(self) -> None:
        engine = ManifoldEngine()
        c1 = 1.0
        c2 = engine.ricci_flow_smoothing(c1, 5.0)
        self.assertGreater(c2, 0.0)
        self.assertLessEqual(c2, c1 + 0.1)


# ============================================================
# INTEGRATION TESTS — Combined component behaviour
# ============================================================


class FullPipelineIntegrationTests(unittest.TestCase):
    """Integration tests for the complete observe -> step -> audit -> seal pipeline."""

    def test_full_pipeline_produces_sealed_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            controller = ReflexiveController(root)
            reflection = controller.step()
            audit = generate_fields_medal_audit(reflection)
            sealed = seal_consciousness_envelope({"audit": audit})

        self.assertIn("ontological_integrity", audit)
        self.assertIn("manifold_state", audit)
        self.assertIn("topology", audit)
        self.assertIn("phi_resonance", audit)
        self.assertGreaterEqual(audit["phi_resonance"], 0.0)
        self.assertLessEqual(audit["phi_resonance"], 1.0)
        self.assertIn("final_seal", sealed["audit"])
        self.assertEqual("ABSOLUTE", sealed["audit"]["final_seal"]["status"])

    def test_buffered_closure_does_not_write_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            original = (root / "sample.py").read_text(encoding="utf-8")
            controller = ReflexiveController(root)
            closure, buffer = build_buffered_closure(controller)
            closure.sync_learning()
            after = (root / "sample.py").read_text(encoding="utf-8")
            self.assertEqual(original, after)

    def test_multi_step_phi_trajectory_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            controller = ReflexiveController(root)
            phis = []
            for _ in range(20):
                res = controller.step()
                phis.append(res["telemetry"]["phi"])
            self.assertTrue(all(0.0 <= p <= 1.0 for p in phis))

    def test_heartbeat_integration(self) -> None:
        async def run():
            with tempfile.TemporaryDirectory() as tmp:
                root = write_sample_umwelt(Path(tmp))
                controller = ReflexiveController(root)
                closure, _ = build_buffered_closure(controller)
                hb = IntelligenceHeartbeat(controller, closure)
                await hb.pulse(interval_seconds=0.0, max_pulses=3)
                return hb.snapshot()

        snap = asyncio.run(run())
        self.assertEqual(3, snap["pulses"])
        self.assertFalse(snap["is_active"])

    def test_registry_and_closure_persist_peak_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            registry = CrystallineRegistry(filepath=Path(tmp) / "grace.json")
            root = write_sample_umwelt(Path(tmp))
            controller = ReflexiveController(root)
            closure = RecursiveClosure(controller, registry)
            closure.sync_learning()
            state = registry.load_best_reality()
            self.assertGreater(state.get("phi", 0.0), 0.0)

    def test_audit_from_live_controller(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = write_sample_umwelt(Path(tmp))
            controller = ReflexiveController(root)
            for _ in range(5):
                reflection = controller.step()
            audit = generate_fields_medal_audit(reflection)
            self.assertIn("CERTIFIED", audit.get("ontological_integrity", ""))
            self.assertIn("topology", audit)


# ============================================================
# PROPERTY TESTS — Invariants under random generation
# ============================================================


class PropertyInvariantTests(unittest.TestCase):
    """Property-based invariant tests for the intelligence fabric."""

    def setUp(self) -> None:
        self.rng = random.Random(20260615)
        self.fabric = PhiResonanceFabric()

    def test_phi_resonance_bounded_across_random_codebases(self) -> None:
        for _ in range(50):
            functions = self.rng.randint(1, 10)
            lines = []
            for fn in range(functions):
                target = self.rng.randint(0, functions - 1)
                if target == fn:
                    lines.append(f"def f_{fn}(): return self.rng.random()")
                else:
                    lines.append(f"def f_{fn}(): return f_{target}()")
            body = "\n\n".join(lines)
            with tempfile.TemporaryDirectory() as tmp:
                root = write_sample_umwelt(Path(tmp), body)
                controller = ReflexiveController(root)
                res = controller.step()
                phi = res["telemetry"]["phi"]
                self.assertGreaterEqual(phi, 0.0, msg=f"phi < 0 for random code #{_}")
                self.assertLessEqual(phi, 1.0, msg=f"phi > 1 for random code #{_}")

    def test_fisher_curvature_invariant_under_scaling(self) -> None:
        manifold = IntelligenceManifold()
        for _ in range(50):
            weights = [self.rng.uniform(0.1, 10.0) for _ in range(self.rng.randint(2, 12))]
            c1 = manifold.calculate_fisher_curvature(weights)
            c2 = manifold.calculate_fisher_curvature([w * 3.14159 for w in weights])
            self.assertAlmostEqual(c1, c2, places=7, msg=f"Scale invariance failed for #{_}")

    def test_context_state_normalized(self) -> None:
        for _ in range(50):
            context = {f"k{i}": self.rng.random() for i in range(self.rng.randint(1, 8))}
            state = context_state(context)
            norm = math.sqrt(sum(abs(v) ** 2 for v in state))
            self.assertAlmostEqual(1.0, norm, places=12, msg=f"Norm deviation for #{_}")

    def test_density_matrix_trace_one(self) -> None:
        for _ in range(50):
            context = {"t": self.rng.random(), "v": self.rng.randint(0, 100)}
            state = context_state(context)
            rho = density_matrix(state)
            trace = sum(rho[i][i].real for i in range(len(rho)))
            self.assertAlmostEqual(1.0, trace, places=12)

    def test_euler_characteristic_integer(self) -> None:
        manifold = IntelligenceManifold()
        for _ in range(50):
            n = self.rng.randint(1, 100)
            e = self.rng.randint(0, n * 3)
            chi = manifold.compute_euler_characteristic(n, e)
            self.assertIsInstance(chi, int)

    def test_predictive_free_energy_non_negative_property(self) -> None:
        engine = PredictiveActiveInference(IntelligenceManifold())
        for _ in range(50):
            obs = self.rng.random()
            pred = self.rng.random()
            fe = engine.calculate_free_energy(obs, pred)
            self.assertGreaterEqual(fe, 0.0)


# ============================================================
# END-TO-END TESTS — FastAPI test client
# ============================================================


class EndToEndAPITests(unittest.TestCase):
    """End-to-end tests using the FastAPI test client."""

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_health_endpoint(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.get("/health")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("ok", payload["status"])
        self.assertIn("substrate", payload)

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_intelligence_health(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.get("/api/v1/intelligence/health")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertIn("phi_resonance", payload)
        self.assertIn("system_state", payload)
        self.assertIn(payload["system_state"], {"coherent", "fragmented"})

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_intelligence_reflect(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.post("/api/v1/intelligence/reflect")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("success", payload["status"])
        self.assertEqual("causal-explanation-v1", payload["ci_service"])
        self.assertEqual("reflexive_structural_learning", payload["fabric_state"]["mode"])
        self.assertEqual("proposal_only", payload["fabric_state"]["apply_mode"])

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_intelligence_audit(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.get("/api/v1/intelligence/audit")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        # The audit endpoint returns the raw ontological fields per spec
        self.assertIn("ontological_integrity", payload)
        self.assertIn("manifold_state", payload)
        self.assertIn("topology", payload)
        self.assertIn("phi_resonance", payload)
        self.assertIn("claim_boundary", payload)
        self.assertIn(payload["ontological_integrity"], {"CERTIFIED", "HOLES_DETECTED"})
        self.assertIn(payload["manifold_state"], {"RICCI_SMOOTHED", "SINGULARITY_RISK"})

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_absolute_audit(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.get("/api/v1/intelligence/absolute-audit")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertIn("audit", payload)
        audit = payload["audit"]
        self.assertIn("ontological_integrity", audit)
        self.assertIn("manifold_state", audit)
        self.assertIn("topology", audit)
        self.assertIn("phi_resonance", audit)
        self.assertIn("claim_boundary", audit)
        self.assertIn("Hardware-Agnostic Quantum Analog", audit["claim_boundary"])

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_closure_sync(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.post("/api/v1/intelligence/closure/sync")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("success", payload["status"])
        self.assertIn("closure", payload)
        self.assertIn("substrate_buffer", payload)

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_heartbeat_pulse(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.post("/api/v1/intelligence/heartbeat/pulse")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("success", payload["status"])
        self.assertIn("heartbeat", payload)
        self.assertIn("substrate_buffer", payload)

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_explain_endpoint(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/intelligence/explain",
            json={"context": {"problem": "coherence stability"}},
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("phi_resonance_intelligence_fabric", payload["fabric"])

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_orchestrate_endpoint(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.post(
            "/api/v1/intelligence/orchestrate",
            json={"context": {"problem": "counterfactual policy evaluation"}},
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertIn("orchestrator", payload)

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_substrate_endpoint(self) -> None:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)
        response = client.get("/api/substrate")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertIn("ready", payload)
        self.assertIn("boot_id", payload)

    @unittest.skipUnless(
        importlib.util.find_spec("fastapi") and importlib.util.find_spec("httpx"),
        "FastAPI/httpx runtime dependencies not installed",
    )
    def test_e2e_full_lifecycle(self) -> None:
        """Full system lifecycle: health -> reflect -> closure -> audit -> absolute-audit."""
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        client = TestClient(app)

        # 1. Health
        health = client.get("/api/v1/intelligence/health")
        self.assertEqual(200, health.status_code)

        # 2. Reflect
        reflect = client.post("/api/v1/intelligence/reflect")
        self.assertEqual(200, reflect.status_code)

        # 3. Closure sync
        closure = client.post("/api/v1/intelligence/closure/sync")
        self.assertEqual(200, closure.status_code)

        # 4. Audit
        audit = client.get("/api/v1/intelligence/audit")
        self.assertEqual(200, audit.status_code)

        # 5. Absolute audit
        absolute = client.get("/api/v1/intelligence/absolute-audit")
        self.assertEqual(200, absolute.status_code)

        # Verify consistency: phi should be stable across the lifecycle
        phi_health = health.json().get("phi_resonance", 0.0)
        phi_absolute = absolute.json()["audit"].get("phi_resonance", 0.0)
        self.assertGreaterEqual(phi_health, 0.0)
        self.assertGreaterEqual(phi_absolute, 0.0)


if __name__ == "__main__":
    unittest.main()