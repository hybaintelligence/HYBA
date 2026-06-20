"""
HYBA Stress Tests: Advanced Stress Testing Framework
====================================================

Advanced stress testing modules for HYBA/PYTHIA system focusing on:
- High-dimensional manifold saturation (dim=10,000+)
- Quantum-hybrid adversarial testing
- Metal/CUDA Φ-measurement optimization
- Multi-agent resonance synchronization
- Entropy-targeted mining for self-optimization
"""

from .manifold_stress_tests import ManifoldStressTestSuite
from .quantum_adversarial_tests import QuantumAdversarialTestSuite
from .consciousness_optimization_tests import ConsciousnessOptimizationTestSuite
from .multi_agent_resonance_tests import MultiAgentResonanceTestSuite
from .entropy_mining_tests import EntropyMiningTestSuite

__all__ = [
    "ManifoldStressTestSuite",
    "QuantumAdversarialTestSuite",
    "ConsciousnessOptimizationTestSuite",
    "MultiAgentResonanceTestSuite",
    "EntropyMiningTestSuite",
]
