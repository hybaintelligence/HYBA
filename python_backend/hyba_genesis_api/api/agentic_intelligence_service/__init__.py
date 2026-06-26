"""Agentic Intelligence as a Service (AIaaS) API Router.

This module provides FastAPI endpoints for agentic intelligence capabilities
including agent execution, token optimization, multi-GPU scaling, and the agent marketplace.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status

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
    execute_agent_task_endpoint,
    list_agents_endpoint,
    get_token_stats_endpoint,
    get_gpu_stats_endpoint,
)


router = APIRouter(
    prefix="/api/agentic",
    tags=["agentic-intelligence"],
)


@router.post("/execute", response_model=AgentExecutionResult)
async def execute_agent_task(request: AgentTaskRequest) -> AgentExecutionResult:
    """Execute an agent task with evidence sealing and governance.
    
    This endpoint:
    - Validates the agent exists in the marketplace
    - Applies token optimization if requested
    - Allocates GPU resources if scaling is enabled
    - Executes the task via PYTHIA orchestrator
    - Returns cryptographically sealed evidence
    - Enforces sovereign human gate on Enterprise/Sovereign rails
    
    Args:
        request: Agent task specification with governance rail configuration
    
    Returns:
        AgentExecutionResult with cryptographic seal and evidence packet
    """
    return await execute_agent_task_endpoint(request)


@router.get("/agents", response_model=List[AgentDefinition])
async def list_agents(category: Optional[str] = None) -> List[AgentDefinition]:
    """List available agents from the marketplace.
    
    Args:
        category: Optional filter by agent category (finance, security, operations, analysis)
    
    Returns:
        List of agent definitions with capabilities and metadata
    """
    return await list_agents_endpoint(category)


@router.get("/agents/{agent_id}", response_model=AgentDefinition)
async def get_agent(agent_id: str) -> AgentDefinition:
    """Get a specific agent definition by ID.
    
    Args:
        agent_id: Unique identifier for the agent
    
    Returns:
        Agent definition with capabilities and metadata
    
    Raises:
        HTTPException 404 if agent not found
    """
    agent = agentic_service.marketplace.get_agent(agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent {agent_id} not found"
        )
    return agent


@router.get("/search/agents")
async def search_agents(query: str) -> List[AgentDefinition]:
    """Search agents by name, description, or capabilities.
    
    Args:
        query: Search query string
    
    Returns:
        List of matching agent definitions
    """
    return agentic_service.marketplace.search_agents(query)


@router.get("/optimization/tokens/stats", response_model=None)
async def get_token_optimization_stats():
    """Get token optimization performance statistics.
    
    Returns:
        Statistics including total optimizations, average compression ratio,
        and total tokens saved
    """
    return await get_token_stats_endpoint()


@router.get("/scaling/gpu/stats", response_model=None)
async def get_gpu_scaling_stats():
    """Get GPU utilization statistics.
    
    Returns:
        Current GPU utilization including active GPUs, max capacity,
        and utilization percentage
    """
    return await get_gpu_stats_endpoint()


@router.post("/optimization/tokens/config")
async def update_token_optimization_config(config: TokenOptimizationConfig) -> Dict[str, str]:
    """Update token optimization configuration.
    
    Args:
        config: New token optimization configuration
    
    Returns:
        Confirmation message
    """
    # In production, this would update the service configuration
    return {"status": "config_updated", "message": "Token optimization configuration updated"}


@router.post("/scaling/gpu/config")
async def update_gpu_scaling_config(config: GPUScalingConfig) -> Dict[str, str]:
    """Update GPU scaling configuration.
    
    Args:
        config: New GPU scaling configuration
    
    Returns:
        Confirmation message
    """
    # In production, this would update the coordinator configuration
    return {"status": "config_updated", "message": "GPU scaling configuration updated"}


__all__ = ["router"]
