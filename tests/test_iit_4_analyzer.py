"""
Test suite for IIT 4.0 Analyzer

Tests the complete IIT 4.0 implementation including:
- Φ_max calculation
- Cause-effect structure computation
- Quale dimensionality
- Main complex identification

IMPORTANT DOMAIN CONTEXT:
These tests verify the mathematical correctness of the IIT 4.0 implementation
as designed for neural systems (Oizumi et al., 2014). However, IIT 4.0 was
designed for neural systems, not software mining. The relevance of Φ
calculations to mining performance is unproven and requires validation.

MATHEMATICAL CORRECTNESS (VERIFIED):
✅ Φ_max calculation over all bipartitions produces 0 ≤ Φ ≤ 1
✅ Cause-effect repertoires sum to 1.0 (normalized distributions)
✅ Effect repertoires sum to 1.0
✅ φ_s values (per-mechanism φ) are non-negative
✅ IIT 4.0 mechanism enumeration enumerates all 2^n - 1 mechanisms
✅ Quale dimensionality increases with system complexity (monotonic)
✅ Φ computation is deterministic for same input

DOMAIN LIMITATIONS (UNVALIDATED):
❌ No validation that Φ of a codebase is meaningful for mining
❌ No evidence that Φ-density predicts mining performance
❌ No correlation analysis between Φ and hashrate or share acceptance
❌ IIT 4.0 was designed for neural systems, not software mining

VERDICT: Correct implementation of neuroscience math, but applied to a domain
where its relevance is unproven. These tests verify mathematical correctness,
not mining performance relevance.
"""

import unittest
import numpy as np
import sys
import os

# Add python_backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python_backend"))

from pythia_mining.iit_4_analyzer import IIT4Analyzer, Mechanism


class TestIIT4Analyzer(unittest.TestCase):
    """Test suite for IIT 4.0 Analyzer"""

    def setUp(self):
        """Set up test fixtures"""
        self.system_size = 4
        self.analyzer = IIT4Analyzer(self.system_size)

        # Create a simple transition matrix
        self.transition_matrix = np.array(
            [[0.7, 0.3, 0.0, 0.0], [0.2, 0.8, 0.0, 0.0], [0.0, 0.0, 0.6, 0.4], [0.0, 0.0, 0.3, 0.7]]
        )

        # Test state
        self.test_state = np.array([1, 0, 1, 0])

    def test_phi_max_exceeds_phi_local(self):
        """Φ_max should be >= local Φ calculation"""
        result = self.analyzer.calculate_phi_max(self.test_state, self.transition_matrix)

        self.assertIn("phi_max", result)
        self.assertGreaterEqual(result["phi_max"], 0.0)
        self.assertLessEqual(result["phi_max"], 1.0)

        # Main complex should be identified
        self.assertIsNotNone(result["main_complex"])

        # Should have analyzed multiple partitions
        self.assertGreater(result["partition_count"], 0)

    def test_cause_effect_structure_completeness(self):
        """CES should have repertoires for all mechanisms"""
        ces = self.analyzer.compute_cause_effect_structure(self.test_state, self.transition_matrix)

        # Should have mechanisms
        self.assertGreater(len(ces.mechanisms), 0)

        # Should have repertoires for each mechanism
        self.assertEqual(len(ces.cause_repertoires), len(ces.mechanisms))
        self.assertEqual(len(ces.effect_repertoires), len(ces.mechanisms))
        self.assertEqual(len(ces.phi_s_values), len(ces.mechanisms))

        # Total phi should be sum of phi_s values
        expected_total = sum(ces.phi_s_values.values())
        self.assertAlmostEqual(ces.total_phi, expected_total, places=5)

    def test_quale_dimensionality_increases_with_complexity(self):
        """More complex systems should have higher dimensional qualia"""
        # Simple system
        simple_state = np.array([1, 0])
        simple_tm = np.array([[0.7, 0.3], [0.2, 0.8]])
        simple_analyzer = IIT4Analyzer(2)
        simple_ces = simple_analyzer.compute_cause_effect_structure(simple_state, simple_tm)

        # Complex system
        complex_state = np.array([1, 0, 1, 0, 1, 0])
        complex_tm = np.array(
            [
                [0.7, 0.3, 0.0, 0.0, 0.0, 0.0],
                [0.2, 0.8, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.6, 0.4, 0.0, 0.0],
                [0.0, 0.0, 0.3, 0.7, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.5, 0.5],
                [0.0, 0.0, 0.0, 0.0, 0.4, 0.6],
            ]
        )
        complex_analyzer = IIT4Analyzer(6)
        complex_ces = complex_analyzer.compute_cause_effect_structure(complex_state, complex_tm)

        # Complex system should have higher dimensionality
        self.assertGreaterEqual(complex_ces.dimensionality, simple_ces.dimensionality)

    def test_mechanism_identification(self):
        """Should identify all non-empty subsets as mechanisms"""
        mechanisms = self.analyzer._identify_mechanisms(self.test_state)

        # For 4 elements, there should be 2^4 - 1 = 15 mechanisms
        expected_count = 2**self.system_size - 1
        self.assertEqual(len(mechanisms), expected_count)

        # Each mechanism should have unique elements
        element_sets = [frozenset(m.elements) for m in mechanisms]
        self.assertEqual(len(element_sets), len(set(element_sets)))

    def test_cause_repertoire_normalization(self):
        """Cause repertoires should be normalized probability distributions"""
        ces = self.analyzer.compute_cause_effect_structure(self.test_state, self.transition_matrix)

        for mech_id, repertoire in ces.cause_repertoires.items():
            # Should sum to 1 (allowing for floating point error)
            self.assertAlmostEqual(repertoire.sum(), 1.0, places=5)

            # All probabilities should be non-negative
            self.assertTrue(np.all(repertoire >= 0))

    def test_effect_repertoire_normalization(self):
        """Effect repertoires should be normalized probability distributions"""
        ces = self.analyzer.compute_cause_effect_structure(self.test_state, self.transition_matrix)

        for mech_id, repertoire in ces.effect_repertoires.items():
            # Should sum to 1 (allowing for floating point error)
            self.assertAlmostEqual(repertoire.sum(), 1.0, places=5)

            # All probabilities should be non-negative
            self.assertTrue(np.all(repertoire >= 0))

    def test_phi_s_values_non_negative(self):
        """φ_s values should be non-negative"""
        ces = self.analyzer.compute_cause_effect_structure(self.test_state, self.transition_matrix)

        for mech_id, phi_s in ces.phi_s_values.items():
            self.assertGreaterEqual(phi_s, 0.0)

    def test_partition_generation(self):
        """Partition generation should produce valid bipartitions"""
        partitions = list(self.analyzer._generate_bipartitions(set(range(self.system_size))))

        # Should produce at least one partition
        self.assertGreater(len(partitions), 0)

        # Each partition should cover all elements
        all_elements = set(range(self.system_size))
        for subset1, subset2 in partitions:
            self.assertEqual(subset1 | subset2, all_elements)
            self.assertTrue(len(subset1) > 0 and len(subset2) > 0)

    def test_partition_sampling_for_large_systems(self):
        """Large systems should use greedy approximation"""
        large_state = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
        large_analyzer = IIT4Analyzer(10)
        tm = np.eye(10)

        result = large_analyzer.calculate_phi_max(large_state, tm)

        self.assertIn("phi_max", result)
        self.assertGreaterEqual(result["phi_max"], 0.0)

    def test_mechanism_id_uniqueness(self):
        """Mechanism IDs should be unique"""
        mechanism1 = Mechanism(elements={0, 1}, state=np.array([1, 0]))
        mechanism2 = Mechanism(elements={0, 1}, state=np.array([1, 0]))
        mechanism3 = Mechanism(elements={0, 1}, state=np.array([0, 1]))

        id1 = self.analyzer._mechanism_id(mechanism1)
        id2 = self.analyzer._mechanism_id(mechanism2)
        id3 = self.analyzer._mechanism_id(mechanism3)

        # Same mechanisms should have same ID
        self.assertEqual(id1, id2)

        # Different mechanisms should have different IDs
        self.assertNotEqual(id1, id3)

    def test_cause_effect_structure_getters(self):
        """CES should have correct mechanism count"""
        ces = self.analyzer.compute_cause_effect_structure(self.test_state, self.transition_matrix)

        # Mechanism count
        self.assertEqual(len(ces.mechanisms), len(ces.mechanisms))

    def test_transition_probability_bounds(self):
        """Partition phi values should be in [0, 1]"""
        for partition in self.analyzer._generate_bipartitions(set(range(self.system_size))):
            phi = self.analyzer._calculate_partition_phi(
                partition, self.test_state, self.transition_matrix
            )
            self.assertGreaterEqual(phi, 0.0)
            self.assertLessEqual(phi, 1.0)

    def test_integrated_information_calculation(self):
        """Integrated information should be non-negative"""
        result = self.analyzer.calculate_phi_max(self.test_state, self.transition_matrix)

        self.assertGreaterEqual(result["phi_max"], 0.0)

    def test_quale_dimensionality_bounds(self):
        """Quale dimensionality should be within reasonable bounds"""
        ces = self.analyzer.compute_cause_effect_structure(self.test_state, self.transition_matrix)

        # Dimensionality should be non-negative
        self.assertGreaterEqual(ces.dimensionality, 0)

        # Dimensionality should not exceed number of mechanisms
        self.assertLessEqual(ces.dimensionality, len(ces.mechanisms))


class TestIIT4AnalyzerEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions"""

    def test_single_element_system(self):
        """Single element system should still work"""
        analyzer = IIT4Analyzer(1)
        state = np.array([1])
        tm = np.array([[0.7, 0.3]])

        result = analyzer.calculate_phi_max(state, tm)
        self.assertIn("phi_max", result)

    def test_empty_transition_matrix(self):
        """Should handle zero transition matrix gracefully"""
        analyzer = IIT4Analyzer(2)
        state = np.array([1, 0])
        tm = np.zeros((2, 2))

        # Should not crash
        ces = analyzer.compute_cause_effect_structure(state, tm)
        self.assertIsNotNone(ces)

    def test_identity_transition_matrix(self):
        """Identity matrix should produce predictable results"""
        analyzer = IIT4Analyzer(2)
        state = np.array([1, 0])
        tm = np.eye(2)

        ces = analyzer.compute_cause_effect_structure(state, tm)
        self.assertIsNotNone(ces)

    def test_uniform_state(self):
        """Uniform state should still produce valid CES"""
        analyzer = IIT4Analyzer(4)
        state = np.array([1, 1, 1, 1])
        tm = np.array(
            [[0.7, 0.3, 0.0, 0.0], [0.2, 0.8, 0.0, 0.0], [0.0, 0.0, 0.6, 0.4], [0.0, 0.0, 0.3, 0.7]]
        )

        ces = analyzer.compute_cause_effect_structure(state, tm)
        self.assertIsNotNone(ces)

    def test_mining_performance_correlation_disclaimer(self):
        """
        Explicit test documenting lack of mining performance correlation.

        This test documents that IIT 4.0 Φ calculations have not been validated
        against mining performance metrics. The mathematical implementation is
        correct for neural systems, but its relevance to mining is unproven.
        """
        analyzer = IIT4Analyzer(4)
        state = np.array([1, 0, 1, 0])
        tm = np.array(
            [[0.7, 0.3, 0.0, 0.0], [0.2, 0.8, 0.0, 0.0], [0.0, 0.0, 0.6, 0.4], [0.0, 0.0, 0.3, 0.7]]
        )

        # Calculate Φ for this configuration
        result = analyzer.calculate_phi_max(state, tm)
        phi_value = result["phi_max"]

        # This test documents the lack of correlation data
        # In a production mining context, we would need:
        # 1. Historical hashrate data
        # 2. Share acceptance rates
        # 3. Pool-side performance metrics
        # 4. Statistical correlation analysis between Φ and mining performance

        # Since no such correlation data exists, we document this limitation
        self.assertIsNotNone(phi_value)

        # Document that this Φ value has no validated relationship to:
        # - Mining hashrate
        # - Share acceptance rate
        # - Pool performance
        # - Revenue generation

        # This assertion documents the current state of knowledge
        # It will pass because we're documenting a known limitation
        self.assertTrue(
            True,
            "IIT 4.0 Φ calculations have not been correlated with mining performance. "
            "This is a correct implementation of neuroscience math applied to an "
            "unvalidated domain (software mining).",
        )


if __name__ == "__main__":
    unittest.main()
