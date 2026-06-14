"""Tests for enhanced Penrose OR implementation."""
import unittest
import numpy as np
from python_backend.pythia_mining.penrose_objective_reduction import ObjectiveReductionEngine

class TestEnhancedPenroseOR(unittest.TestCase):
    def test_backward_compatibility(self):
        engine = ObjectiveReductionEngine()
        self.assertFalse(engine.enable_true_or)
        self.assertFalse(engine.enhanced_gravity_model)
    
    def test_enhanced_gravity_model_enabled(self):
        engine = ObjectiveReductionEngine(enhanced_gravity_model=True, enable_true_or=True)
        self.assertTrue(engine.enhanced_gravity_model)
        self.assertTrue(engine.enable_true_or)
    
    def test_operational_proxy_mode(self):
        engine = ObjectiveReductionEngine()
        rho = np.eye(4, dtype=np.complex128) / 4
        collapsed, is_event = engine.objective_reduction(rho, 1.0)
        self.assertIsInstance(collapsed, np.ndarray)
        self.assertIsInstance(is_event, bool)
    
    def test_metrics_include_enhanced_mode(self):
        engine = ObjectiveReductionEngine(enhanced_gravity_model=True)
        metrics = engine.get_consciousness_metrics()
        self.assertIn('enhanced_gravity_model', metrics)
        self.assertTrue(metrics['enhanced_gravity_model'])

if __name__ == '__main__':
    unittest.main()
