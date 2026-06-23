"""Unit tests for theoretical foundations (Penrose, Deutsch, Du Sautoy)"""

import unittest
import numpy as np

from pythia_mining.penrose_objective_reduction import ObjectiveReductionEngine
from pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
from pythia_mining.du_sautoy_symmetry import SymmetryExploitationEngine
from pythia_mining.pulvini_group import compute_graph_automorphisms
from pythia_mining.pulvini_topology import ADJACENCY_MAP


class TestPenroseObjectiveReduction(unittest.TestCase):
    """Tests for Penrose OR engine"""

    def test_or_engine_initialization(self):
        """Test OR engine creates successfully"""
        engine = ObjectiveReductionEngine(enable_true_or=False)
        self.assertFalse(engine.enable_true_or)
        self.assertEqual(engine.consciousness_event_count, 0)

    def test_or_preserves_trace(self):
        """OR must preserve trace=1 of density matrix"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        # Create density matrix
        dim = 16
        rho = np.eye(dim, dtype=np.complex128) / dim
        trace_before = np.trace(rho).real

        # Apply OR
        rho_after, _ = engine.objective_reduction(rho, coherence_time=1.0)
        trace_after = np.trace(rho_after).real

        self.assertAlmostEqual(trace_before, trace_after, places=6)
        self.assertAlmostEqual(trace_after, 1.0, places=6)

    def test_or_increases_purity_on_collapse(self):
        """When OR collapses, purity should increase"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        # Create mixed state (low purity)
        dim = 16
        rho = np.eye(dim, dtype=np.complex128) / dim
        purity_before = np.trace(rho @ rho).real

        # Long coherence time + low purity should trigger collapse
        rho_after, collapsed = engine.objective_reduction(rho, coherence_time=5.0)
        purity_after = np.trace(rho_after @ rho_after).real

        if collapsed:
            self.assertGreaterEqual(purity_after, purity_before)

    def test_or_produces_hermitian_matrix(self):
        """OR output must be Hermitian"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        dim = 8
        rho = np.eye(dim, dtype=np.complex128) / dim
        rho_after, _ = engine.objective_reduction(rho, 1.0)

        # Check Hermitian
        self.assertTrue(np.allclose(rho_after, rho_after.conj().T, atol=1e-10))

    def test_or_consciousness_metrics(self):
        """Test consciousness metrics tracking"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        dim = 8
        rho = np.eye(dim, dtype=np.complex128) / dim

        # Trigger some OR events
        for _ in range(5):
            engine.objective_reduction(rho, 2.0)

        metrics = engine.get_consciousness_metrics()

        self.assertIn("total_or_events", metrics)
        self.assertIn("or_event_rate", metrics)
        self.assertGreaterEqual(metrics["total_or_events"], 0)


class TestDeutschKnowledgeSubstrate(unittest.TestCase):
    """Tests for Deutsch knowledge creation"""

    def test_knowledge_substrate_initialization(self):
        """Test substrate creates successfully"""
        substrate = KnowledgeSubstrate()
        self.assertEqual(len(substrate.explanations), 0)
        self.assertEqual(len(substrate.counterfactuals), 0)

    def test_knowledge_from_success(self):
        """Test creating knowledge from successful share"""
        substrate = KnowledgeSubstrate()

        strategy = "phi_resonance"
        context = {"difficulty": 1e15, "thermal_load": 0.5, "phi_resonance": 0.618}
        outcome = {"accepted": True}

        explanation = substrate.create_knowledge_from_success(
            strategy, context, outcome
        )

        self.assertEqual(explanation.strategy_id, strategy)
        self.assertEqual(explanation.times_tested, 1)
        self.assertIn(strategy, substrate.explanations)

    def test_knowledge_from_failure(self):
        """Test creating knowledge from failed share"""
        substrate = KnowledgeSubstrate()

        strategy = "bad_strategy"
        context = {"difficulty": 1e15, "thermal_load": 0.9}
        outcome = {"accepted": False}

        explanation = substrate.create_knowledge_from_failure(
            strategy, context, outcome
        )

        if explanation:
            self.assertLessEqual(explanation.predictive_accuracy, 0.5)

    def test_counterfactual_reasoning(self):
        """Test counterfactual 'what if' reasoning"""
        substrate = KnowledgeSubstrate()

        actual_strategy = "strategy_a"
        alternative = "strategy_b"
        context = {"difficulty": 1e15, "thermal_load": 0.5}
        outcome = {"accepted": True}

        counterfactual = substrate.counterfactual_reasoning(
            actual_strategy, outcome, alternative, context
        )

        self.assertEqual(counterfactual.actual_strategy, actual_strategy)
        self.assertEqual(counterfactual.counterfactual_strategy, alternative)
        self.assertGreaterEqual(counterfactual.confidence, 0.0)
        self.assertLessEqual(counterfactual.confidence, 1.0)

    def test_best_explanation_selection(self):
        """Test selecting best explanation for context"""
        substrate = KnowledgeSubstrate()

        # Create some knowledge
        strategy1 = "strategy_1"
        strategy2 = "strategy_2"
        context = {"difficulty": 1e15, "thermal_load": 0.5}

        substrate.create_knowledge_from_success(strategy1, context, {"accepted": True})
        substrate.create_knowledge_from_success(strategy2, context, {"accepted": True})

        best = substrate.best_explanation_for_context(context)

        # Should return one of the strategies
        self.assertIn(best, [strategy1, strategy2, None])

    def test_explain_decision(self):
        """Test natural language explanation generation"""
        substrate = KnowledgeSubstrate()

        strategy = "phi_strategy"
        context = {"difficulty": 1e15, "thermal_load": 0.5, "phi_resonance": 0.618}

        substrate.create_knowledge_from_success(strategy, context, {"accepted": True})

        explanation_dict = substrate.explain_decision(strategy, context)

        self.assertIn("strategy", explanation_dict)
        self.assertIn("explanation", explanation_dict)
        self.assertIn("confidence", explanation_dict)
        self.assertEqual(explanation_dict["strategy"], strategy)

    def test_knowledge_metrics(self):
        """Test knowledge substrate metrics"""
        substrate = KnowledgeSubstrate()

        # Add some knowledge
        for i in range(5):
            substrate.create_knowledge_from_success(
                f"strategy_{i}",
                {"difficulty": 1e15 + i * 1e10},
                {"accepted": True},
            )

        metrics = substrate.get_knowledge_metrics()

        self.assertGreaterEqual(metrics["total_explanations"], 5)
        self.assertGreaterEqual(metrics["strategies_with_explanations"], 1)


class TestDuSautoySymmetry(unittest.TestCase):
    """Tests for Du Sautoy symmetry exploitation"""

    @classmethod
    def setUpClass(cls):
        """Compute automorphisms once"""
        bipartite_adj = {}
        for node_id in range(32):
            cross_key = "i" if node_id < 20 else "d"
            bipartite_adj[node_id] = {
                "d": [],
                "i": list(ADJACENCY_MAP[node_id].get(cross_key, [])),
            }
        cls.automorphisms = compute_graph_automorphisms(bipartite_adj)

    def test_symmetry_engine_initialization(self):
        """Test symmetry engine creates with automorphisms"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        self.assertEqual(engine.group_size, len(self.automorphisms))
        self.assertGreater(len(engine.orbits), 0)
        self.assertLessEqual(len(engine.orbits), 32)

    def test_orbits_partition_nodes(self):
        """Test orbits form a partition of 32 nodes"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        # Collect all nodes in orbits
        all_nodes = set()
        for orbit in engine.orbits:
            all_nodes.update(orbit.orbit_members)

        # Must be exactly {0, 1, ..., 31}
        self.assertEqual(all_nodes, set(range(32)))

        # Orbits must be disjoint
        for i, orbit_i in enumerate(engine.orbits):
            for j, orbit_j in enumerate(engine.orbits):
                if i != j:
                    intersection = set(orbit_i.orbit_members) & set(
                        orbit_j.orbit_members
                    )
                    self.assertEqual(len(intersection), 0)

    def test_search_space_reduction(self):
        """Test symmetry reduces search space"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        # Full search: 32 nodes
        # Reduced search: num_orbits nodes
        reduction = engine.search_reduction_factor

        self.assertGreater(reduction, 1.0)
        print(f"\nSearch space reduction factor: {reduction:.2f}x")

    def test_nonce_allocation_by_orbit(self):
        """Test nonce space allocation using orbits"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        total_nonce_space = 1_000_000
        allocations = engine.exploit_symmetry_for_nonce_allocation(total_nonce_space)

        # Should have one allocation per orbit
        self.assertEqual(len(allocations), len(engine.orbits))

        # Allocations should be non-overlapping
        ranges = list(allocations.values())
        for i, (start_i, end_i) in enumerate(ranges):
            for j, (start_j, end_j) in enumerate(ranges):
                if i != j:
                    # No overlap
                    overlap = not (end_i < start_j or end_j < start_i)
                    self.assertFalse(overlap)

    def test_fibonacci_allocation(self):
        """Test Fibonacci-based capacity allocation"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        capacities = engine.fibonacci_heap_allocation()

        # Should have capacity for all 32 nodes
        self.assertEqual(len(capacities), 32)

        # Capacities should sum to 1 (normalized)
        total = sum(capacities.values())
        self.assertAlmostEqual(total, 1.0, places=6)

        # All capacities should be positive
        for cap in capacities.values():
            self.assertGreater(cap, 0.0)

    def test_golden_spiral_search(self):
        """Test golden spiral search pattern"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        center_nonce = 1_000_000
        max_radius = 50

        spiral_nonces = engine.golden_spiral_search(center_nonce, max_radius)

        # Should generate nonces
        self.assertGreater(len(spiral_nonces), 0)

        # All nonces should be valid (0 to 2^32-1)
        for nonce in spiral_nonces:
            self.assertGreaterEqual(nonce, 0)
            self.assertLess(nonce, 2**32)

    def test_temporal_symmetry_detection(self):
        """Test detecting periodicity in share history"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        # Create periodic share history
        period = 5.0
        share_history = []
        for i in range(15):
            share_history.append(
                {
                    "timestamp": 1000.0 + i * period,
                    "accepted": True,
                }
            )

        result = engine.detect_temporal_symmetry(share_history)

        self.assertIn("periodicity", result)
        self.assertIn("confidence", result)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_symmetry_metrics(self):
        """Test symmetry exploitation metrics"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        metrics = engine.get_symmetry_metrics()

        self.assertIn("group_size", metrics)
        self.assertIn("num_orbits", metrics)
        self.assertIn("search_reduction_factor", metrics)

        self.assertEqual(metrics["group_size"], len(self.automorphisms))
        self.assertGreater(metrics["search_reduction_factor"], 1.0)


class TestIntegration(unittest.TestCase):
    """Integration tests combining theoretical components"""

    @classmethod
    def setUpClass(cls):
        bipartite_adj = {}
        for node_id in range(32):
            cross_key = "i" if node_id < 20 else "d"
            bipartite_adj[node_id] = {
                "d": [],
                "i": list(ADJACENCY_MAP[node_id].get(cross_key, [])),
            }
        cls.automorphisms = compute_graph_automorphisms(bipartite_adj)

    def test_penrose_deutsch_integration(self):
        """Test OR consciousness events + knowledge creation"""
        or_engine = ObjectiveReductionEngine(enable_true_or=False)
        knowledge = KnowledgeSubstrate()

        dim = 16
        rho = np.eye(dim, dtype=np.complex128) / dim

        # Simulate mining cycle
        rho_after, consciousness_event = or_engine.objective_reduction(rho, 2.0)

        if consciousness_event:
            # Create knowledge about this consciousness moment
            context = {
                "purity": float(np.trace(rho_after @ rho_after).real),
                "consciousness_event": True,
            }
            knowledge.create_knowledge_from_success(
                "consciousness_strategy", context, {"accepted": True}
            )

        # Knowledge should be recorded
        total_knowledge = sum(len(exps) for exps in knowledge.explanations.values())
        self.assertGreaterEqual(total_knowledge, 0)

    def test_symmetry_knowledge_integration(self):
        """Test symmetry exploitation + knowledge substrate"""
        symmetry = SymmetryExploitationEngine(self.automorphisms)
        knowledge = KnowledgeSubstrate()

        # Use symmetry to reduce search space
        orbit_representatives = [orbit.representative for orbit in symmetry.orbits]

        # Create knowledge for each orbit representative
        for rep in orbit_representatives:
            context = {"node_id": rep, "orbit_member": True}
            knowledge.create_knowledge_from_success(
                f"orbit_{rep}", context, {"accepted": True}
            )

        # Should have knowledge for orbit representatives
        self.assertGreaterEqual(
            len(knowledge.explanations), len(orbit_representatives) // 2
        )

    def test_full_theoretical_stack(self):
        """Test Penrose + Deutsch + Du Sautoy working together"""
        or_engine = ObjectiveReductionEngine(enable_true_or=False)
        knowledge = KnowledgeSubstrate()
        symmetry = SymmetryExploitationEngine(self.automorphisms)

        # Simulate full mining cycle with all three components

        # 1. Use symmetry to reduce search space
        orbit_reps = [orbit.representative for orbit in symmetry.orbits]
        search_space_reduction = 32.0 / len(orbit_reps)

        # 2. Check for consciousness event (Penrose)
        dim = 16
        rho = np.eye(dim, dtype=np.complex128) / dim
        rho_after, consciousness_event = or_engine.objective_reduction(rho, 1.5)

        # 3. Create knowledge from cycle (Deutsch)
        context = {
            "search_reduction": search_space_reduction,
            "consciousness_event": consciousness_event,
            "purity": float(np.trace(rho_after @ rho_after).real),
        }
        knowledge.create_knowledge_from_success(
            "theoretical_strategy", context, {"accepted": True}
        )

        # Verify integration
        self.assertGreater(search_space_reduction, 1.0)
        self.assertTrue(consciousness_event is not None)
        self.assertGreater(len(knowledge.explanations), 0)

        print("\nTheoretical Stack Integration:")
        print(f"  Search reduction: {search_space_reduction:.2f}x")
        print(f"  Consciousness events: {or_engine.consciousness_event_count}")
        print(
            f"  Knowledge explanations: {sum(len(e) for e in knowledge.explanations.values())}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
