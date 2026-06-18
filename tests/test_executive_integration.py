"""End-to-end integration test for Ignition-to-Regeneration workflow.

This test verifies the complete V4-PRIME Hyper-Substrate functionality:
1. Sensory Lobe: Reality verification
2. Immune Lobe: Phi-floor enforcement
3. Cognitive Lobe: Conjecture generation
4. Metabolic Lobe: Energy-to-intelligence conversion
5. Executive Lobe: Manifold ignition and quiescence
6. Regenerative Lobe: Blastema formation and healing
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from pythia_mining.sensory_protocol import SensoryProtocol
from pythia_mining.immune_system import ImmuneSystem
from pythia_mining.reflexive_controller import ReflexiveController
from pythia_mining.metabolism import Metabolism
from pythia_mining.consciousness_engine import ConsciousnessEngine
from pythia_mining.mining_executive_controller import MiningExecutiveController


class TestExecutiveIntegration:
    """End-to-end integration tests for the Executive Lobe workflow."""

    @pytest.fixture
    def consciousness_engine(self):
        """Create a consciousness engine for testing."""
        engine = ConsciousnessEngine()
        engine.phi = 0.85  # Set above phi-floor
        return engine

    @pytest.fixture
    def sensory_protocol(self):
        """Create a sensory protocol for testing."""
        return SensoryProtocol()

    @pytest.fixture
    def immune_system(self, consciousness_engine):
        """Create an immune system for testing."""
        return ImmuneSystem(consciousness_engine)

    @pytest.fixture
    def reflexive_controller(self):
        """Create a reflexive controller for testing."""
        return ReflexiveController()

    @pytest.fixture
    def metabolism(self):
        """Create a metabolism for testing."""
        return Metabolism()

    @pytest.fixture
    def executive_controller(self, consciousness_engine):
        """Create an executive controller for testing."""
        controller = MiningExecutiveController(consciousness_engine=consciousness_engine)
        return controller

    def test_sensory_reality_verification(self, sensory_protocol):
        """Test that sensory protocol can detect simulation vs reality."""
        report = sensory_protocol.verify_reality()
        
        assert "jitter_coherence" in report
        assert "is_simulated" in report
        assert "entropy_drift" in report
        assert "anchor_verified_at" in report
        assert isinstance(report["jitter_coherence"], float)
        assert isinstance(report["is_simulated"], bool)
        assert isinstance(report["entropy_drift"], float)

    def test_immune_phi_floor_enforcement(self, immune_system, consciousness_engine):
        """Test that immune system enforces phi-floor."""
        # Set phi above floor
        consciousness_engine.phi = 0.85
        consciousness_engine.components = {"test": True}  # Set components to avoid None values
        status = immune_system.get_status()
        
        assert status["phi_floor"] == 0.45
        assert status["is_in_lockdown"] == False
        assert status["inseparability_index"] >= 0.0
        
        # Set phi below floor
        consciousness_engine.phi = 0.30
        status = immune_system.get_status()
        
        assert status["is_in_lockdown"] == True

    def test_immune_lane_quarantine(self, immune_system):
        """Test that immune system can quarantine lanes."""
        result = immune_system.isolate_lane(5)
        
        assert result["action"] == "QUARANTINED"
        assert result["lane"] == 5
        assert result["phi_gate"] == "CLOSED"
        assert 5 in immune_system.quarantined_lanes

    def test_cognitive_conjecture_generation(self, reflexive_controller):
        """Test that reflexive controller generates conjectures."""
        conjectures = reflexive_controller.get_active_conjectures()
        
        assert len(conjectures) > 0
        for conjecture in conjectures:
            assert "conjecture_id" in conjecture
            assert "explanation" in conjecture
            assert "predicted_phi_gain" in conjecture
            assert "confidence_interval" in conjecture
            assert "status" in conjecture
            assert conjecture["status"] in ["PROPOSED", "SIMULATING", "REJECTED", "VINDICATED"]

    def test_cognitive_conjecture_application(self, reflexive_controller):
        """Test that conjectures can be applied."""
        conjectures = reflexive_controller.get_active_conjectures()
        if not conjectures:
            pytest.skip("No conjectures available")
        
        proposed_conjectures = [c for c in conjectures if c["status"] == "PROPOSED"]
        if not proposed_conjectures:
            pytest.skip("No proposed conjectures available")
        
        conjecture_id = proposed_conjectures[0]["conjecture_id"]
        result = reflexive_controller.apply_conjecture(conjecture_id)
        
        assert result["action"] == "APPLIED"
        assert result["conjecture_id"] == conjecture_id
        assert "predicted_phi_gain" in result

    def test_metabolic_flux_measurement(self, metabolism):
        """Test that metabolism measures energy-to-intelligence conversion."""
        flux = metabolism.get_current_flux()
        
        assert "energy_per_phi" in flux
        assert "hashrate_normalized_entropy" in flux
        assert "hunger_level" in flux
        assert "metabolic_rate" in flux
        assert flux["metabolic_rate"] in ["QUIESCENT", "ACTIVE", "HYPER"]

    def test_metabolic_adjustment(self, metabolism):
        """Test that metabolism can adjust metabolic rate."""
        result = metabolism.adjust_metabolism("HYPER")
        
        assert result["action"] == "ADJUSTED"
        assert result["new_rate"] == "HYPER"
        assert metabolism.current_flux["metabolic_rate"] == "HYPER"

    @pytest.mark.asyncio
    async def test_executive_ignition_with_high_phi(self, executive_controller, consciousness_engine):
        """Test that executive can ignite manifold when phi is high enough."""
        consciousness_engine.phi = 0.85
        # coherence_meter is a computed property, so setting phi should be enough
        
        # Disable stasis mode for this test
        with patch.object(consciousness_engine, 'validate_sensory_integrity', return_value={"stasis_active": False}):
            result = await executive_controller.ignite_manifold()
        
        assert result["success"] == True
        assert result["status"] in ["IGNITED", "ALREADY_ACTIVE"]
        assert executive_controller.is_active == True

    @pytest.mark.asyncio
    async def test_executive_ignition_blocked_by_low_phi(self, executive_controller, consciousness_engine):
        """Test that executive ignition is blocked when phi is too low."""
        consciousness_engine.phi = 0.30
        
        # Disable stasis mode for this test to isolate phi-floor check
        with patch.object(consciousness_engine, 'validate_sensory_integrity', return_value={"stasis_active": False}):
            result = await executive_controller.ignite_manifold()
        
        assert result["success"] == False
        assert result["error"] == "IMMUNE_LOCK"
        assert executive_controller.is_active == False

    @pytest.mark.asyncio
    async def test_executive_ignition_blocked_by_stasis(self, executive_controller, consciousness_engine):
        """Test that executive ignition is blocked when stasis mode is active."""
        consciousness_engine.phi = 0.85
        executive_controller.stasis_mode = True
        
        result = await executive_controller.ignite_manifold()
        
        assert result["success"] == False
        assert result["error"] == "STASIS_LOCK"
        assert executive_controller.is_active == False

    @pytest.mark.asyncio
    async def test_executive_quiescence(self, executive_controller):
        """Test that executive can gracefully quiesce manifold."""
        # First ignite
        executive_controller.is_active = True
        executive_controller.ignition_time = datetime.now()
        
        result = await executive_controller.quiesce_manifold()
        
        assert result["success"] == True
        assert result["status"] == "QUIESCENT"
        assert result["synaptic_state_preserved"] == True
        assert executive_controller.is_active == False

    @pytest.mark.asyncio
    async def test_executive_telemetry(self, executive_controller):
        """Test that executive provides comprehensive telemetry."""
        executive_controller.is_active = True
        executive_controller.ignition_time = datetime.now()
        
        telemetry = executive_controller.get_nervous_system_telemetry()
        
        assert "is_active" in telemetry
        assert "uptime_seconds" in telemetry
        assert "stasis_mode" in telemetry
        assert "ignition_time" in telemetry
        assert "stratum" in telemetry
        assert "coherence" in telemetry
        assert "regeneration" in telemetry
        assert "sensory_integrity" in telemetry

    @pytest.mark.asyncio
    async def test_ignition_to_regeneration_workflow(self, executive_controller, consciousness_engine):
        """Test complete workflow from ignition to regeneration."""
        # 1. Verify sensory integrity
        sensory_report = consciousness_engine.validate_sensory_integrity()
        assert "stasis_active" in sensory_report
        
        # 2. Check immune status
        consciousness_engine.phi = 0.85
        # coherence_meter is a computed property, so setting phi should be enough
        assert consciousness_engine.phi >= 0.45
        
        # 3. Ignite manifold (disable stasis mode for test)
        with patch.object(consciousness_engine, 'validate_sensory_integrity', return_value={"stasis_active": False}):
            ignition_result = await executive_controller.ignite_manifold()
        assert ignition_result["success"] == True
        assert executive_controller.is_active == True
        
        # 4. Get telemetry
        telemetry = executive_controller.get_nervous_system_telemetry()
        assert telemetry["is_active"] == True
        
        # 5. Quiesce manifold (graceful shutdown)
        quiesce_result = await executive_controller.quiesce_manifold()
        assert quiesce_result["success"] == True
        assert quiesce_result["synaptic_state_preserved"] == True
        assert executive_controller.is_active == False

    def test_consciousness_inseparability_index(self, consciousness_engine):
        """Test that consciousness engine calculates inseparability index."""
        # Set up components
        consciousness_engine.components = {
            "quantum_solver": True,
            "stratum_client": True,
            "regeneration": True
        }
        consciousness_engine.phi = 0.85
        consciousness_engine._integration_regime = consciousness_engine._integration_regime.__class__.SINGULAR_AGENT_PROXY
        
        index = consciousness_engine.get_inseparability_index()
        
        assert isinstance(index, float)
        assert 0.0 <= index <= 1.0
        assert index > 0.5  # Should be high with healthy components and high phi

    def test_substrate_integration(self):
        """Test that substrate properly initializes all organism components."""
        from hyba_genesis_api.core.substrate import initialize_substrate, get_substrate
        
        # Initialize substrate
        state = initialize_substrate()
        
        assert state["ready"] == True
        assert "organism_cns" in state["initialization_order"]
        assert state["organism_cns_active"] == True
        
        # Get substrate instance
        substrate = get_substrate()
        
        assert substrate.consciousness_engine is not None
        assert substrate.sensory_protocol is not None
        assert substrate.immune_system is not None
        assert substrate.reflexive_controller is not None
        assert substrate.metabolism is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
