"""
Salamander Multi-Agent System - Base Agent Classes

Phase 5: Hierarchical Multi-Agent Coordination
Provides the foundational architecture for specialized AI agents with clear command-and-control layers.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel
import time
import asyncio


class AgentCapability(BaseModel):
    """Defines what an agent can do."""

    name: str
    description: str
    confidence_threshold: float = 75.0


class AgentTask(BaseModel):
    """A task assigned to an agent."""

    task_id: str
    task_type: str
    prompt: str
    target_files: List[str]
    context: Dict[str, Any] = {}
    priority: str = "medium"
    parent_task_id: Optional[str] = None


class AgentResult(BaseModel):
    """Result returned by an agent."""

    task_id: str
    agent_name: str
    status: str  # completed, failed, pending
    data: Dict[str, Any]
    confidence: float
    explanation: str
    timestamp: float
    execution_time_ms: float


class SalamanderAgent(ABC):
    """
    Base class for all Salamander agents.

    All specialized agents inherit from this class and implement the execute_task method.
    Provides common functionality for agent lifecycle, confidence scoring, and communication.
    """

    def __init__(
        self,
        name: str,
        role: str,
        capabilities: List[AgentCapability],
        confidence_threshold: float = 75.0,
    ):
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.confidence_threshold = confidence_threshold
        self.execution_count = 0
        self.success_count = 0
        self.total_execution_time_ms = 0.0

    @abstractmethod
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Execute a task assigned to this agent.

        All specialized agents must implement this method.
        """
        raise NotImplementedError("Agents must implement execute_task")

    async def can_handle_task(self, task: AgentTask) -> bool:
        """
        Determine if this agent can handle the given task based on capabilities.
        """
        # Simple capability matching - can be enhanced with more sophisticated logic
        task_type = task.task_type.lower()
        for capability in self.capabilities:
            if task_type in capability.name.lower():
                return True
        return False

    def calculate_confidence(self, data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the result.

        Base implementation - specialized agents can override with domain-specific logic.
        """
        # Default confidence based on execution success and data quality
        confidence = 50.0

        if data.get("status") == "completed":
            confidence += 30.0

        if data.get("verification_passed"):
            confidence += 15.0

        if data.get("error_count", 0) == 0:
            confidence += 5.0

        return min(100.0, confidence)

    def update_stats(self, success: bool, execution_time_ms: float):
        """Update agent execution statistics."""
        self.execution_count += 1
        if success:
            self.success_count += 1
        self.total_execution_time_ms += execution_time_ms

    def get_success_rate(self) -> float:
        """Calculate agent success rate."""
        if self.execution_count == 0:
            return 0.0
        return (self.success_count / self.execution_count) * 100.0

    def get_avg_execution_time_ms(self) -> float:
        """Calculate average execution time."""
        if self.execution_count == 0:
            return 0.0
        return self.total_execution_time_ms / self.execution_count

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information and statistics."""
        return {
            "name": self.name,
            "role": self.role,
            "capabilities": [cap.dict() for cap in self.capabilities],
            "confidence_threshold": self.confidence_threshold,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "success_rate": self.get_success_rate(),
            "avg_execution_time_ms": self.get_avg_execution_time_ms(),
        }


class SpecialistAgent(SalamanderAgent):
    """
    Base class for specialist agents (Frontend, Backend, Quantum, Security, etc.).

    Specialist agents focus on specific domains and provide deep expertise in their area.
    """

    def __init__(
        self,
        name: str,
        role: str,
        domain: str,
        capabilities: List[AgentCapability],
        confidence_threshold: float = 75.0,
    ):
        super().__init__(name, role, capabilities, confidence_threshold)
        self.domain = domain
        self.domain_patterns = self._get_domain_patterns()

    def _get_domain_patterns(self) -> List[str]:
        """Get file patterns associated with this agent's domain."""
        # Base implementation - specialized agents override
        return []

    def is_domain_file(self, file_path: str) -> bool:
        """Check if a file belongs to this agent's domain."""
        for pattern in self.domain_patterns:
            if pattern in file_path.lower():
                return True
        return False

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Execute task with domain-specific preprocessing.
        """
        start_time = time.time()

        # Filter files to domain-relevant ones
        domain_files = [f for f in task.target_files if self.is_domain_file(f)]

        if not domain_files:
            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed",
                data={"message": "No domain-relevant files found"},
                confidence=100.0,
                explanation=f"No {self.domain} files in task",
                timestamp=time.time(),
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Create domain-specific task
        domain_task = AgentTask(
            task_id=task.task_id,
            task_type=task.task_type,
            prompt=task.prompt,
            target_files=domain_files,
            context=task.context,
            priority=task.priority,
            parent_task_id=task.parent_task_id,
        )

        # Execute domain-specific logic
        result = await self._execute_domain_task(domain_task)

        execution_time_ms = (time.time() - start_time) * 1000
        self.update_stats(result.status == "completed", execution_time_ms)

        return AgentResult(
            task_id=task.task_id,
            agent_name=self.name,
            status=result.status,
            data=result.data,
            confidence=result.confidence,
            explanation=result.explanation,
            timestamp=time.time(),
            execution_time_ms=execution_time_ms,
        )

    @abstractmethod
    async def _execute_domain_task(self, task: AgentTask) -> AgentResult:
        """
        Execute domain-specific task logic.

        Specialist agents must implement this method.
        """
        raise NotImplementedError(
            "Specialist agents must implement _execute_domain_task"
        )
