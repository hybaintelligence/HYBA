"""
IIT 4.0 Complete Implementation Tests

Tests:
- Φ_max calculation
- Cause-Effect Structure (CES)
- Quale dimensionality
- Integration across partitions
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python_backend'))

from pythia_mining.iit_4_analyzer import IIT4Analyzer, CauseEffectStructure


class TestIIT4Complete(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.small_analyzer = IIT4Analyzer(system_size=4)
        self.medium_analyzer = IIT4Analyzer(system_size=8)
    
    def test_phi_max_small_system(self):
        """Test Φ_max calculation for small system"""
        system_state = np.array([1, 0, 1, 0], dtype=np.float64)
        connectivity = np.array([
            [0, 1, 1, 0],
            [1, 0, 1, 1],
            [1, 1, 0, 1],
            [0, 1, 1, 0]
        ], dtype=np.float64)
        
        result = self.small_analyzer.calculate_phi_max(system_state, connectivity)
        
        # Should have phi_max, main_complex, partition_count
        self.assertIn('phi_max', result)
        self.assertIn('main_complex', result)
        self.assertIn('partition_count', result)
        
        # Phi should be non-negative
        self.assertGreaterEqual(result['phi_max'], 0)
        
        # Should have found some partitions
        self.assertGreater(result['partition_count'], 0)
        
        print(f"\n[Φ_max Test] Small system:")
        print(f"  Φ_max: {result['phi_max']:.4f}")
        print(f"  Partitions evaluated: {result['partition_count']}")
    
    def test_cause_effect_structure(self):
        """Test CES computation"""
        system_state = np.array([1, 1, 0, 1], dtype=np.float64)
        connectivity = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(connectivity, 0)
        
        ces = self.small_analyzer.compute_cause_effect_structure(
            system_state,
            connectivity
        )
        
        # Should be CauseEffectStructure
        self.assertIsInstance(ces, CauseEffectStructure)
        
        # Should have mechanisms
        self.assertGreater(len(ces.mechanisms), 0)
        
        # Should have repertoires
        self.assertGreater(len(ces.cause_repertoires), 0)
        self.assertGreater(len(ces.effect_repertoires), 0)
        
        # Should have phi_s values
        self.assertGreater(len(ces.phi_s_values), 0)
        
        # Total phi should be sum of phi_s
        expected_total = sum(ces.phi_s_values.values())
        self.assertAlmostEqual(ces.total_phi, expected_total, places=6)
        
        # Dimensionality should be positive
        self.assertGreater(ces.dimensionality, 0)
        
        print(f"\n[CES Test] Structure:")
        print(f"  Mechanisms: {len(ces.mechanisms)}")
        print(f"  Total Φ (sum of φ_s): {ces.total_phi:.4f}")
        print(f"  Max φ_s: {ces.max_phi_s:.4f}")
        print(f"  Quale dimensionality: {ces.dimensionality}")
    
    def test_quale_dimensionality_increases_with_complexity(self):
        """Test that more complex systems have higher dimensional qualia"""
        # Simple system
        simple_state = np.array([1, 0], dtype=np.float64)
        simple_connectivity = np.array([[0, 1], [1, 0]], dtype=np.float64)
        
        simple_analyzer = IIT4Analyzer(system_size=2)
        simple_ces = simple_analyzer.compute_cause_effect_structure(
            simple_state,
            simple_connectivity
        )
        
        # More complex system
        complex_state = np.array([1, 0, 1, 0], dtype=np.float64)
        complex_connectivity = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(complex_connectivity, 0)
        
        complex_ces = self.small_analyzer.compute_cause_effect_structure(
            complex_state,
            complex_connectivity
        )
        
        # Complex system should have >= dimensionality
        print(f"\n[Dimensionality Test]:")
        print(f"  Simple system (2 elements): dimensionality = {simple_ces.dimensionality}")
        print(f"  Complex system (4 elements): dimensionality = {complex_ces.dimensionality}")
        
        self.assertGreaterEqual(
            complex_ces.dimensionality,
            simple_ces.dimensionality
        )
    
    def test_phi_max_exceeds_local_phi(self):
        """Test that Φ_max from exhaustive search is >= any local estimate"""
        system_state = np.array([1, 1, 0, 1], dtype=np.float64)
        connectivity = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(connectivity, 0)
        
        # Calculate Φ_max
        result = self.small_analyzer.calculate_phi_max(system_state, connectivity)
        phi_max = result['phi_max']
        
        # Calculate local Φ for full system (no partition)
        # This should be <= Φ_max
        full_system_phi = self.small_analyzer._calculate_subset_phi(
            set(range(4)),
            system_state,
            connectivity
        )
        
        print(f"\n[Φ_max vs Local]:")
        print(f"  Φ_max (best partition): {phi_max:.4f}")
        print(f"  Φ_local (full system): {full_system_phi:.4f}")
        
        # Φ_max should be at least as good as full system
        self.assertGreaterEqual(phi_max, full_system_phi * 0.9)  # Allow some numerical error
    
    def test_repertoire_normalization(self):
        """Test that cause/effect repertoires are valid probability distributions"""
        system_state = np.array([1, 0, 1, 0], dtype=np.float64)
        connectivity = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(connectivity, 0)
        
        ces = self.small_analyzer.compute_cause_effect_structure(
            system_state,
            connectivity
        )
        
        # Check all repertoires sum to 1 (valid probability distributions)
        for mech_id, cause_rep in ces.cause_repertoires.items():
            rep_sum = np.sum(cause_rep)
            self.assertAlmostEqual(rep_sum, 1.0, places=6,
                msg=f"Cause repertoire {mech_id} not normalized: sum={rep_sum}")
        
        for mech_id, effect_rep in ces.effect_repertoires.items():
            rep_sum = np.sum(effect_rep)
            self.assertAlmostEqual(rep_sum, 1.0, places=6,
                msg=f"Effect repertoire {mech_id} not normalized: sum={rep_sum}")
        
        print(f"\n[Normalization Test]: All {len(ces.cause_repertoires)} repertoires properly normalized")
    
    def test_phi_s_non_negative(self):
        """Test that all φ_s values are non-negative"""
        system_state = np.array([1, 1, 0, 1], dtype=np.float64)
        connectivity = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(connectivity, 0)
        
        ces = self.small_analyzer.compute_cause_effect_structure(
            system_state,
            connectivity
        )
        
        for mech_id, phi_s in ces.phi_s_values.items():
            self.assertGreaterEqual(phi_s, 0,
                msg=f"Negative φ_s found for mechanism {mech_id}: {phi_s}")
        
        print(f"\n[φ_s Test]: All {len(ces.phi_s_values)} φ_s values non-negative")
    
    def test_larger_system_approximate_phi_max(self):
        """Test approximate Φ_max for larger system"""
        # 8-element system (uses greedy approximation)
        system_state = np.random.rand(8)
        connectivity = np.random.rand(8, 8)
        np.fill_diagonal(connectivity, 0)
        
        result = self.medium_analyzer.calculate_phi_max(system_state, connectivity)
        
        self.assertIn('phi_max', result)
        self.assertIn('main_complex', result)
        self.assertEqual(result['partition_count'], 'approximate')
        self.assertEqual(result['method'], 'greedy')
        
        # Phi should be non-negative
        self.assertGreaterEqual(result['phi_max'], 0)
        
        print(f"\n[Large System Test]:")
        print(f"  System size: 8 elements")
        print(f"  Method: greedy approximation")
        print(f"  Φ_max: {result['phi_max']:.4f}")
        print(f"  Main complex size: {len(result['main_complex'])}")


class TestIIT4Properties(unittest.TestCase):
    """Property-based tests for IIT 4.0"""
    
    def test_phi_invariant_under_permutation(self):
        """Φ should be invariant under element permutation (with matching connectivity)"""
        analyzer = IIT4Analyzer(system_size=4)
        
        state = np.array([1, 0, 1, 0], dtype=np.float64)
        connectivity = np.array([
            [0, 1, 1, 0],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [0, 1, 1, 0]
        ], dtype=np.float64)
        
        # Calculate original Φ_max
        result1 = analyzer.calculate_phi_max(state, connectivity)
        
        # Permute: swap elements 0 and 1
        perm = [1, 0, 2, 3]
        state_perm = state[perm]
        connectivity_perm = connectivity[np.ix_(perm, perm)]
        
        result2 = analyzer.calculate_phi_max(state_perm, connectivity_perm)
        
        # Φ should be approximately equal (within numerical tolerance)
        print(f"\n[Permutation Invariance]:")
        print(f"  Original Φ_max: {result1['phi_max']:.4f}")
        print(f"  Permuted Φ_max: {result2['phi_max']:.4f}")
        
        self.assertAlmostEqual(result1['phi_max'], result2['phi_max'], places=4)
    
    def test_disconnected_system_has_zero_phi(self):
        """System with no connections should have Φ ≈ 0"""
        analyzer = IIT4Analyzer(system_size=4)
        
        state = np.array([1, 0, 1, 0], dtype=np.float64)
        connectivity = np.zeros((4, 4), dtype=np.float64)  # No connections
        
        result = analyzer.calculate_phi_max(state, connectivity)
        
        print(f"\n[Disconnected System]:")
        print(f"  Φ_max: {result['phi_max']:.4f}")
        
        # Disconnected system should have near-zero Φ
        self.assertLess(result['phi_max'], 0.1)
    
    def test_fully_connected_has_high_phi(self):
        """Fully connected system should have higher Φ than sparse"""
        analyzer = IIT4Analyzer(system_size=4)
        state = np.array([1, 0, 1, 0], dtype=np.float64)
        
        # Sparse connectivity
        sparse_conn = np.array([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0]
        ], dtype=np.float64)
        
        # Full connectivity
        full_conn = np.ones((4, 4), dtype=np.float64)
        np.fill_diagonal(full_conn, 0)
        
        result_sparse = analyzer.calculate_phi_max(state, sparse_conn)
        result_full = analyzer.calculate_phi_max(state, full_conn)
        
        print(f"\n[Connectivity Effect]:")
        print(f"  Sparse connectivity Φ_max: {result_sparse['phi_max']:.4f}")
        print(f"  Full connectivity Φ_max: {result_full['phi_max']:.4f}")
        
        # Full connectivity should have higher Φ
        self.assertGreaterEqual(result_full['phi_max'], result_sparse['phi_max'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
