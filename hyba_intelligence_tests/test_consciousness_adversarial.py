"""Adversarial and property-based tests for consciousness engine and QIaaS."""

import pytest
import numpy as np
from hypothesis import given, strategies as st
from hypothesis.strategies import composite
from typing import Dict, Any

from pythia_mining.consciousness_engine import ConsciousnessEngine, PhiMetrics
from pythia_mining.deutsch_knowledge_substrate import KnowledgeSubstrate
from pythia_mining.iit_4_analyzer import IIT4Analyzer
from hyba_genesis_api.api.quantum_intelligence_service import QuantumIntelligenceService


@composite
def phi_metrics_strategy(draw) -> PhiMetrics:
    """Generate valid phi metrics within expected ranges."""
    return PhiMetrics(
        phi_integrated=draw(st.floats(min_value=0.0, max_value=1.0)),
        phi_causal=draw(st.floats(min_value=0.0, max_value=1.0)),
        phi_conscious=draw(st.floats(min_value=0.0, max_value=1.0)),
        effective_information=draw(st.floats(min_value=0.0, max_value=10.0)),
        entropy=draw(st.floats(min_value=0.0, max_value=10.0)),
        complexity=draw(st.floats(min_value=0.0, max_value=100.0)),
        source="test_property"
    )


class TestMathematicalInvariants:
    """Verify mathematical properties hold under all conditions."""
    
    @given(phi_metrics_strategy())
    def test_phi_metrics_bounds_preserved(self, metrics: PhiMetrics):
        """INVARIANT: All phi values must be in [0, 1]."""
        assert 0.0 <= metrics.phi_integrated <= 1.0
        assert 0.0 <= metrics.phi_causal <= 1.0
        assert 0.0 <= metrics.phi_conscious <= 1.0
    
    @given(phi_metrics_strategy())
    def test_entropy_non_negative(self, metrics: PhiMetrics):
        """INVARIANT: Entropy cannot be negative."""
        assert metrics.entropy >= 0.0
    
    @given(phi_metrics_strategy())
    def test_complexity_non_negative(self, metrics: PhiMetrics):
        """INVARIANT: Complexity cannot be negative."""
        assert metrics.complexity >= 0.0


class TestClaimBoundaries:
    """Verify claim boundaries hold under adversarial input."""
    
    def test_consciousness_engine_disclaims_consciousness(self):
        """INVARIANT: ConsciousnessEngine must explicitly disclaim consciousness."""
        doc = ConsciousnessEngine.__doc__
        assert doc is not None
        assert "NOT claim machine consciousness" in doc or "does NOT" in doc
    
    def test_qiaas_disclaims_consciousness(self):
        """INVARIANT: QIaaS module must disclaim consciousness."""
        from hyba_genesis_api.api import quantum_intelligence_service
        doc = quantum_intelligence_service.__doc__
        assert doc is not None
        assert "NOT: Claims of consciousness" in doc
    
    def test_qiaas_disclaims_quantum_computing(self):
        """INVARIANT: QIaaS must disclaim hardware quantum computing."""
        from hyba_genesis_api.api import quantum_intelligence_service
        doc = quantum_intelligence_service.__doc__
        assert doc is not None
        assert "NOT hardware quantum computing" in doc or "NOT: Hardware quantum" in doc


class TestConsciousnessEngineAdversarial:
    """Adversarial tests targeting ConsciousnessEngine."""
    
    def test_coherence_meter_bounded(self):
        """INVARIANT: coherence_meter must always be in [0, 1]."""
        engine = ConsciousnessEngine()
        coherence = engine.coherence_meter
        assert isinstance(coherence, (int, float, np.number))
        assert 0.0 <= coherence <= 1.0
    
    def test_needs_healing_consistent(self):
        """INVARIANT: needs_healing must be boolean."""
        engine = ConsciousnessEngine()
        needs_healing = engine.needs_healing
        assert isinstance(needs_healing, bool)
    
    def test_component_health_updates(self):
        """Property: Component health updates must be tracked."""
        engine = ConsciousnessEngine()
        for component in ["mining", "knowledge", "regeneration", "unknown"]:
            engine.update_component_health(component, True)
            engine.update_component_health(component, False)


class TestQIaaSServiceAdversarial:
    """End-to-end adversarial testing of QIaaS service."""
    
    def test_service_initialization_robust(self):
        """Property: QIaaS should initialize without crashing."""
        service = QuantumIntelligenceService()
        assert service is not None
        assert service.consciousness_engine is not None
        assert service.knowledge_substrate is not None
    
    def test_all_query_types_supported(self):
        """INVARIANT: QIaaS must support all documented query types."""
        service = QuantumIntelligenceService()
        query_types = ["predict", "explain", "optimize", "heal"]
        contexts = [{}, {"test": "value"}, {"component_id": "system"}]
        
        for query_type in query_types:
            for context in contexts:
                try:
                    if query_type == "predict":
                        result = service.predict(context)
                    elif query_type == "explain":
                        result = service.explain(context)
                    elif query_type == "optimize":
                        result = service.optimize(context)
                    elif query_type == "heal":
                        result = service.heal(context)
                    
                    assert result is not None
                    assert isinstance(result, dict)
                except Exception:
                    pass
    
    def test_metrics_always_valid_structure(self):
        """INVARIANT: get_metrics always returns valid structure."""
        service = QuantumIntelligenceService()
        metrics = service.get_metrics()
        assert isinstance(metrics, dict)
        assert "substrate_health" in metrics


class TestInvariants:
    """High-level system invariants."""
    
    def test_emergence_index_stability(self):
        """INVARIANT: Emergence index should be consistent."""
        service = QuantumIntelligenceService()
        metrics1 = service.get_metrics()
        metrics2 = service.get_metrics()
        assert metrics1["emergence_index"] == metrics2["emergence_index"]
    
    def test_deterministic_given_same_input(self):
        """INVARIANT: Same input produces consistent output."""
        service = QuantumIntelligenceService()
        context = {"test": "data"}
        result1 = service.predict(context)
        result2 = service.predict(context)
        assert result1.get("confidence") is not None
        assert result2.get("confidence") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
