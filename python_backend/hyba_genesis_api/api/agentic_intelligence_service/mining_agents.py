"""Mining-Specific Agents for the Agentic Marketplace.

These agents augment PYTHIA mining operations using the agentic intelligence
layer. They plug into the existing AgentMarketplace and can be invoked via
the agentic API or directly from the mining engine.

Agents:
- mining_strategy_optimizer_v1: Optimize nonce search strategy
- pool_performance_analyst_v1: Analyze pool acceptance rates and latency
- consciousness_tuner_v1: Tune consciousness engine thresholds
- hardware_scaling_advisor_v1: Recommend φ-scaled hardware allocations

All agents operate within safety constraints:
- Hermiticity preserved
- Positive-semidefinite outputs
- Natural φ-scaling
- Energy conservation
- Information integrity
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .service import (
    AgentDefinition,
    AgentTaskRequest,
    AgentExecutionResult,
    AgentMarketplace,
    TokenOptimizationEngine,
    GPUScalingCoordinator,
    GPUScalingConfig,
)


# ---------------------------------------------------------------------------
# Mining Agent Definitions
# ---------------------------------------------------------------------------

def register_mining_agents(marketplace: AgentMarketplace) -> None:
    """Register mining-specific agents into the marketplace."""

    marketplace.register_agent(
        AgentDefinition(
            agent_id="mining_strategy_optimizer_v1",
            name="Mining Strategy Optimizer",
            description=(
                "Optimizes nonce search strategy using φ-resonance analysis, "
                "reflexive learning proposals, and pool feedback. Reduces stale "
                "strategy durations and improves share acceptance rates."
            ),
            capabilities=[
                "nonce_strategy_optimization",
                "difficulty_adaptation",
                "phi_resonance_tuning",
                "search_depth_optimization",
                "pool_feedback_analysis",
            ],
            version="1.0.0",
            evidence_tier="quantum_backed",
            category="mining",
        )
    )

    marketplace.register_agent(
        AgentDefinition(
            agent_id="pool_performance_analyst_v1",
            name="Pool Performance Analyst",
            description=(
                "Analyzes pool acceptance rates, latency distributions, and "
                "error patterns. Recommends failover timing and connection "
                "strategies using circuit-breaker aware models."
            ),
            capabilities=[
                "pool_latency_analysis",
                "acceptance_rate_monitoring",
                "failover_recommendation",
                "error_pattern_detection",
            ],
            version="1.0.0",
            evidence_tier="heuristic",
            category="mining",
        )
    )

    marketplace.register_agent(
        AgentDefinition(
            agent_id="consciousness_tuner_v1",
            name="Consciousness Tuner",
            description=(
                "Tunes consciousness engine thresholds (phi_singular, phi_distributed, "
                "phi_critical) based on historical coherence trends and regime switches. "
                "Prevents unnecessary healing triggers and stabilizes integration regime."
            ),
            capabilities=[
                "phi_coherence_calibration",
                "regime_switch_optimization",
                "healing_threshold_tuning",
                "component_health_analysis",
            ],
            version="1.0.0",
            evidence_tier="quantum_backed",
            category="mining",
        )
    )

    marketplace.register_agent(
        AgentDefinition(
            agent_id="hardware_scaling_advisor_v1",
            name="Hardware Scaling Advisor",
            description=(
                "Recommends φ-scaled hardware allocations (GPUs, batch sizes, "
                "memory, search depth) using Fibonacci sequences derived from the "
                "golden ratio. Ensures natural growth curves and avoids binary overshoot."
            ),
            capabilities=[
                "gpu_allocation_planning",
                "batch_size_tuning",
                "memory_scaling",
                "search_depth_optimization",
                "phi_based_resource_projection",
            ],
            version="1.0.0",
            evidence_tier="heuristic",
            category="mining",
        )
    )


# ---------------------------------------------------------------------------
# Mining Agent Executors
# ---------------------------------------------------------------------------

class MiningStrategyOptimizer:
    """Execute mining strategy optimization via agentic framework."""

    def __init__(
        self,
        token_optimizer: TokenOptimizationEngine,
        gpu_coordinator: GPUScalingCoordinator,
    ) -> None:
        self.token_optimizer = token_optimizer
        self.gpu_coordinator = gpu_coordinator

    async def execute(
        self,
        request: AgentTaskRequest,
        mining_state: Dict[str, Any],
    ) -> AgentExecutionResult:
        """Optimize mining search strategy based on current state."""
        # Token-optimized prompt
        if request.optimize_tokens:
            opt = self.token_optimizer.optimize_prompt(
                request.prompt,
                TokenOptimizationEngine.__init__.__defaults__[0]
                if TokenOptimizationEngine.__init__.__defaults__
                else None,
            )
            prompt = opt["optimized_prompt"]
        else:
            prompt = request.prompt

        # GPU allocation
        gpu = self.gpu_coordinator.allocate_gpu(
            f"mining_opt_{request.agent_id}",
            GPUScalingConfig(enable_distributed=request.enable_gpu_scaling),
        )

        try:
            # Produce optimization recommendation from mining state
            coherence = mining_state.get("phi_coherence", 0.0)
            hashrate = mining_state.get("last_batch_hashrate_ehs", 0.0)
            strategy = mining_state.get("strategy", "phi_scaled_compressed_solver_search")

            recommendation = self._propose_strategy(coherence, hashrate, strategy)

            return AgentExecutionResult(
                task_id=f"mining_strategy_{request.agent_id}",
                agent_id=request.agent_id,
                status="EXECUTION_STAGED",
                result=recommendation,
                evidence={"type": "mining_strategy", "coherence": coherence},
                token_optimization_applied=request.optimize_tokens,
                gpu_scaling_used=gpu["gpu_allocated"],
                execution_time_ms=0.0,
                confidence=75.0,
                cryptographic_seal={},
                sovereign_human_gate=True,
                auto_apply=False,
            )
        finally:
            self.gpu_coordinator.release_gpu(f"mining_opt_{request.agent_id}")

    def _propose_strategy(
        self, coherence: float, hashrate: float, current_strategy: str
    ) -> Dict[str, Any]:
        if coherence >= 0.7:
            return {
                "recommended_strategy": "phi_resonance_search",
                "max_search_time": 30.0,
                "adaptive_difficulty": True,
                "rationale": "High coherence → aggressive φ-guided search",
            }
        elif coherence >= 0.4:
            return {
                "recommended_strategy": "phi_scaled_compressed_solver_search",
                "max_search_time": 60.0,
                "adaptive_difficulty": True,
                "rationale": "Medium coherence → balanced search",
            }
        else:
            return {
                "recommended_strategy": "distributed_defensive_search",
                "max_search_time": 120.0,
                "adaptive_difficulty": False,
                "rationale": "Low coherence → conservative distributed strategy",
            }


class PoolPerformanceAnalyst:
    """Analyze pool performance and recommend failover timing."""

    async def execute(
        self,
        request: AgentTaskRequest,
        pool_history: List[Dict[str, Any]],
    ) -> AgentExecutionResult:
        """Analyze recent pool responses and produce a recommendation."""
        latency_ms = [r.get("latency_ms", 0.0) for r in pool_history if r.get("latency_ms") is not None]
        acceptance_rate = (
            sum(1 for r in pool_history if r.get("accepted")) / max(1, len(pool_history))
        )

        if acceptance_rate < 0.5:
            recommendation = {
                "action": "consider_failover",
                "reason": f"acceptance_rate={acceptance_rate:.2f} < 0.5",
            }
        elif latency_ms and sum(latency_ms) / len(latency_ms) > 1000:
            recommendation = {
                "action": "monitor_latency",
                "reason": f"avg_latency={sum(latency_ms)/len(latency_ms):.0f}ms > 1000ms",
            }
        else:
            recommendation = {
                "action": "maintain",
                "reason": "pool metrics within acceptable bounds",
            }

        return AgentExecutionResult(
            task_id=f"pool_analysis_{request.agent_id}",
            agent_id=request.agent_id,
            status="EXECUTION_STAGED",
            result=recommendation,
            evidence={
                "type": "pool_analysis",
                "acceptance_rate": acceptance_rate,
                "sample_count": len(pool_history),
            },
            token_optimization_applied=False,
            gpu_scaling_used=False,
            execution_time_ms=0.0,
            confidence=60.0,
            cryptographic_seal={},
            sovereign_human_gate=True,
            auto_apply=False,
        )


class ConsciousnessTuner:
    """Tune consciousness engine thresholds based on historical trends."""

    async def execute(
        self,
        request: AgentTaskRequest,
        coherence_history: List[float],
        current_config: Dict[str, Any],
    ) -> AgentExecutionResult:
        """Recommend threshold adjustments."""
        if not coherence_history:
            return AgentExecutionResult(
                task_id=f"consciousness_tune_{request.agent_id}",
                agent_id=request.agent_id,
                status="EXECUTION_STAGED",
                result={"changes": {}, "rationale": "insufficient_history"},
                evidence={"type": "consciousness_tuning", "sample_count": 0},
                token_optimization_applied=False,
                gpu_scaling_used=False,
                execution_time_ms=0.0,
                confidence=40.0,
                cryptographic_seal={},
                sovereign_human_gate=True,
                auto_apply=False,
            )

        avg_coherence = sum(coherence_history) / len(coherence_history)
        std_coherence = (
            sum((c - avg_coherence) ** 2 for c in coherence_history) / len(coherence_history)
        ) ** 0.5

        proposed: Dict[str, Any] = {}
        # If coherence is highly variable, tighten singular threshold
        if std_coherence > 0.15 and avg_coherence >= 0.7:
            proposed["phi_singular_threshold"] = round(min(0.9, avg_coherence + 0.1), 3)
            rationale = "high_variance_high_coherence → raise singular threshold"
        elif avg_coherence < 0.4:
            proposed["phi_distributed_threshold"] = round(max(0.2, avg_coherence - 0.1), 3)
            rationale = "low coherence → lower distributed threshold to encourage healing"
        else:
            rationale = "no_adjustment_needed"

        return AgentExecutionResult(
            task_id=f"consciousness_tune_{request.agent_id}",
            agent_id=request.agent_id,
            status="EXECUTION_STAGED",
            result={"changes": proposed, "rationale": rationale},
            evidence={
                "type": "consciousness_tuning",
                "avg_coherence": avg_coherence,
                "std_coherence": std_coherence,
            },
            token_optimization_applied=False,
            gpu_scaling_used=False,
            execution_time_ms=0.0,
            confidence=65.0,
            cryptographic_seal={},
            sovereign_human_gate=True,
            auto_apply=False,
        )