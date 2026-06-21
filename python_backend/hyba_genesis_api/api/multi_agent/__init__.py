"""
Salamander Multi-Agent System

Phase 5: Hierarchical Multi-Agent Coordination
Provides specialized AI agents with clear command-and-control layers for autonomous regeneration.
"""

from .base_agent import SalamanderAgent, SpecialistAgent, AgentTask, AgentResult, AgentCapability
from .orchestrator import SalamanderOrchestrator, get_orchestrator
from .specialist_agents import (
    DiagnosisAgent,
    PlanningAgent,
    BackendSpecialist,
    FrontendSpecialist,
    VerificationSpecialist,
    ExecutorAgent,
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
]
