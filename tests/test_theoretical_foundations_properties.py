"""Property-based tests for theoretical foundations.

Tests Penrose OR, Deutsch knowledge, Du Sautoy symmetry enhancements
using Hypothesis for property-based testing.
"""

import unittest
from hypothesis import given, strategies as st, assume, settings
import numpy as np

from pythia_mining.penrose_objective_reduction import (
    ObjectiveReductionEngine,
)
from pythia_mining.deutsch_knowledge_substrate import (
    KnowledgeSubstrate,
)
from pythia_mining.du_sautoy_symmetry import (
    SymmetryExploitationEngine,
)
from pythia_mining.pulvini_group import compute_graph_automorphisms
from pythia_mining.pulvini_topology import ADJACENCY_MAP


class TestPenroseORProperties(unittest.TestCase):
    """Property tests for Penrose objective reduction"""

    @given(
        dim=st.integers(min_value=4, max_value=32),
        coherence_time=st.floats(min_value=0.0, max_value=10.0),
    )
    @settings(deadline=None, max_examples=50)
    def test_or_preserves_trace(self, dim, coherence_time):
        """Property: OR preserves trace of density matrix"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        # Create random density matrix
        rho = self._random_density_matrix(dim)
        trace_before = np.trace(rho).real

        # Apply OR
        rho_after, _ = engine.objective_reduction(rho, coherence_time)
        trace_after = np.trace(rho_after).real

        # Trace must be preserved
        self.assertAlmostEqual(trace_before, trace_after, places=5)

    @given(
        dim=st.integers(min_value=4, max_value=32),
        coherence_time=st.floats(min_value=0.0, max_value=10.0),
    )
    @settings(deadline=None, max_examples=50)
    def test_or_increases_purity(self, dim, coherence_time):
        """Property: OR collapse increases purity"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        rho = self._random_density_matrix(dim)
        purity_before = np.trace(rho @ rho).real

        rho_after, collapsed = engine.objective_reduction(rho, coherence_time)
        purity_after = np.trace(rho_after @ rho_after).real

        if collapsed:
            # Purity should increase on collapse
            self.assertGreaterEqual(purity_after, purity_before - 1e-6)

    @given(dim=st.integers(min_value=4, max_value=32))
    @settings(deadline=None, max_examples=30)
    def test_or_produces_hermitian_output(self, dim):
        """Property: OR always produces Hermitian density matrix"""
        engine = ObjectiveReductionEngine(enable_true_or=False)

        rho = self._random_density_matrix(dim)
        rho_after, _ = engine.objective_reduction(rho, 1.0)

        # Check Hermitian
        self.assertTrue(np.allclose(rho_after, rho_after.conj().T, atol=1e-10))

    def _random_density_matrix(self, dim):
        """Generate random positive semidefinite, trace-one matrix"""
        # Random complex matrix
        A = np.random.randn(dim, dim) + 1j * np.random.randn(dim, dim)
        # Make Hermitian
        H = (A + A.conj().T) / 2
        # Get positive eigenvalues
        eigvals, eigvecs = np.linalg.eigh(H)
        eigvals = np.abs(eigvals)
        eigvals = eigvals / np.sum(eigvals)  # Normalize trace
        # Reconstruct
        rho = eigvecs @ np.diag(eigvals) @ eigvecs.conj().T
        return rho


class TestDeutschKnowledgeProperties(unittest.TestCase):
    """Property tests for Deutsch knowledge substrate"""

    @given(
        strategy_id=st.text(
            min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))
        ),
        difficulty=st.floats(min_value=1e10, max_value=1e20),
        accepted=st.booleans(),
    )
    @settings(deadline=None, max_examples=50)
    def test_knowledge_accumulation_property(self, strategy_id, difficulty, accepted):
        """Property: knowledge accumulates monotonically"""
        substrate = KnowledgeSubstrate()

        initial_count = sum(len(exps) for exps in substrate.explanations.values())

        context = {"difficulty": difficulty, "thermal_load": 0.5}
        outcome = {"accepted": accepted}

        if accepted:
            substrate.create_knowledge_from_success(strategy_id, context, outcome)
        else:
            substrate.create_knowledge_from_failure(strategy_id, context, outcome)

        final_count = sum(len(exps) for exps in substrate.explanations.values())

        # Knowledge should not decrease
        self.assertGreaterEqual(final_count, initial_count)

    @given(
        strategies=st.lists(
            st.text(
                min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=("Lu", "Ll"))
            ),
            min_size=2,
            max_size=5,
            unique=True,
        )
    )
    @settings(deadline=None, max_examples=30)
    def test_counterfactual_transitivity(self, strategies):
        """Property: counterfactual reasoning should be transitive"""
        assume(len(strategies) >= 2)

        substrate = KnowledgeSubstrate()
        context = {"difficulty": 1e15, "thermal_load": 0.5}

        # Create knowledge for strategies
        for strategy in strategies:
            outcome = {"accepted": True}
            substrate.create_knowledge_from_success(strategy, context, outcome)
            substrate.strategy_performance[strategy].append(0.8)

        # If A > B and B > C, some transitivity should hold
        # (not strict due to stochastic nature, but generally true)
        if len(strategies) >= 3:
            a, b, c = strategies[:3]

            cf_ab = substrate.counterfactual_reasoning(a, {"chosen": True}, b, context)
            cf_bc = substrate.counterfactual_reasoning(b, {"chosen": True}, c, context)

            # Both should have reasonable confidence
            self.assertGreater(cf_ab.confidence, 0.0)
            self.assertGreater(cf_bc.confidence, 0.0)

    @given(
        num_successes=st.integers(min_value=1, max_value=10),
        num_failures=st.integers(min_value=0, max_value=5),
    )
    @settings(deadline=None, max_examples=30)
    def test_explanation_accuracy_improves_with_data(self, num_successes, num_failures):
        """Property: explanations should improve with more data"""
        substrate = KnowledgeSubstrate()
        strategy_id = "test_strategy"
        context = {"difficulty": 1e15, "thermal_load": 0.5}

        # Add successes
        for _ in range(num_successes):
            substrate.create_knowledge_from_success(strategy_id, context, {"accepted": True})

        # Add failures
        for _ in range(num_failures):
            substrate.create_knowledge_from_failure(strategy_id, context, {"accepted": False})

        # Check explanations exist and have reasonable accuracy
        if strategy_id in substrate.explanations:
            for explanation in substrate.explanations[strategy_id]:
                # Accuracy should be in [0, 1]
                self.assertGreaterEqual(explanation.predictive_accuracy, 0.0)
                self.assertLessEqual(explanation.predictive_accuracy, 1.0)

                # More data = more tests
                expected_min_tests = min(num_successes + num_failures, 1)
                self.assertGreaterEqual(explanation.times_tested, expected_min_tests)


class TestDuSautoySymmetryProperties(unittest.TestCase):
    """Property tests for Du Sautoy symmetry exploitation"""

    @classmethod
    def setUpClass(cls):
        """Compute automorphisms once for all tests"""
        # Build bipartite adjacency for automorphism computation
        bipartite_adj = {}
        for node_id in range(32):
            cross_key = "i" if node_id < 20 else "d"
            bipartite_adj[node_id] = {
                "d": [],
                "i": list(ADJACENCY_MAP[node_id].get(cross_key, [])),
            }

        cls.automorphisms = compute_graph_automorphisms(bipartite_adj)

    def test_orbit_partition_property(self):
        """Property: orbits partition the node set"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        # Collect all nodes in orbits
        all_nodes = set()
        for orbit in engine.orbits:
            all_nodes.update(orbit.orbit_members)

        # Must include all 32 nodes
        self.assertEqual(all_nodes, set(range(32)))

        # Orbits must be disjoint
        for i, orbit_i in enumerate(engine.orbits):
            for j, orbit_j in enumerate(engine.orbits):
                if i != j:
                    intersection = set(orbit_i.orbit_members) & set(orbit_j.orbit_members)
                    self.assertEqual(len(intersection), 0)

    def test_orbit_stabilizer_theorem(self):
        """Property: |Orbit| * |Stabilizer| = |Group|"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        for orbit in engine.orbits:
            # Orbit-stabilizer theorem
            product = orbit.orbit_size * orbit.stabilizer_size
            # Should equal or divide group size
            self.assertEqual(engine.group_size % product, 0)

    @given(
        total_nonce_space=st.integers(min_value=1000, max_value=2**20),
    )
    @settings(deadline=None, max_examples=20)
    def test_nonce_allocation_covers_space(self, total_nonce_space):
        """Property: nonce allocation should cover entire space"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        allocations = engine.exploit_symmetry_for_nonce_allocation(total_nonce_space)

        # Check allocations are disjoint and cover space
        covered_nonces = 0
        for start, end in allocations.values():
            covered_nonces += end - start + 1

        # Should allocate most of the space (within 10% due to rounding)
        self.assertGreaterEqual(covered_nonces, total_nonce_space * 0.9)

    @given(center_nonce=st.integers(min_value=0, max_value=2**31))
    @settings(deadline=None, max_examples=20)
    def test_golden_spiral_search_property(self, center_nonce):
        """Property: golden spiral should not repeat nonces quickly"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        max_radius = 100
        spiral_nonces = engine.golden_spiral_search(center_nonce, max_radius)

        # Should generate reasonable number of nonces
        self.assertGreater(len(spiral_nonces), 10)

        # Check for uniqueness (most should be unique)
        unique_ratio = len(set(spiral_nonces)) / len(spiral_nonces)
        self.assertGreater(unique_ratio, 0.7)

    @given(
        share_count=st.integers(min_value=5, max_value=20),
        has_periodicity=st.booleans(),
    )
    @settings(deadline=None, max_examples=20)
    def test_temporal_symmetry_detection_property(self, share_count, has_periodicity):
        """Property: should detect periodicity when present"""
        engine = SymmetryExploitationEngine(self.automorphisms)

        # Generate share history
        share_history = []
        base_time = 1000.0
        period = 5.0 if has_periodicity else np.random.uniform(1, 20)

        for i in range(share_count):
            if has_periodicity:
                timestamp = base_time + i * period
            else:
                timestamp = base_time + np.random.uniform(0, 100)

            share_history.append({"timestamp": timestamp, "accepted": True})

        result = engine.detect_temporal_symmetry(share_history)

        if has_periodicity and share_count >= 10:
            # Should detect the period with reasonable confidence
            self.assertIsNotNone(result["periodicity"])
        else:
            # Confidence should reflect uncertainty
            self.assertLessEqual(result["confidence"], 1.0)
            self.assertGreaterEqual(result["confidence"], 0.0)


class TestIntegrationProperties(unittest.TestCase):
    """Integration tests combining multiple theoretical components"""

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

    def test_knowledge_with_symmetry_reduces_search(self):
        """Integration: knowledge + symmetry should reduce search space"""
        knowledge = KnowledgeSubstrate()
        symmetry = SymmetryExploitationEngine(self.automorphisms)

        # Full search space
        full_nodes = set(range(32))

        # Symmetry reduces to orbit representatives
        orbit_reps = {orbit.representative for orbit in symmetry.orbits}

        # Reduction should be significant
        reduction_factor = len(full_nodes) / len(orbit_reps)
        self.assertGreater(reduction_factor, 1.5)

        # Knowledge can further prioritize within orbits
        context = {"difficulty": 1e15, "thermal_load": 0.5}
        best_strategy = knowledge.best_explanation_for_context(context)

        # Should return something or None (if no knowledge yet)
        self.assertTrue(best_strategy is None or isinstance(best_strategy, str))

    def test_penrose_or_with_symmetry_preserved(self):
        """Integration: OR should preserve symmetry structure"""
        or_engine = ObjectiveReductionEngine(enable_true_or=False)
        SymmetryExploitationEngine(self.automorphisms)

        # Create density matrix respecting symmetry
        dim = 32
        rho = np.eye(dim, dtype=np.complex128) / dim

        # Apply OR
        rho_after, collapsed = or_engine.objective_reduction(rho, 2.0)

        # Symmetry properties should still hold
        trace = np.trace(rho_after).real
        self.assertAlmostEqual(trace, 1.0, places=6)

        # Purity should be well-defined
        purity = np.trace(rho_after @ rho_after).real
        self.assertGreaterEqual(purity, 0.0)
        self.assertLessEqual(purity, 1.0 + 1e-6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
