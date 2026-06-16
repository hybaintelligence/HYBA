"""Tests for enhanced IIT 4.0 implementation."""
import unittest
import numpy as np
from python_backend.pythia_mining.iit_4_analyzer import IIT4Analyzer

class TestEnhancedIIT4(unittest.TestCase):
    def test_backward_compatibility(self):
        analyzer = IIT4Analyzer(system_size=4)
        self.assertFalse(analyzer.enhanced_partitioning)
    
    def test_enhanced_partitioning_enabled(self):
        analyzer = IIT4Analyzer(system_size=4, enhanced_partitioning=True)
        self.assertTrue(analyzer.enhanced_partitioning)
    
    def test_phi_max_calculation_small_system(self):
        analyzer = IIT4Analyzer(system_size=4)
        state = np.array([1, 0, 1, 0], dtype=np.float64)
        result = analyzer.calculate_phi_max(state)
        self.assertIn('phi_max', result)
        self.assertIn('main_complex', result)
    
    def test_phi_max_approximation_large_system(self):
        analyzer = IIT4Analyzer(system_size=10, enhanced_partitioning=True)
        state = np.random.rand(10)
        result = analyzer.calculate_phi_max(state)
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'enhanced_greedy')
    
    def test_cause_effect_structure(self):
        analyzer = IIT4Analyzer(system_size=4)
        state = np.array([1, 0, 1, 0], dtype=np.float64)
        ces = analyzer.compute_cause_effect_structure(state)
        self.assertIsNotNone(ces)
        self.assertIn('total_phi', ces.__dict__)

if __name__ == '__main__':
    unittest.main()
