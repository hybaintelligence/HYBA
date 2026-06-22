"""PYTHIA agent orchestration substrate.

This package lets PYTHIA spawn bounded quantum-native work, route it through
validated mathematical/external executors, and return sealed evidence packets.
It is production-governed: executor failures are converted to sealed failure
packets and, where a repair target is supplied, sovereign Salamander repair
proposals are staged instead of silently mutating source.
"""

from .pythia_agent_orchestrator import (
    AgentExecutionError,
    PythiaAgentInvariantError,
    PythiaAgentOrchestrator,
    PythiaMathematicalQuantumExecutor,
    PythiaSubAgent,
    QuantumResult,
    QuantumTask,
    verify_sealed_packet,
)

__all__ = [
    "AgentExecutionError",
    "PythiaAgentInvariantError",
    "PythiaAgentOrchestrator",
    "PythiaMathematicalQuantumExecutor",
    "PythiaSubAgent",
    "QuantumResult",
    "QuantumTask",
    "verify_sealed_packet",
]
