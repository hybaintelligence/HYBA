"""Tests for enhanced Deutsch knowledge substrate implementation."""
import unittest
from python_backend.pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate

class TestEnhancedDeutsch(unittest.TestCase):
    def test_backward_compatibility(self):
        substrate = KnowledgeSubstrate()
        self.assertIsNotNone(substrate.explanations)
        self.assertIsNotNone(substrate.counterfactuals)
    
    def test_enhanced_explanation_generation(self):
        substrate = KnowledgeSubstrate()
        context = {
            'difficulty': 1000000,
            'thermal_load': 0.5,
            'phi_resonance': 0.618,
            'pool_latency': 45
        }
        outcome = {'accepted': True}
        
        explanation = substrate.create_knowledge_from_success('strategy_a', context, outcome)
        self.assertIn('φ-resonance', explanation.explanation_text)
        self.assertIn('thermal', explanation.explanation_text.lower())
    
    def test_enhanced_failure_analysis(self):
        substrate = KnowledgeSubstrate()
        context = {
            'difficulty': 1000000,
            'thermal_load': 0.9,
            'phi_resonance': 0.2,
            'pool_latency': 250
        }
        outcome = {'accepted': False}
        
        explanation = substrate.create_knowledge_from_failure('strategy_b', context, outcome)
        if explanation:
            self.assertIn('failed', explanation.explanation_text.lower())
    
    def test_enhanced_counterfactual_simulation(self):
        substrate = KnowledgeSubstrate()
        substrate.strategy_performance['strategy_a'] = [0.8, 0.9, 0.7]
        
        context = {
            'thermal_load': 0.5,
            'phi_resonance': 0.6,
            'pool_latency': 50
        }
        
        counterfactual = substrate.counterfactual_reasoning(
            'strategy_a', {'accepted': True}, 'strategy_b', context
        )
        
        self.assertIn('predicted_acceptance', counterfactual.predicted_counterfactual_outcome)
        self.assertIn('confidence', counterfactual.predicted_counterfactual_outcome)
    
    def test_context_aware_modeling(self):
        substrate = KnowledgeSubstrate()
        substrate.strategy_performance['strategy_a'] = [0.7, 0.8]
        
        context = {
            'thermal_load': 0.5,
            'phi_resonance': 0.6,
            'pool_latency': 50
        }
        
        simulation = substrate._simulate_alternative_strategy('strategy_a', context)
        
        # Enhanced simulation should include context factors
        self.assertIn('context_factors', simulation)
        self.assertIn('thermal', simulation['context_factors'])
        self.assertIn('phi', simulation['context_factors'])
        self.assertIn('latency', simulation['context_factors'])

if __name__ == '__main__':
    unittest.main()
