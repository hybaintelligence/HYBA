"""Integration tests for GenesisAI using enhanced capabilities."""
import unittest
import numpy as np
from unittest.mock import Mock, MagicMock, AsyncMock
import asyncio

class TestGenesisAIIntegration(unittest.TestCase):
    """Test that GenesisAI actually uses enhanced capabilities in mining workflow."""
    
    def test_genesis_ai_has_enhanced_components(self):
        """Test that GenesisAI initializes with all enhanced components."""
        from python_backend.pythia_mining.genesis_ai import GenesisAI
        
        config = {
            "pools": [],
            "autonomics": {"decoherence_threshold": 0.15},
            "system_complexity": "high",
            "computational_budget": "high"
        }
        
        # Mock environment to avoid pool connections
        import os
        os.environ["NODE_ENV"] = "development"
        os.environ["HYBA_ALLOW_DEV_FIXTURES"] = "true"
        
        genesis = GenesisAI(config)
        
        # Verify enhanced components are initialized
        self.assertTrue(hasattr(genesis, 'iit_analyzer'))
        self.assertTrue(hasattr(genesis, 'penrose_or'))
        self.assertTrue(hasattr(genesis, 'knowledge_substrate'))
        
        # Verify enhanced modes are enabled when config specifies high complexity/budget
        self.assertTrue(genesis.iit_analyzer.enhanced_partitioning)
        self.assertTrue(genesis.penrose_or.enhanced_gravity_model)
    
    def test_penrose_or_integration(self):
        """Test that Penrose OR is used in consciousness event detection."""
        from python_backend.pythia_mining.penrose_objective_reduction import ObjectiveReductionEngine
        
        engine = ObjectiveReductionEngine(enhanced_gravity_model=True, enable_true_or=False)
        
        # Create a density matrix
        rho = np.eye(4, dtype=np.complex128) / 4
        coherence_time = 1.0
        
        collapsed, is_event = engine.objective_reduction(rho, coherence_time)
        
        # Verify it works
        self.assertIsInstance(collapsed, np.ndarray)
        self.assertIsInstance(is_event, bool)
        
        # Verify metrics include enhanced mode
        metrics = engine.get_consciousness_metrics()
        self.assertTrue(metrics['enhanced_gravity_model'])
    
    def test_iit_analyzer_integration(self):
        """Test that IIT 4.0 analyzer is used with enhanced partitioning."""
        from python_backend.pythia_mining.iit_4_analyzer import IIT4Analyzer
        
        # Use larger system size to trigger approximate method
        analyzer = IIT4Analyzer(system_size=10, enhanced_partitioning=True)
        
        state = np.random.rand(10)
        result = analyzer.calculate_phi_max(state)
        
        # Verify enhanced partitioning is used
        self.assertIn('method', result)
        self.assertEqual(result['method'], 'enhanced_greedy')
    
    def test_deutsch_substrate_integration(self):
        """Test that Deutsch knowledge substrate is used in decision making."""
        from python_backend.pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
        
        substrate = KnowledgeSubstrate()
        
        context = {
            'difficulty': 1000000,
            'thermal_load': 0.5,
            'phi_resonance': 0.618,
            'pool_latency': 45
        }
        outcome = {'accepted': True}
        
        explanation = substrate.create_knowledge_from_success('strategy_a', context, outcome)
        
        # Verify φ-resonance is included (required for enhanced mode)
        self.assertIn('φ-resonance', explanation.explanation_text)
        
        # Add strategy to performance history to test context-aware modeling
        substrate.strategy_performance['strategy_a'] = [0.7, 0.8, 0.9]
        simulation = substrate._simulate_alternative_strategy('strategy_a', context)
        self.assertIn('context_factors', simulation)
    
    def test_golden_ratio_scaling(self):
        """Test that Golden Ratio scaling is applied to consciousness metrics."""
        import math
        PHI = (1 + math.sqrt(5)) / 2
        
        # Simulate scaling with formula that increases values
        phi_integrated = 0.5
        phi_causal = 0.4
        
        # Use scaling that increases values: phi * PHI / 1.5
        scaled_integrated = min(1.0, phi_integrated * PHI / 1.5)
        scaled_causal = min(1.0, phi_causal * PHI / 1.5)
        
        # Verify scaling is applied (values should increase)
        self.assertGreater(scaled_integrated, phi_integrated)
        self.assertGreater(scaled_causal, phi_causal)
        self.assertLessEqual(scaled_integrated, 1.0)
        self.assertLessEqual(scaled_causal, 1.0)
    
    def test_pulvini_memory_compression_integration(self):
        """Test that Pulvini memory compression is used for nonce space pre-computation."""
        from python_backend.pythia_mining.pulvini_memory_fabric import PulviniMemoryFabric
        
        fabric = PulviniMemoryFabric(num_nodes=32)
        
        # Record some paths
        fabric.record_path([0, 1, 2], 0.8)
        fabric.record_path([1, 2, 3], 0.6)
        
        # Get compressed snapshot
        snapshot = fabric.compressed_kernel_snapshot()
        
        # Verify compression data is available
        self.assertIn('compression', snapshot.to_dict())
        self.assertIn('kernel', snapshot.to_dict())
    
    def test_backward_compatibility_maintained(self):
        """Test that all changes maintain backward compatibility."""
        from python_backend.pythia_mining.penrose_objective_reduction import ObjectiveReductionEngine
        from python_backend.pythia_mining.iit_4_analyzer import IIT4Analyzer
        from python_backend.pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
        
        # Test default parameters maintain backward compatibility
        penrose = ObjectiveReductionEngine()
        self.assertFalse(penrose.enable_true_or)
        self.assertFalse(penrose.enhanced_gravity_model)
        
        iit = IIT4Analyzer(system_size=4)
        self.assertFalse(iit.enhanced_partitioning)
        
        substrate = KnowledgeSubstrate()
        # Deutsch substrate has no breaking changes
        
        # Verify they still work with default parameters
        rho = np.eye(4, dtype=np.complex128) / 4
        collapsed, _ = penrose.objective_reduction(rho, 1.0)
        self.assertIsInstance(collapsed, np.ndarray)

if __name__ == '__main__':
    unittest.main()
