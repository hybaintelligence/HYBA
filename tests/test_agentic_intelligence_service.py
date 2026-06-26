"""Production tests for Agentic Intelligence as a Service (AIaaS).

Tests cover:
- Agent marketplace functionality
- Token optimization with PULVINI integration
- GPU scaling coordination
- Evidence sealing and governance
- Agent execution with sovereign gates
- API endpoint integration
"""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from hyba_genesis_api.api.agentic_intelligence_service.service import (
    AgentDefinition,
    AgentTaskRequest,
    AgentExecutionResult,
    TokenOptimizationConfig,
    GPUScalingConfig,
    AgenticIntelligenceService,
    TokenOptimizationEngine,
    GPUScalingCoordinator,
    AgentMarketplace,
    agentic_service,
)


class TestAgentMarketplace:
    """Test agent marketplace functionality."""
    
    def test_marketplace_initialization(self):
        """Test marketplace initializes with built-in agents."""
        marketplace = AgentMarketplace()
        assert len(marketplace.agents) > 0
        
        # Check built-in agents exist
        assert marketplace.get_agent("fin_analysis_v1") is not None
        assert marketplace.get_agent("security_monitor_v1") is not None
        assert marketplace.get_agent("ops_optimizer_v1") is not None
        assert marketplace.get_agent("data_analyst_v1") is not None
    
    def test_register_agent(self):
        """Test registering a new agent."""
        marketplace = AgentMarketplace()
        initial_count = len(marketplace.agents)
        
        new_agent = AgentDefinition(
            agent_id="test_agent_v1",
            name="Test Agent",
            description="Test agent for unit testing",
            capabilities=["test_capability"],
            version="1.0.0",
            category="test"
        )
        
        marketplace.register_agent(new_agent)
        assert len(marketplace.agents) == initial_count + 1
        assert marketplace.get_agent("test_agent_v1") == new_agent
    
    def test_list_agents(self):
        """Test listing agents with category filter."""
        marketplace = AgentMarketplace()
        
        # List all agents
        all_agents = marketplace.list_agents()
        assert len(all_agents) > 0
        
        # Filter by category
        finance_agents = marketplace.list_agents(category="finance")
        assert all(agent.category == "finance" for agent in finance_agents)
    
    def test_search_agents(self):
        """Test searching agents by query."""
        marketplace = AgentMarketplace()
        
        # Search by name
        results = marketplace.search_agents("financial")
        assert len(results) > 0
        assert any("financial" in agent.name.lower() for agent in results)
        
        # Search by capability
        results = marketplace.search_agents("risk")
        assert len(results) > 0
        assert any("risk" in " ".join(agent.capabilities).lower() for agent in results)


class TestTokenOptimizationEngine:
    """Test token optimization with PULVINI integration."""
    
    def test_engine_initialization(self):
        """Test engine initializes with PULVINI."""
        engine = TokenOptimizationEngine()
        assert engine.pulvini is not None
        assert len(engine.optimization_history) == 0
    
    def test_optimize_prompt_disabled(self):
        """Test optimization when disabled."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=False)
        
        result = engine.optimize_prompt("Test prompt", config)
        
        assert result["optimized_prompt"] == "Test prompt"
        assert result["tokens_saved"] == 0
        assert result["compression_ratio"] == 1.0
        assert result["strategy"] == "none"
    
    def test_optimize_prompt_enabled(self):
        """Test optimization when enabled."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=True)
        
        prompt = "Please kindly could you analyze this data for me"
        result = engine.optimize_prompt(prompt, config)
        
        assert result["optimized_prompt"] != prompt
        assert result["tokens_saved"] >= 0
        assert result["compression_ratio"] <= 1.0
        assert len(engine.optimization_history) == 1
    
    def test_semantic_compression(self):
        """Test semantic compression preserves structure."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(
            enable_compression=True,
            preserve_semantic_integrity=True
        )
        
        prompt = "What is the risk? How do we optimize?"
        result = engine.optimize_prompt(prompt, config)
        
        # Question marks should be preserved
        assert "?" in result["optimized_prompt"]
    
    def test_optimization_stats(self):
        """Test optimization statistics tracking."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=True)
        
        # Run multiple optimizations
        engine.optimize_prompt("Test prompt 1", config)
        engine.optimize_prompt("Test prompt 2", config)
        
        stats = engine.get_optimization_stats()
        
        assert stats["total_optimizations"] == 2
        assert stats["avg_compression_ratio"] <= 1.0
        assert stats["total_tokens_saved"] >= 0


class TestGPUScalingCoordinator:
    """Test GPU scaling coordination."""
    
    def test_coordinator_initialization(self):
        """Test coordinator initializes with max GPUs."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        assert coordinator.max_gpus == 4
        assert len(coordinator.active_gpus) == 0
    
    def test_allocate_gpu_disabled(self):
        """Test GPU allocation when distributed is disabled."""
        coordinator = GPUScalingCoordinator()
        config = GPUScalingConfig(enable_distributed=False)
        
        result = coordinator.allocate_gpu("task_1", config)
        
        assert result["gpu_allocated"] is False
        assert result["gpu_id"] is None
        assert result["strategy"] == "single_cpu"
    
    def test_allocate_gpu_enabled(self):
        """Test GPU allocation when distributed is enabled."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        config = GPUScalingConfig(enable_distributed=True, max_gpus=2)
        
        result = coordinator.allocate_gpu("task_1", config)
        
        assert result["gpu_allocated"] is True
        assert result["gpu_id"] is not None
        assert result["strategy"] == "round_robin"
        assert len(coordinator.active_gpus) == 1
    
    def test_release_gpu(self):
        """Test releasing GPU resources."""
        coordinator = GPUScalingCoordinator()
        config = GPUScalingConfig(enable_distributed=True)
        
        coordinator.allocate_gpu("task_1", config)
        assert len(coordinator.active_gpus) == 1
        
        coordinator.release_gpu("task_1")
        assert len(coordinator.active_gpus) == 0
    
    def test_gpu_utilization(self):
        """Test GPU utilization statistics."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        config = GPUScalingConfig(enable_distributed=True)
        
        # Allocate 2 GPUs
        coordinator.allocate_gpu("task_1", config)
        coordinator.allocate_gpu("task_2", config)
        
        stats = coordinator.get_gpu_utilization()
        
        assert stats["active_gpus"] == 2
        assert stats["max_gpus"] == 4
        assert stats["utilization_percent"] == 50.0


class TestAgenticIntelligenceService:
    """Test main agentic intelligence service."""
    
    def test_service_initialization(self):
        """Test service initializes all components."""
        service = AgenticIntelligenceService()
        
        assert service.orchestrator is not None
        assert service.token_optimizer is not None
        assert service.gpu_coordinator is not None
        assert service.marketplace is not None
        assert service.guard is not None
    
    def test_execute_agent_task_invalid_agent(self):
        """Test execution fails for invalid agent ID."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="invalid_agent",
            task_type="test",
            prompt="Test prompt"
        )
        
        with pytest.raises(Exception) as exc_info:
            service.execute_agent_task(request)
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_execute_agent_task_valid_agent(self):
        """Test execution succeeds for valid agent."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="fin_analysis_v1",
            task_type="risk_analysis",
            prompt="Analyze risk for portfolio",
            optimize_tokens=True,
            enable_gpu_scaling=False,
            governance_rail="enterprise"
        )
        
        result = service.execute_agent_task(request)
        
        assert result.status in ["EXECUTION_STAGED", "EXECUTION_REJECTED", "EXECUTION_REJECTED_REPAIR_STAGED"]
        assert result.agent_id == "fin_analysis_v1"
        assert result.token_optimization_applied is True
        assert result.sovereign_human_gate is True
        assert result.auto_apply is False
        assert result.cryptographic_seal is not None
    
    def test_governance_enforcement(self):
        """Test governance rail enforcement."""
        service = AgenticIntelligenceService()
        
        # Enterprise rail should enforce human gate
        request = AgentTaskRequest(
            agent_id="data_analyst_v1",
            task_type="analysis",
            prompt="Test",
            governance_rail="enterprise"
        )
        
        result = service.execute_agent_task(request)
        assert result.sovereign_human_gate is True
        assert result.auto_apply is False
    
    def test_list_marketplace_agents(self):
        """Test listing marketplace agents."""
        service = AgenticIntelligenceService()
        
        agents = service.list_marketplace_agents()
        assert len(agents) > 0
        
        finance_agents = service.list_marketplace_agents(category="finance")
        assert all(agent.category == "finance" for agent in finance_agents)
    
    def test_get_token_optimization_stats(self):
        """Test getting token optimization statistics."""
        service = AgenticIntelligenceService()
        
        stats = service.get_token_optimization_stats()
        assert "total_optimizations" in stats
        assert "avg_compression_ratio" in stats
    
    def test_get_gpu_utilization(self):
        """Test getting GPU utilization statistics."""
        service = AgenticIntelligenceService()
        
        stats = service.get_gpu_utilization()
        assert "active_gpus" in stats
        assert "max_gpus" in stats
        assert "utilization_percent" in stats


class TestEvidenceSealing:
    """Test evidence sealing and cryptographic verification."""
    
    def test_execution_result_has_seal(self):
        """Test execution result includes cryptographic seal."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="ops_optimizer_v1",
            task_type="optimization",
            prompt="Optimize process"
        )
        
        result = service.execute_agent_task(request)
        
        assert result.cryptographic_seal is not None
        assert "seal" in result.cryptographic_seal
        assert "body_hash" in result.cryptographic_seal
        assert "algorithm" in result.cryptographic_seal
        assert result.cryptographic_seal["algorithm"] == "SHA-256"
    
    def test_sovereign_gate_enforced(self):
        """Test sovereign human gate is always enforced."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="security_monitor_v1",
            task_type="monitoring",
            prompt="Monitor security"
        )
        
        result = service.execute_agent_task(request)
        
        assert result.sovereign_human_gate is True
        assert result.auto_apply is False


class TestGlobalServiceInstance:
    """Test global service instance for API integration."""
    
    def test_global_service_exists(self):
        """Test global service instance is available."""
        assert agentic_service is not None
        assert isinstance(agentic_service, AgenticIntelligenceService)
    
    def test_global_service_functional(self):
        """Test global service can execute tasks."""
        request = AgentTaskRequest(
            agent_id="fin_analysis_v1",
            task_type="analysis",
            prompt="Test"
        )
        
        result = agentic_service.execute_agent_task(request)
        assert result is not None


class TestTokenOptimizationWithPulvini:
    """Test PULVINI integration in token optimization."""
    
    def test_pulvini_compression_attempted(self):
        """Test PULVINI compression is attempted for numerical data."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(
            enable_compression=True,
            use_pulvini=True
        )
        
        prompt = "Analyze values 123.45, 67.89, 10.5 in the dataset"
        result = engine.optimize_prompt(prompt, config)
        
        # Should attempt PULVINI for numerical data
        assert "pulvini" in result["strategy"].lower() or "semantic" in result["strategy"].lower()
    
    def test_pulvini_fallback_on_error(self):
        """Test fallback when PULVINI compression fails."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(
            enable_compression=True,
            use_pulvini=True
        )
        
        # Prompt without numerical data should still work
        prompt = "Analyze the text data without numbers"
        result = engine.optimize_prompt(prompt, config)
        
        assert result["optimized_prompt"] is not None
        assert result["compression_ratio"] <= 1.0


class TestGPUScalingStrategies:
    """Test different GPU scaling strategies."""
    
    def test_round_robin_allocation(self):
        """Test round-robin GPU allocation."""
        coordinator = GPUScalingCoordinator(max_gpus=2)
        config = GPUScalingConfig(
            enable_distributed=True,
            load_balancing_strategy="round_robin"
        )
        
        result1 = coordinator.allocate_gpu("task_1", config)
        result2 = coordinator.allocate_gpu("task_2", config)
        
        assert result1["gpu_id"] != result2["gpu_id"]
    
    def test_max_gpus_limit(self):
        """Test max GPUs limit is respected."""
        coordinator = GPUScalingCoordinator(max_gpus=2)
        config = GPUScalingConfig(
            enable_distributed=True,
            max_gpus=10  # Request more than available
        )
        
        result = coordinator.allocate_gpu("task_1", config)
        assert result["max_gpus"] == 2  # Limited by coordinator


@pytest.mark.integration
class TestAgenticServiceIntegration:
    """Integration tests for agentic service with full stack."""
    
    def test_full_agent_execution_flow(self):
        """Test complete flow from request to sealed result."""
        service = AgenticIntelligenceService()
        
        # Execute task
        request = AgentTaskRequest(
            agent_id="data_analyst_v1",
            task_type="causal_analysis",
            prompt="Analyze causal relationships",
            optimize_tokens=True,
            enable_gpu_scaling=False
        )
        
        result = service.execute_agent_task(request)
        
        # Verify complete flow
        assert result.task_id is not None
        assert result.status is not None
        assert result.evidence is not None
        assert result.cryptographic_seal is not None
        assert result.execution_time_ms > 0
        assert 0 <= result.confidence <= 100
    
    def test_token_optimization_integration(self):
        """Test token optimization in full execution flow."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="fin_analysis_v1",
            task_type="analysis",
            prompt="Please kindly analyze the financial data for risk assessment",
            optimize_tokens=True
        )
        
        result = service.execute_agent_task(request)
        
        assert result.token_optimization_applied is True
        assert result.tokens_saved is not None
    
    def test_gpu_scaling_integration(self):
        """Test GPU scaling in full execution flow."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="ops_optimizer_v1",
            task_type="optimization",
            prompt="Optimize operations",
            enable_gpu_scaling=True
        )
        
        result = service.execute_agent_task(request)
        
        assert result.gpu_scaling_used is True
        assert result.gpus_utilized is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
