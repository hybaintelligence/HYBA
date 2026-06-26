"""Benchmark tests for Agentic Intelligence Service.

These tests measure performance characteristics:
- Token optimization throughput
- GPU scaling allocation speed
- Agent execution latency
- Evidence sealing performance
- Marketplace query performance
"""

import pytest
import time
from pytest_benchmark import BenchmarkFixture

from hyba_genesis_api.api.agentic_intelligence_service.service import (
    TokenOptimizationEngine,
    GPUScalingCoordinator,
    AgentMarketplace,
    AgenticIntelligenceService,
    AgentTaskRequest,
    TokenOptimizationConfig,
    GPUScalingConfig,
)


class TestTokenOptimizationBenchmarks:
    """Benchmark tests for token optimization."""
    
    def test_optimize_short_prompt_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark optimizing a short prompt."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=True)
        prompt = "Analyze this data"
        
        result = benchmark(engine.optimize_prompt, prompt, config)
        
        assert result["compression_ratio"] <= 1.0
    
    def test_optimize_medium_prompt_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark optimizing a medium prompt."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=True)
        prompt = "Please kindly analyze the financial data for risk assessment and provide recommendations for portfolio optimization"
        
        result = benchmark(engine.optimize_prompt, prompt, config)
        
        assert result["compression_ratio"] <= 1.0
    
    def test_optimize_long_prompt_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark optimizing a long prompt."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=True)
        prompt = " ".join(["analyze"] * 100)
        
        result = benchmark(engine.optimize_prompt, prompt, config)
        
        assert result["compression_ratio"] <= 1.0
    
    def test_optimize_with_pulvini_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark optimizing with PULVINI enabled."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(
            enable_compression=True,
            use_pulvini=True
        )
        prompt = "Analyze values 123.45, 67.89, 10.5 in the dataset"
        
        result = benchmark(engine.optimize_prompt, prompt, config)
        
        assert result["compression_ratio"] <= 1.0
    
    def test_get_optimization_stats_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark getting optimization statistics."""
        engine = TokenOptimizationEngine()
        
        # Add some optimizations first
        for _ in range(10):
            engine.optimize_prompt("test prompt", TokenOptimizationConfig(enable_compression=True))
        
        stats = benchmark(engine.get_optimization_stats)
        
        assert stats["total_optimizations"] == 10


class TestGPUScalingBenchmarks:
    """Benchmark tests for GPU scaling."""
    
    def test_gpu_allocation_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark GPU allocation."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        config = GPUScalingConfig(enable_distributed=True)
        
        result = benchmark(coordinator.allocate_gpu, "task_1", config)
        
        assert result["gpu_allocated"] is True
    
    def test_gpu_release_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark GPU release."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        config = GPUScalingConfig(enable_distributed=True)
        
        coordinator.allocate_gpu("task_1", config)
        benchmark(coordinator.release_gpu, "task_1")
    
    def test_get_gpu_utilization_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark getting GPU utilization."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        
        stats = benchmark(coordinator.get_gpu_utilization)
        
        assert "active_gpus" in stats
    
    def test_concurrent_gpu_allocations_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark concurrent GPU allocations."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        config = GPUScalingConfig(enable_distributed=True)
        
        def allocate_multiple():
            for i in range(10):
                coordinator.allocate_gpu(f"task_{i}", config)
        
        benchmark(allocate_multiple)


class TestAgentMarketplaceBenchmarks:
    """Benchmark tests for agent marketplace."""
    
    def test_list_all_agents_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark listing all agents."""
        marketplace = AgentMarketplace()
        
        agents = benchmark(marketplace.list_agents)
        
        assert len(agents) > 0
    
    def test_list_agents_with_filter_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark listing agents with category filter."""
        marketplace = AgentMarketplace()
        
        agents = benchmark(marketplace.list_agents, category="finance")
        
        assert all(agent.category == "finance" for agent in agents)
    
    def test_search_agents_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark searching agents."""
        marketplace = AgentMarketplace()
        
        results = benchmark(marketplace.search_agents, "financial")
        
        assert isinstance(results, list)
    
    def test_get_agent_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark getting a specific agent."""
        marketplace = AgentMarketplace()
        
        agent = benchmark(marketplace.get_agent, "fin_analysis_v1")
        
        assert agent is not None
        assert agent.agent_id == "fin_analysis_v1"
    
    def test_register_agent_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark registering a new agent."""
        marketplace = AgentMarketplace()
        
        from hyba_genesis_api.api.agentic_intelligence_service.service import AgentDefinition
        
        agent = AgentDefinition(
            agent_id="benchmark_test_agent",
            name="Benchmark Test Agent",
            description="Test agent for benchmarking",
            capabilities=["test"],
            category="test"
        )
        
        benchmark(marketplace.register_agent, agent)


class TestAgentExecutionBenchmarks:
    """Benchmark tests for agent execution."""
    
    def test_agent_execution_simple_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark simple agent execution."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="fin_analysis_v1",
            task_type="risk_analysis",
            prompt="Test",
            optimize_tokens=False,
            enable_gpu_scaling=False
        )
        
        result = benchmark(service.execute_agent_task, request)
        
        assert result.status is not None
    
    def test_agent_execution_with_token_optimization_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark agent execution with token optimization."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="ops_optimizer_v1",
            task_type="optimization",
            prompt="Test prompt for optimization",
            optimize_tokens=True,
            enable_gpu_scaling=False
        )
        
        result = benchmark(service.execute_agent_task, request)
        
        assert result.token_optimization_applied is True
    
    def test_agent_execution_with_gpu_scaling_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark agent execution with GPU scaling."""
        service = AgenticIntelligenceService()
        
        request = AgentTaskRequest(
            agent_id="data_analyst_v1",
            task_type="analysis",
            prompt="Test prompt",
            optimize_tokens=False,
            enable_gpu_scaling=True
        )
        
        result = benchmark(service.execute_agent_task, request)
        
        assert result.gpu_scaling_used is True


class TestEvidenceSealingBenchmarks:
    """Benchmark tests for evidence sealing."""
    
    def test_hash_computation_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark SHA-256 hash computation."""
        import hashlib
        import json
        
        data = {"test": "data", "numbers": [1, 2, 3, 4, 5]}
        
        def compute_hash():
            canonical = json.dumps(data, sort_keys=True, default=str, separators=(",", ":"))
            return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        
        hash_value = benchmark(compute_hash)
        
        assert len(hash_value) == 64  # SHA-256 produces 64 hex chars
    
    def test_seal_generation_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark cryptographic seal generation."""
        from hyba_genesis_api.api.agentic_intelligence_service.service import AgenticIntelligenceService
        import hashlib
        import json
        from datetime import datetime, timezone
        
        def generate_seal():
            body = {
                "test": "data",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            canonical = json.dumps(body, sort_keys=True, default=str, separators=(",", ":"))
            body_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            seal_body = {
                "algorithm": "SHA-256",
                "body_hash": body_hash,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            return hashlib.sha256(json.dumps(seal_body, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")).hexdigest()
        
        seal = benchmark(generate_seal)
        
        assert len(seal) == 64


class TestServiceInitializationBenchmarks:
    """Benchmark tests for service initialization."""
    
    def test_service_initialization_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark AgenticIntelligenceService initialization."""
        
        service = benchmark(AgenticIntelligenceService)
        
        assert service is not None
        assert service.orchestrator is not None
    
    def test_marketplace_initialization_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark AgentMarketplace initialization."""
        
        marketplace = benchmark(AgentMarketplace)
        
        assert len(marketplace.list_agents()) > 0
    
    def test_token_optimizer_initialization_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark TokenOptimizationEngine initialization."""
        
        engine = benchmark(TokenOptimizationEngine)
        
        assert engine.pulvini is not None
    
    def test_gpu_coordinator_initialization_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark GPUScalingCoordinator initialization."""
        
        coordinator = benchmark(GPUScalingCoordinator, max_gpus=4)
        
        assert coordinator.max_gpus == 4


class TestThroughputBenchmarks:
    """Throughput benchmarks for high-volume operations."""
    
    def test_token_optimization_throughput_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark token optimization throughput (100 operations)."""
        engine = TokenOptimizationEngine()
        config = TokenOptimizationConfig(enable_compression=True)
        
        def optimize_100():
            for i in range(100):
                engine.optimize_prompt(f"Test prompt {i}", config)
        
        benchmark(optimize_100)
    
    def test_gpu_allocation_throughput_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark GPU allocation throughput (100 allocations)."""
        coordinator = GPUScalingCoordinator(max_gpus=4)
        config = GPUScalingConfig(enable_distributed=True)
        
        def allocate_100():
            for i in range(100):
                coordinator.allocate_gpu(f"task_{i}", config)
        
        benchmark(allocate_100)
    
    def test_marketplace_search_throughput_benchmark(self, benchmark: BenchmarkFixture):
        """Benchmark marketplace search throughput (100 searches)."""
        marketplace = AgentMarketplace()
        
        def search_100():
            for i in range(100):
                marketplace.search_agents("test")
        
        benchmark(search_100)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
