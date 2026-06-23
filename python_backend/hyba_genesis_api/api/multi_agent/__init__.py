"""
Salamander Multi-Agent System

Phase 5: Hierarchical Multi-Agent Coordination
Provides specialized AI agents with clear command-and-control layers for autonomous regeneration.
"""

from .base_agent import (
    SalamanderAgent,
    SpecialistAgent,
    AgentTask,
    AgentResult,
    AgentCapability,
)
from .orchestrator import SalamanderOrchestrator, get_orchestrator
from .specialist_agents import (
    DiagnosisAgent,
    PlanningAgent,
    BackendSpecialist,
    FrontendSpecialist,
    VerificationSpecialist,
    ExecutorAgent,
)
from .swarm_communication import (
    SwarmMessage,
    SwarmCommunication,
    SwarmEnabledAgent,
    get_swarm_communication,
)
from .pso_allocator import (
    PSOParticle,
    PSOTaskAllocator,
    SwarmTaskCoordinator,
    get_task_coordinator,
)

__all__ = [
    "SalamanderAgent",
    "SpecialistAgent",
    "AgentTask",
    "AgentResult",
    "AgentCapability",
    "SalamanderOrchestrator",
    "get_orchestrator",
    "DiagnosisAgent",
    "PlanningAgent",
    "BackendSpecialist",
    "FrontendSpecialist",
    "VerificationSpecialist",
    "ExecutorAgent",
    "SwarmMessage",
    "SwarmCommunication",
    "SwarmEnabledAgent",
    "get_swarm_communication",
    "PSOParticle",
    "PSOTaskAllocator",
    "SwarmTaskCoordinator",
    "get_task_coordinator",
]
