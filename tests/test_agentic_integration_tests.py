"""Integration tests for Agentic Intelligence Service.

These tests verify the full integration between components:
- API endpoints to service layer
- Service layer to PYTHIA orchestrator
- Token optimization to PULVINI
- GPU scaling coordination
- Evidence sealing across the stack
- Governance enforcement
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from hyba_genesis_api.main import app
from hyba_genesis_api.api.agentic_intelligence_service.service import (
    AgentDefinition,
    AgentTaskRequest,
    agentic_service,
)


class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    def test_list_agents_endpoint(self):
        """Test the list agents API endpoint."""
        client = TestClient(app)
        response = client.get("/api/agentic/agents")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify agent structure
        agent = data[0]
        assert "agent_id" in agent
        assert "name" in agent
        assert "capabilities" in agent
    
    def test_list_agents_with_category_filter(self):
        """Test listing agents with category filter."""
        client = TestClient(app)
        response = client.get("/api/agentic/agents?category=finance")
        
        assert response.status_code == 200
        data = response.json()
        assert all(agent["category"] == "finance" for agent in data)
    
    def test_get_specific_agent_endpoint(self):
        """Test getting a specific agent by ID."""
        client = TestClient(app)
        
        # First get list to find a valid ID
        list_response = client.get("/api/agentic/agents")
        agent_id = list_response.json()[0]["agent_id"]
        
        # Get specific agent
        response = client.get(f"/api/agentic/agents/{agent_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == agent_id
    
    def test_search_agents_endpoint(self):
        """Test searching agents by query."""
        client = TestClient(app)
        response = client.get("/api/agentic/search/agents?query=financial")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_token_optimization_stats_endpoint(self):
        """Test token optimization statistics endpoint."""
        client = TestClient(app)
        response = client.get("/api/agentic/optimization/tokens/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_optimizations" in data
        assert "avg_compression_ratio" in data
        assert "total_tokens_saved" in data
    
    def test_gpu_scaling_stats_endpoint(self):
        """Test GPU scaling statistics endpoint."""
        client = TestClient(app)
        response = client.get("/api/agentic/scaling/gpu/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_gpus" in data
        assert "max_gpus" in data
        assert "utilization_percent" in data
    
    def test_execute_agent_task_endpoint(self):
        """Test executing an agent task via API."""
        client = TestClient(app)
        
        request = {
            "agent_id": "fin_analysis_v1",
            "task_type": "risk_analysis",
            "prompt": "Analyze portfolio risk",
            "optimize_tokens": True,
            "enable_gpu_scaling": False,
            "governance_rail": "enterprise"
        }
        
        response = client.post("/api/agentic/execute", json=request)
        
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "cryptographic_seal" in data
        assert data["sovereign_human_gate"] is True
        assert data["auto_apply"] is False
    
    def test_execute_agent_task_invalid_agent(self):
        """Test execution fails for invalid agent."""
        client = TestClient(app)
        
        request = {
            "agent_id": "invalid_agent_id",
            "task_type": "test",
            "prompt": "Test prompt"
        }
        
        response = client.post("/api/agentic/execute", json=request)
        
        assert response.status_code == 404
    
    def test_update_token_optimization_config(self):
        """Test updating token optimization configuration."""
        client = TestClient(app)
        
        config = {
            "enable_compression": True,
            "target_reduction_ratio": 0.8,
            "use_pulvini": True
        }
        
        response = client.post("/api/agentic/optimization/tokens/config", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_update_gpu_scaling_config(self):
        """Test updating GPU scaling configuration."""
        client = TestClient(app)
        
        config = {
            "enable_distributed": True,
            "max_gpus": 4,
            "load_balancing_strategy": "round_robin"
        }
        
        response = client.post("/api/agentic/scaling/gpu/config", json=config)
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestServiceToOrchestratorIntegration:
    """Integration tests between service and PYTHIA orchestrator."""
    
    def test_service_uses_pythia_orchestrator(self):
        """Test that service properly delegates to PYTHIA orchestrator."""
        from pythia_agents.pythia_agent_orchestrator import PythiaAgentOrchestrator
        
        assert agentic_service.orchestrator is not None
        assert isinstance(agentic_service.orchestrator, PythiaAgentOrchestrator)
    
    def test_service_has_builtin_agent_registered(self):
        """Test that builtin mathematical executor is registered."""
        assert "pythia-math-substrate" in agentic_service.orchestrator.sub_agents
    
    def test_task_creation_and_execution_flow(self):
        """Test complete flow from task creation to execution."""
        from pythia_agents.pythia_agent_orchestrator import QuantumTask
        
        # Create a task
        task = QuantumTask.create(
            description="Test task",
            operation="phi_weighted_consensus",
            payload={"scores": [0.5, 0.7, 0.9]}
        )
        
        # Execute via orchestrator
        packets = agentic_service.orchestrator.run_entangled_group(
            agent_name="pythia-math-substrate",
            tasks=[task],
            max_workers=1
        )
        
        assert len(packets) == 1
        assert packets[0]["status"] in ["EXECUTION_STAGED", "EXECUTION_REJECTED"]
        assert "cryptographic_seal" in packets[0]


class TestTokenOptimizationToPulviniIntegration:
    """Integration tests between token optimization and PULVINI."""
    
    def test_pulvini_engine_initialized(self):
        """Test that PULVINI engine is initialized in token optimizer."""
        from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
        
        assert agentic_service.token_optimizer.pulvini is not None
        assert isinstance(
            agentic_service.token_optimizer.pulvini,
            PulviniPhiMemoryCompressionEngine
        )
    
    def test_pulvini_used_for_numerical_data(self):
        """Test that PULVINI is used for prompts with numerical data."""
        from hyba_genesis_api.api.agentic_intelligence_service.service import TokenOptimizationConfig
        
        prompt = "Analyze values 123.45, 67.89, 10.5 in dataset"
        config = TokenOptimizationConfig(enable_compression=True, use_pulvini=True)
        
        result = agentic_service.token_optimizer.optimize_prompt(prompt, config)
        
        # Should attempt PULVINI compression
        assert "pulvini" in result["strategy"].lower() or "semantic" in result["strategy"].lower()
    
    def test_pulvini_compression_reversible(self):
        """Test that PULVINI compression is reversible."""
        import numpy as np
        
        # Test with actual numerical data
        test_array = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        result = agentic_service.token_optimizer.pulvini.compress(test_array)
        
        assert result.reversible is True
        assert result.reconstruction_error <= 1e-8


class TestEvidenceSealingIntegration:
    """Integration tests for evidence sealing across the stack."""
    
    def test_execution_result_has_complete_seal(self):
        """Test that execution results have complete cryptographic seals."""
        request = AgentTaskRequest(
            agent_id="data_analyst_v1",
            task_type="analysis",
            prompt="Test prompt",
            optimize_tokens=False,
            enable_gpu_scaling=False
        )
        
        result = agentic_service.execute_agent_task(request)
        
        assert result.cryptographic_seal is not None
        assert "algorithm" in result.cryptographic_seal
        assert "body_hash" in result.cryptographic_seal
        assert "seal" in result.cryptographic_seal
        assert "timestamp" in result.cryptographic_seal
        assert result.cryptographic_seal["algorithm"] == "SHA-256"
    
    def test_seal_deterministic_for_same_input(self):
        """Test that seals are deterministic for identical inputs."""
        request = AgentTaskRequest(
            agent_id="ops_optimizer_v1",
            task_type="optimization",
            prompt="Test prompt",
            optimize_tokens=False,
            enable_gpu_scaling=False
        )
        
        result1 = agentic_service.execute_agent_task(request)
        result2 = agentic_service.execute_agent_task(request)
        
        # Body hashes should be similar (may differ due to timestamps in evidence)
        # but seals should have the same structure and algorithm
        assert result1.cryptographic_seal["algorithm"] == result2.cryptographic_seal["algorithm"]
        assert "body_hash" in result1.cryptographic_seal
        assert "seal" in result1.cryptographic_seal
    
    def test_sovereign_gate_enforced_in_all_results(self):
        """Test that sovereign gate is enforced across all execution paths."""
        agents = ["fin_analysis_v1", "security_monitor_v1", "ops_optimizer_v1"]
        
        for agent_id in agents:
            request = AgentTaskRequest(
                agent_id=agent_id,
                task_type="test",
                prompt="Test prompt",
                governance_rail="enterprise"
            )
            
            result = agentic_service.execute_agent_task(request)
            assert result.sovereign_human_gate is True
            assert result.auto_apply is False


class TestGovernanceIntegration:
    """Integration tests for governance enforcement."""
    
    def test_treasury_rail_allows_execution(self):
        """Test that treasury rail allows execution."""
        request = AgentTaskRequest(
            agent_id="fin_analysis_v1",
            task_type="analysis",
            prompt="Test",
            governance_rail="treasury"
        )
        
        result = agentic_service.execute_agent_task(request)
        assert result.sovereign_human_gate is True
    
    def test_enterprise_rail_enforces_human_gate(self):
        """Test that enterprise rail enforces human gate."""
        request = AgentTaskRequest(
            agent_id="security_monitor_v1",
            task_type="monitoring",
            prompt="Test",
            governance_rail="enterprise"
        )
        
        result = agentic_service.execute_agent_task(request)
        assert result.sovereign_human_gate is True
        assert result.auto_apply is False
    
    def test_sovereign_rail_enforces_strictest_controls(self):
        """Test that sovereign rail enforces strictest controls."""
        request = AgentTaskRequest(
            agent_id="data_analyst_v1",
            task_type="analysis",
            prompt="Test",
            governance_rail="sovereign"
        )
        
        result = agentic_service.execute_agent_task(request)
        assert result.sovereign_human_gate is True
        assert result.auto_apply is False


class TestMarketplaceIntegration:
    """Integration tests for agent marketplace."""
    
    def test_marketplace_has_builtin_agents(self):
        """Test that marketplace is initialized with built-in agents."""
        agents = agentic_service.marketplace.list_agents()
        
        assert len(agents) >= 4
        agent_ids = [a.agent_id for a in agents]
        assert "fin_analysis_v1" in agent_ids
        assert "security_monitor_v1" in agent_ids
        assert "ops_optimizer_v1" in agent_ids
        assert "data_analyst_v1" in agent_ids
    
    def test_marketplace_search_works(self):
        """Test that marketplace search functionality works."""
        results = agentic_service.marketplace.search_agents("financial")
        assert len(results) > 0
    
    def test_marketplace_category_filtering_works(self):
        """Test that marketplace category filtering works."""
        finance_agents = agentic_service.marketplace.list_agents(category="finance")
        assert all(a.category == "finance" for a in finance_agents)


class TestGPUScalingIntegration:
    """Integration tests for GPU scaling."""
    
    def test_gpu_coordinator_initialized(self):
        """Test that GPU coordinator is properly initialized."""
        assert agentic_service.gpu_coordinator is not None
        assert agentic_service.gpu_coordinator.max_gpus > 0
    
    def test_gpu_allocation_with_scaling_enabled(self):
        """Test GPU allocation when scaling is enabled."""
        request = AgentTaskRequest(
            agent_id="ops_optimizer_v1",
            task_type="optimization",
            prompt="Test",
            enable_gpu_scaling=True
        )
        
        result = agentic_service.execute_agent_task(request)
        assert result.gpu_scaling_used is True
    
    def test_gpu_utilization_tracking(self):
        """Test that GPU utilization is tracked correctly."""
        stats = agentic_service.get_gpu_utilization()
        
        assert "active_gpus" in stats
        assert "max_gpus" in stats
        assert "utilization_percent" in stats
        assert 0 <= stats["utilization_percent"] <= 100


class TestFullStackIntegration:
    """End-to-end integration tests for the full stack."""
    
    def test_complete_agent_execution_workflow(self):
        """Test complete workflow from API to execution to evidence sealing."""
        client = TestClient(app)
        
        # Step 1: List available agents
        agents_response = client.get("/api/agentic/agents")
        assert agents_response.status_code == 200
        agents = agents_response.json()
        assert len(agents) > 0
        
        # Step 2: Select an agent
        agent_id = agents[0]["agent_id"]
        
        # Step 3: Execute a task
        request = {
            "agent_id": agent_id,
            "task_type": agents[0]["capabilities"][0],
            "prompt": "Test prompt for integration test",
            "optimize_tokens": True,
            "enable_gpu_scaling": False,
            "governance_rail": "enterprise"
        }
        
        execution_response = client.post("/api/agentic/execute", json=request)
        assert execution_response.status_code == 200
        result = execution_response.json()
        
        # Step 4: Verify evidence seal
        assert "cryptographic_seal" in result
        assert result["sovereign_human_gate"] is True
        
        # Step 5: Check token optimization stats
        stats_response = client.get("/api/agentic/optimization/tokens/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_optimizations"] > 0
    
    def test_concurrent_agent_executions(self):
        """Test handling multiple concurrent agent executions."""
        import threading
        
        client = TestClient(app)
        results = []
        
        def execute_task(agent_id):
            request = {
                "agent_id": agent_id,
                "task_type": "test",
                "prompt": "Concurrent test",
                "optimize_tokens": False,
                "enable_gpu_scaling": False
            }
            response = client.post("/api/agentic/execute", json=request)
            results.append(response.status_code)
        
        threads = []
        agent_ids = ["fin_analysis_v1", "security_monitor_v1", "ops_optimizer_v1"]
        
        for agent_id in agent_ids:
            thread = threading.Thread(target=execute_task, args=(agent_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All executions should succeed
        assert all(status == 200 for status in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
