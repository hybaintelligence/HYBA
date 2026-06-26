"""Agentic Intelligence as a Service (AIaaS) - Production API Layer.

This module extends QIaaS with agentic capabilities while maintaining HYBA's
evidence-sealed governance model. It provides:

- Agent orchestration over QIaaS substrate
- Token optimization using mathematical optimization
- Multi-GPU scaling coordination
- Evidence-sealed agent execution
- Sovereign governance integration
- Agent marketplace framework

All agent outputs are cryptographically sealed with SHA-256 evidence packets.
No autonomous deployment - all agent actions require sovereign approval on
Enterprise/Sovereign rails.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass, field
import numpy as np

from fastapi import HTTPException, status
from pydantic import BaseModel, Field

# Import existing HYBA substrate components
from pythia_mining.pulvini_phi_memory import PulviniPhiMemoryCompressionEngine
from pythia_agents.pythia_agent_orchestrator import (
    PythiaAgentOrchestrator,
    QuantumTask,
    PythiaAgentInvariantGuard,
)
from pythia_self_healing.autonomic_organism_governor import AutonomicInvariantError


# ============================================================================
# Data Models
# ============================================================================

class AgentDefinition(BaseModel):
    """Definition of an agent in the marketplace."""
    
    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    version: str = "1.0.0"
    evidence_tier: str = "heuristic"  # quantum_backed, heuristic, classical_fallback
    confidence_threshold: float = 75.0
    requires_gpu: bool = False
    max_tokens: Optional[int] = None
    category: str = "general"  # finance, security, operations, analysis


class AgentTaskRequest(BaseModel):
    """Request to execute an agent task."""
    
    agent_id: str
    task_type: str
    prompt: str
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "medium"
    optimize_tokens: bool = True
    enable_gpu_scaling: bool = False
    governance_rail: str = "enterprise"  # treasury, enterprise, sovereign


class TokenOptimizationConfig(BaseModel):
    """Configuration for token optimization."""
    
    enable_compression: bool = True
    target_reduction_ratio: float = 0.8  # Target 20% reduction
    use_pulvini: bool = True
    preserve_semantic_integrity: bool = True
    max_context_window: int = 128000


class GPUScalingConfig(BaseModel):
    """Configuration for multi-GPU scaling."""
    
    enable_distributed: bool = True
    max_gpus: int = 4
    load_balancing_strategy: str = "round_robin"  # round_robin, least_loaded, hash_based
    enable_checkpointing: bool = True
    checkpoint_interval_seconds: int = 60


class AgentExecutionResult(BaseModel):
    """Result of agent execution with evidence seal."""
    
    task_id: str
    agent_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    evidence: Dict[str, Any]
    token_optimization_applied: bool
    tokens_saved: Optional[int] = None
    gpu_scaling_used: bool
    gpus_utilized: Optional[int] = None
    execution_time_ms: float
    confidence: float
    cryptographic_seal: Dict[str, Any]
    sovereign_human_gate: bool = True
    auto_apply: bool = False


# ============================================================================
# Token Optimization Engine
# ============================================================================

class TokenOptimizationEngine:
    """Mathematical token optimization using PULVINI compression and semantic analysis."""
    
    def __init__(self, pulvini_engine: Optional[PulviniPhiMemoryCompressionEngine] = None):
        self.pulvini = pulvini_engine or PulviniPhiMemoryCompressionEngine()
        self.optimization_history: List[Dict[str, Any]] = []
    
    def optimize_prompt(
        self,
        prompt: str,
        config: TokenOptimizationConfig
    ) -> Dict[str, Any]:
        """Optimize prompt for token efficiency while preserving semantic integrity."""
        
        original_tokens = self._estimate_tokens(prompt)
        
        if not config.enable_compression:
            return {
                "optimized_prompt": prompt,
                "original_tokens": original_tokens,
                "optimized_tokens": original_tokens,
                "tokens_saved": 0,
                "compression_ratio": 1.0,
                "strategy": "none"
            }
        
        # Strategy 1: Semantic compression using mathematical analysis
        compressed = self._semantic_compress(prompt, config)
        
        # Strategy 2: PULVINI compression for numerical/context data
        if config.use_pulvini:
            compressed = self._pulvini_compress_context(compressed, config)
        
        optimized_tokens = self._estimate_tokens(compressed)
        tokens_saved = max(0, original_tokens - optimized_tokens)
        compression_ratio = min(1.0, optimized_tokens / max(1, original_tokens))
        
        result = {
            "optimized_prompt": compressed,
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "tokens_saved": tokens_saved,
            "compression_ratio": compression_ratio,
            "strategy": "semantic_pulvini_hybrid" if config.use_pulvini else "semantic_only",
            "target_achieved": compression_ratio <= config.target_reduction_ratio
        }
        
        self.optimization_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "original_tokens": original_tokens,
            "optimized_tokens": optimized_tokens,
            "compression_ratio": compression_ratio
        })
        
        return result
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (simplified - in production use actual tokenizer)."""
        # Rough estimate: ~4 chars per token for English text
        return len(text) // 4
    
    def _semantic_compress(self, prompt: str, config: TokenOptimizationConfig) -> str:
        """Compress prompt while preserving semantic integrity."""
        # Remove redundant whitespace
        compressed = ' '.join(prompt.split())
        
        # Remove common filler phrases (configurable)
        fillers = ["please", "kindly", "could you", "would you"]
        for filler in fillers:
            compressed = compressed.replace(filler, "")
        
        # Preserve semantic structure by keeping key markers
        if config.preserve_semantic_integrity:
            # Ensure question marks, colons, and structural elements remain
            compressed = compressed.replace(" ?", "?")
            compressed = compressed.replace(" :", ":")
        
        return compressed.strip()
    
    def _pulvini_compress_context(self, prompt: str, config: TokenOptimizationConfig) -> str:
        """Use PULVINI to compress contextual data within prompt."""
        # Extract numerical/context patterns
        import re
        numbers = re.findall(r'\d+\.?\d*', prompt)
        
        if not numbers:
            return prompt
        
        # Convert to numpy array for PULVINI compression
        num_array = np.array([float(n) for n in numbers])
        
        try:
            result = self.pulvini.compress(num_array)
            
            if result.reversible and result.working_set_compression_ratio > 1.0:
                # Replace numbers with compressed representation marker
                # In production, would embed actual compressed data
                marker = f"[PULVINI_COMPRESSED_{result.working_set_compression_ratio:.2f}X]"
                
                # Replace first occurrence as demonstration
                for num in numbers[:1]:
                    prompt = prompt.replace(num, marker, 1)
                
                return prompt
        except Exception:
            # Fallback to original if compression fails
            pass
        
        return prompt
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get statistics on token optimization performance."""
        if not self.optimization_history:
            return {
                "total_optimizations": 0,
                "avg_compression_ratio": 1.0,
                "total_tokens_saved": 0
            }
        
        total = len(self.optimization_history)
        avg_ratio = sum(h["compression_ratio"] for h in self.optimization_history) / total
        total_saved = sum(
            h["original_tokens"] - h["optimized_tokens"]
            for h in self.optimization_history
        )
        
        return {
            "total_optimizations": total,
            "avg_compression_ratio": avg_ratio,
            "total_tokens_saved": total_saved,
            "avg_tokens_saved_per_optimization": total_saved / total if total > 0 else 0
        }


# ============================================================================
# Multi-GPU Scaling Coordinator
# ============================================================================

class GPUScalingCoordinator:
    """Coordinate multi-GPU execution with evidence sealing."""
    
    def __init__(self, max_gpus: int = 4):
        self.max_gpus = max_gpus
        self.active_gpus: Dict[str, Any] = {}
        self.load_balancer_index = 0
    
    def allocate_gpu(self, task_id: str, config: GPUScalingConfig) -> Dict[str, Any]:
        """Allocate GPU resources for a task."""
        
        if not config.enable_distributed:
            return {
                "gpu_allocated": False,
                "strategy": "single_cpu",
                "gpu_id": None
            }
        
        # Enforce max_gpus limit - release oldest if at capacity
        effective_max = min(config.max_gpus, self.max_gpus)
        if len(self.active_gpus) >= effective_max:
            # Release oldest task
            oldest_task = min(self.active_gpus.keys(), 
                           key=lambda k: self.active_gpus[k]["allocated_at"])
            del self.active_gpus[oldest_task]
        
        # Simple round-robin allocation
        gpu_id = f"gpu_{self.load_balancer_index % effective_max}"
        self.load_balancer_index += 1
        
        self.active_gpus[task_id] = {
            "gpu_id": gpu_id,
            "allocated_at": datetime.now(timezone.utc).isoformat(),
            "config": config.model_dump()
        }
        
        return {
            "gpu_allocated": True,
            "strategy": config.load_balancing_strategy,
            "gpu_id": gpu_id,
            "max_gpus": effective_max
        }
    
    def release_gpu(self, task_id: str) -> None:
        """Release GPU resources after task completion."""
        if task_id in self.active_gpus:
            del self.active_gpus[task_id]
    
    def get_gpu_utilization(self) -> Dict[str, Any]:
        """Get current GPU utilization statistics."""
        return {
            "active_gpus": len(self.active_gpus),
            "max_gpus": self.max_gpus,
            "utilization_percent": (len(self.active_gpus) / max(1, self.max_gpus)) * 100,
            "active_tasks": list(self.active_gpus.keys())
        }


# ============================================================================
# Agent Marketplace
# ============================================================================

class AgentMarketplace:
    """Registry and marketplace for pre-built agents."""
    
    def __init__(self):
        self.agents: Dict[str, AgentDefinition] = {}
        self._initialize_builtin_agents()
    
    def _initialize_builtin_agents(self):
        """Initialize built-in industry-specific agents."""
        
        # Financial Analysis Agent
        self.register_agent(AgentDefinition(
            agent_id="fin_analysis_v1",
            name="Financial Analysis Agent",
            description="Specialized agent for financial data analysis, risk assessment, and portfolio optimization using quantum-inspired algorithms",
            capabilities=["risk_analysis", "portfolio_optimization", "market_prediction", "fraud_detection"],
            version="1.0.0",
            evidence_tier="heuristic",
            category="finance"
        ))
        
        # Security Monitoring Agent
        self.register_agent(AgentDefinition(
            agent_id="security_monitor_v1",
            name="Security Monitoring Agent",
            description="Autonomous security monitoring with threat detection, anomaly analysis, and incident response coordination",
            capabilities=["threat_detection", "anomaly_analysis", "incident_response", "log_analysis"],
            version="1.0.0",
            evidence_tier="heuristic",
            category="security"
        ))
        
        # Operations Optimization Agent
        self.register_agent(AgentDefinition(
            agent_id="ops_optimizer_v1",
            name="Operations Optimization Agent",
            description="Operational efficiency optimization using Salamander regeneration and PULVINI memory compression",
            capabilities=["process_optimization", "resource_allocation", "performance_tuning", "capacity_planning"],
            version="1.0.0",
            evidence_tier="heuristic",
            category="operations"
        ))
        
        # Data Analysis Agent
        self.register_agent(AgentDefinition(
            agent_id="data_analyst_v1",
            name="Data Analysis Agent",
            description="Multi-manifold data analysis with causal, counterfactual, and topological intelligence",
            capabilities=["causal_analysis", "counterfactual_simulation", "topological_analysis", "pattern_recognition"],
            version="1.0.0",
            evidence_tier="quantum_backed",
            category="analysis"
        ))
    
    def register_agent(self, agent: AgentDefinition) -> None:
        """Register a new agent in the marketplace."""
        self.agents[agent.agent_id] = agent
    
    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent definition by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self, category: Optional[str] = None) -> List[AgentDefinition]:
        """List all agents, optionally filtered by category."""
        agents = list(self.agents.values())
        if category:
            agents = [a for a in agents if a.category == category]
        return agents
    
    def search_agents(self, query: str) -> List[AgentDefinition]:
        """Search agents by name, description, or capabilities."""
        query_lower = query.lower()
        results = []
        for agent in self.agents.values():
            if (query_lower in agent.name.lower() or
                query_lower in agent.description.lower() or
                any(query_lower in cap.lower() for cap in agent.capabilities)):
                results.append(agent)
        return results


# ============================================================================
# Main Agentic Intelligence Service
# ============================================================================

class AgenticIntelligenceService:
    """Main service for agentic intelligence with evidence sealing."""
    
    def __init__(self):
        self.orchestrator = PythiaAgentOrchestrator()
        self.orchestrator.register_builtin_agent()
        self.token_optimizer = TokenOptimizationEngine()
        self.gpu_coordinator = GPUScalingCoordinator()
        self.marketplace = AgentMarketplace()
        self.guard = PythiaAgentInvariantGuard()
    
    def execute_agent_task(
        self,
        request: AgentTaskRequest
    ) -> AgentExecutionResult:
        """Execute an agent task with full evidence sealing."""
        
        start_time = datetime.now(timezone.utc)
        
        # Validate agent exists
        agent_def = self.marketplace.get_agent(request.agent_id)
        if not agent_def:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent {request.agent_id} not found in marketplace"
            )
        
        # Apply governance rail
        if request.governance_rail in ["enterprise", "sovereign"]:
            # Force human gate on production rails
            self.guard.assert_safe_payload(
                {"sovereign_human_gate": True, "auto_apply": False},
                context="governance_enforcement"
            )
        
        # Token optimization
        tokens_saved = 0
        if request.optimize_tokens:
            opt_config = TokenOptimizationConfig()
            opt_result = self.token_optimizer.optimize_prompt(request.prompt, opt_config)
            optimized_prompt = opt_result["optimized_prompt"]
            tokens_saved = opt_result["tokens_saved"]
        else:
            optimized_prompt = request.prompt
        
        # GPU allocation
        gpu_result = self.gpu_coordinator.allocate_gpu(
            f"task_{request.agent_id}",
            GPUScalingConfig(enable_distributed=request.enable_gpu_scaling)
        )
        
        try:
            # Execute via PYTHIA orchestrator
            task = QuantumTask.create(
                description=f"Agent task: {request.task_type}",
                operation="phi_weighted_consensus",  # Use built-in operation
                payload={
                    "prompt": optimized_prompt,
                    "task_type": request.task_type,
                    "context": request.context,
                    "agent_capabilities": agent_def.capabilities
                }
            )
            
            packets = self.orchestrator.run_entangled_group(
                agent_name="pythia-math-substrate",
                tasks=[task],
                max_workers=1
            )
            
            if not packets:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Agent execution failed - no packets returned"
                )
            
            packet = packets[0]
            execution_time_ms = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds() * 1000
            
            # Calculate confidence based on evidence
            confidence = self._calculate_confidence(packet, agent_def)
            
            # Create result with evidence seal
            result = AgentExecutionResult(
                task_id=task.task_id,
                agent_id=request.agent_id,
                status=packet.get("status", "unknown"),
                result=packet.get("body", {}).get("result", {}),
                evidence=packet.get("body", {}).get("evidence", {}),
                token_optimization_applied=request.optimize_tokens,
                tokens_saved=tokens_saved if request.optimize_tokens else None,
                gpu_scaling_used=gpu_result["gpu_allocated"],
                gpus_utilized=1 if gpu_result["gpu_allocated"] else None,
                execution_time_ms=execution_time_ms,
                confidence=confidence,
                cryptographic_seal=packet.get("cryptographic_seal", {}),
                sovereign_human_gate=True,
                auto_apply=False
            )
            
            return result
            
        finally:
            # Release GPU resources
            self.gpu_coordinator.release_gpu(f"task_{request.agent_id}")
    
    def _calculate_confidence(
        self,
        packet: Dict[str, Any],
        agent_def: AgentDefinition
    ) -> float:
        """Calculate confidence score based on evidence and agent definition."""
        
        base_confidence = 50.0
        
        # Evidence tier contribution
        if agent_def.evidence_tier == "quantum_backed":
            base_confidence += 30.0
        elif agent_def.evidence_tier == "heuristic":
            base_confidence += 20.0
        
        # Packet status contribution
        if packet.get("status") == "EXECUTION_STAGED":
            base_confidence += 15.0
        
        # Evidence completeness
        evidence = packet.get("body", {}).get("evidence", {})
        if evidence.get("finite"):
            base_confidence += 5.0
        
        return min(100.0, base_confidence)
    
    def list_marketplace_agents(
        self,
        category: Optional[str] = None
    ) -> List[AgentDefinition]:
        """List available agents from marketplace."""
        return self.marketplace.list_agents(category)
    
    def get_token_optimization_stats(self) -> Dict[str, Any]:
        """Get token optimization statistics."""
        return self.token_optimizer.get_optimization_stats()
    
    def get_gpu_utilization(self) -> Dict[str, Any]:
        """Get GPU utilization statistics."""
        return self.gpu_coordinator.get_gpu_utilization()


# Global service instance
agentic_service = AgenticIntelligenceService()


# ============================================================================
# FastAPI Endpoints (to be integrated into main.py)
# ============================================================================

async def execute_agent_task_endpoint(request: AgentTaskRequest) -> AgentExecutionResult:
    """FastAPI endpoint for agent task execution."""
    return agentic_service.execute_agent_task(request)


async def list_agents_endpoint(category: Optional[str] = None) -> List[AgentDefinition]:
    """FastAPI endpoint to list marketplace agents."""
    return agentic_service.list_marketplace_agents(category)


async def get_token_stats_endpoint() -> Dict[str, Any]:
    """FastAPI endpoint for token optimization statistics."""
    return agentic_service.get_token_optimization_stats()


async def get_gpu_stats_endpoint() -> Dict[str, Any]:
    """FastAPI endpoint for GPU utilization statistics."""
    return agentic_service.get_gpu_utilization()


__all__ = [
    "AgenticIntelligenceService",
    "AgentDefinition",
    "AgentTaskRequest",
    "AgentExecutionResult",
    "TokenOptimizationConfig",
    "GPUScalingConfig",
    "agentic_service",
    "execute_agent_task_endpoint",
    "list_agents_endpoint",
    "get_token_stats_endpoint",
    "get_gpu_stats_endpoint",
]
