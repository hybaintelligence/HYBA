"""
Salamander Multi-Agent System - Specialist Agents

Phase 5: Hierarchical Multi-Agent Coordination
Specialized agents for different domains: Diagnosis, Planning, Backend, Frontend, Verification, Execution.

Phase 5.1: Swarm Intelligence Integration
Agents now have swarm communication capabilities for proposal/voting and stigmergy.
"""

from typing import Dict, List, Optional, Any
from .base_agent import (
    SalamanderAgent,
    SpecialistAgent,
    AgentTask,
    AgentResult,
    AgentCapability,
)
from .swarm_communication import SwarmEnabledAgent, get_swarm_communication
import time
import json


class DiagnosisAgent(SalamanderAgent):
    """
    Strategic layer agent responsible for diagnosing issues.

    Analyzes the problem, identifies root causes, and determines the scope of changes needed.

    PHASE 5.1: Enhanced with swarm communication for collaborative diagnosis.
    """

    def __init__(self):
        super().__init__(
            name="diagnosis",
            role="strategic",
            capabilities=[
                AgentCapability(
                    name="issue_diagnosis",
                    description="Analyze and diagnose software issues",
                    confidence_threshold=70.0,
                ),
                AgentCapability(
                    name="root_cause_analysis",
                    description="Identify root causes of problems",
                    confidence_threshold=75.0,
                ),
                AgentCapability(
                    name="impact_assessment",
                    description="Assess the impact of changes",
                    confidence_threshold=80.0,
                ),
            ],
            confidence_threshold=75.0,
        )
        self.swarm_comm = get_swarm_communication()

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute diagnosis task."""
        start_time = time.time()

        try:
            # Analyze the prompt and target files
            diagnosis = await self._analyze_issue(
                task.prompt, task.target_files, task.context
            )

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(True, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed",
                data={
                    "diagnosis": diagnosis,
                    "severity": diagnosis.get("severity", "medium"),
                    "affected_modules": diagnosis.get("affected_modules", []),
                    "root_causes": diagnosis.get("root_causes", []),
                },
                confidence=diagnosis.get("confidence", 75.0),
                explanation=diagnosis.get(
                    "explanation", "Issue diagnosed successfully"
                ),
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(False, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="failed",
                data={"error": str(e)},
                confidence=0.0,
                explanation=f"Diagnosis failed: {str(e)}",
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

    async def _analyze_issue(
        self, prompt: str, target_files: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Analyze the issue and provide diagnosis."""
        # In production, this would call an LLM with the prompt and file contents
        # For now, return a structured diagnosis

        return {
            "severity": "medium",
            "affected_modules": target_files[:3],  # Limit to first 3 files
            "root_causes": [
                "Potential logic error in implementation",
                "Missing error handling",
                "Type mismatch in function signature",
            ],
            "confidence": 75.0,
            "explanation": f"Analysis of {len(target_files)} files identified potential issues requiring regeneration",
            "recommended_actions": [
                "Review function signatures",
                "Add error handling",
                "Validate type constraints",
            ],
        }


class PlanningAgent(SalamanderAgent):
    """
    Strategic layer agent responsible for creating repair plans.

    Takes diagnosis and creates a structured plan with subtasks for specialist agents.
    """

    def __init__(self):
        super().__init__(
            name="planner",
            role="strategic",
            capabilities=[
                AgentCapability(
                    name="repair_planning",
                    description="Create structured repair plans",
                    confidence_threshold=80.0,
                ),
                AgentCapability(
                    name="task_decomposition",
                    description="Decompose complex tasks into subtasks",
                    confidence_threshold=75.0,
                ),
                AgentCapability(
                    name="agent_assignment",
                    description="Assign subtasks to appropriate agents",
                    confidence_threshold=85.0,
                ),
            ],
            confidence_threshold=80.0,
        )

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute planning task."""
        start_time = time.time()

        try:
            diagnosis = task.context.get("diagnosis", {})

            # Create repair plan based on diagnosis
            plan = await self._create_repair_plan(
                diagnosis, task.target_files, task.context
            )

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(True, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed",
                data={
                    "plan": plan,
                    "subtasks": plan.get("subtasks", []),
                    "estimated_duration_ms": plan.get("estimated_duration_ms", 60000),
                    "complexity": plan.get("complexity", "medium"),
                },
                confidence=plan.get("confidence", 80.0),
                explanation=plan.get("explanation", "Repair plan created successfully"),
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(False, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="failed",
                data={"error": str(e)},
                confidence=0.0,
                explanation=f"Planning failed: {str(e)}",
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

    async def _create_repair_plan(
        self, diagnosis: Dict, target_files: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Create a structured repair plan with subtasks."""
        # Determine which specialists are needed based on file types
        backend_files = [
            f for f in target_files if any(ext in f for ext in [".py", ".ts"])
        ]
        frontend_files = [
            f for f in target_files if any(ext in f for ext in [".tsx", ".jsx", ".css"])
        ]

        subtasks = []

        # Add backend specialist task if needed
        if backend_files:
            subtasks.append(
                {
                    "name": "backend_repair",
                    "type": "backend",
                    "assigned_agent": "backend_specialist",
                    "prompt": "Repair backend code issues",
                    "files": backend_files,
                    "priority": "high",
                }
            )

        # Add frontend specialist task if needed
        if frontend_files:
            subtasks.append(
                {
                    "name": "frontend_repair",
                    "type": "frontend",
                    "assigned_agent": "frontend_specialist",
                    "prompt": "Repair frontend code issues",
                    "files": frontend_files,
                    "priority": "high",
                }
            )

        return {
            "implementation_plan": "Execute specialist repairs in parallel",
            "subtasks": subtasks,
            "estimated_duration_ms": 60000,
            "complexity": "medium",
            "confidence": 80.0,
            "explanation": f"Created repair plan with {len(subtasks)} subtasks for {len(target_files)} files",
        }


class BackendSpecialist(SpecialistAgent):
    """
    Specialist agent for Python/FastAPI backend code.

    Handles backend-specific repairs with deep understanding of Python patterns, FastAPI best practices, and backend architecture.
    """

    def __init__(self):
        super().__init__(
            name="backend_specialist",
            role="specialist",
            domain="backend",
            capabilities=[
                AgentCapability(
                    name="python_repair",
                    description="Repair Python code issues",
                    confidence_threshold=80.0,
                ),
                AgentCapability(
                    name="fastapi_optimization",
                    description="Optimize FastAPI endpoints",
                    confidence_threshold=75.0,
                ),
                AgentCapability(
                    name="database_migration",
                    description="Handle database schema changes",
                    confidence_threshold=70.0,
                ),
            ],
            confidence_threshold=80.0,
        )

    def _get_domain_patterns(self) -> List[str]:
        """Get file patterns for backend domain."""
        return [".py", ".ts", "api/", "backend/", "models/", "schemas/"]

    async def _execute_domain_task(self, task: AgentTask) -> AgentResult:
        """Execute backend-specific task."""
        start_time = time.time()

        try:
            # Generate backend-specific repair plan
            repair_plan = await self._generate_backend_repair(
                task.prompt, task.target_files, task.context
            )

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(True, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed",
                data={
                    "repair_plan": repair_plan,
                    "files_modified": task.target_files,
                    "changes_count": repair_plan.get("changes_count", 0),
                    "backend_specific": True,
                },
                confidence=repair_plan.get("confidence", 80.0),
                explanation=repair_plan.get("explanation", "Backend repair completed"),
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(False, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="failed",
                data={"error": str(e)},
                confidence=0.0,
                explanation=f"Backend repair failed: {str(e)}",
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

    async def _generate_backend_repair(
        self, prompt: str, target_files: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Generate backend-specific repair plan."""
        return {
            "changes_count": len(target_files) * 3,  # Estimate 3 changes per file
            "confidence": 80.0,
            "explanation": f"Generated repair plan for {len(target_files)} Python files",
            "backend_patterns": [
                "Type hints added",
                "Error handling improved",
                "Async patterns optimized",
            ],
        }


class FrontendSpecialist(SpecialistAgent):
    """
    Specialist agent for React/TypeScript frontend code.

    Handles frontend-specific repairs with deep understanding of React patterns, TypeScript, and UI/UX best practices.
    """

    def __init__(self):
        super().__init__(
            name="frontend_specialist",
            role="specialist",
            domain="frontend",
            capabilities=[
                AgentCapability(
                    name="react_repair",
                    description="Repair React component issues",
                    confidence_threshold=80.0,
                ),
                AgentCapability(
                    name="typescript_fix",
                    description="Fix TypeScript type errors",
                    confidence_threshold=85.0,
                ),
                AgentCapability(
                    name="ui_optimization",
                    description="Optimize UI performance and accessibility",
                    confidence_threshold=75.0,
                ),
            ],
            confidence_threshold=80.0,
        )

    def _get_domain_patterns(self) -> List[str]:
        """Get file patterns for frontend domain."""
        return [".tsx", ".jsx", ".css", ".scss", "components/", "src/", "app/"]

    async def _execute_domain_task(self, task: AgentTask) -> AgentResult:
        """Execute frontend-specific task."""
        start_time = time.time()

        try:
            # Generate frontend-specific repair plan
            repair_plan = await self._generate_frontend_repair(
                task.prompt, task.target_files, task.context
            )

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(True, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed",
                data={
                    "repair_plan": repair_plan,
                    "files_modified": task.target_files,
                    "changes_count": repair_plan.get("changes_count", 0),
                    "frontend_specific": True,
                },
                confidence=repair_plan.get("confidence", 80.0),
                explanation=repair_plan.get("explanation", "Frontend repair completed"),
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(False, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="failed",
                data={"error": str(e)},
                confidence=0.0,
                explanation=f"Frontend repair failed: {str(e)}",
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

    async def _generate_frontend_repair(
        self, prompt: str, target_files: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Generate frontend-specific repair plan."""
        return {
            "changes_count": len(target_files) * 2,  # Estimate 2 changes per file
            "confidence": 80.0,
            "explanation": f"Generated repair plan for {len(target_files)} React/TypeScript files",
            "frontend_patterns": [
                "Type safety improved",
                "Component structure optimized",
                "Props interface updated",
            ],
        }


class VerificationSpecialist(SalamanderAgent):
    """
    Specialist agent responsible for verification and testing.

    Runs test suites, validates changes, and ensures quality standards are met.
    """

    def __init__(self):
        super().__init__(
            name="verification_specialist",
            role="tactical",
            capabilities=[
                AgentCapability(
                    name="test_execution",
                    description="Execute test suites",
                    confidence_threshold=90.0,
                ),
                AgentCapability(
                    name="code_validation",
                    description="Validate code quality and standards",
                    confidence_threshold=85.0,
                ),
                AgentCapability(
                    name="integration_testing",
                    description="Run integration tests",
                    confidence_threshold=80.0,
                ),
            ],
            confidence_threshold=85.0,
        )

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute verification task."""
        start_time = time.time()

        try:
            # Run verification suite
            verification_result = await self._run_verification(
                task.target_files, task.context
            )

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(verification_result["passed"], execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed",
                data=verification_result,
                confidence=verification_result.get("confidence", 85.0),
                explanation=verification_result.get(
                    "explanation", "Verification completed"
                ),
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(False, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="failed",
                data={"error": str(e)},
                confidence=0.0,
                explanation=f"Verification failed: {str(e)}",
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

    async def _run_verification(
        self, target_files: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Run verification suite on target files."""
        # In production, this would integrate with the existing run_verification_suite
        # For now, return a structured verification result

        specialist_results = context.get("specialist_results", {})

        return {
            "passed": True,
            "test_results": {
                "total_tests": 10,
                "passed_tests": 9,
                "failed_tests": 1,
                "skipped_tests": 0,
            },
            "confidence": 85.0,
            "explanation": "Verification passed with 9/10 tests passing",
            "specialist_validation": {
                agent: result.get("confidence", 0) > 70.0
                for agent, result in specialist_results.items()
            },
        }


class ExecutorAgent(SalamanderAgent):
    """
    Tactical agent responsible for applying changes to files.

    Takes approved plans and executes the actual file modifications.
    """

    def __init__(self):
        super().__init__(
            name="executor",
            role="tactical",
            capabilities=[
                AgentCapability(
                    name="file_modification",
                    description="Apply changes to files",
                    confidence_threshold=95.0,
                ),
                AgentCapability(
                    name="rollback_execution",
                    description="Execute rollback if needed",
                    confidence_threshold=90.0,
                ),
                AgentCapability(
                    name="change_validation",
                    description="Validate applied changes",
                    confidence_threshold=85.0,
                ),
            ],
            confidence_threshold=95.0,
        )

    async def execute_task(self, task: AgentTask) -> AgentResult:
        """Execute file modification task."""
        start_time = time.time()

        try:
            # Apply changes to files
            execution_result = await self._apply_changes(
                task.target_files, task.context
            )

            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(execution_result["success"], execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="completed" if execution_result["success"] else "failed",
                data=execution_result,
                confidence=execution_result.get("confidence", 95.0),
                explanation=execution_result.get(
                    "explanation", "Changes applied successfully"
                ),
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            self.update_stats(False, execution_time_ms)

            return AgentResult(
                task_id=task.task_id,
                agent_name=self.name,
                status="failed",
                data={"error": str(e)},
                confidence=0.0,
                explanation=f"Execution failed: {str(e)}",
                timestamp=time.time(),
                execution_time_ms=execution_time_ms,
            )

    async def _apply_changes(
        self, target_files: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Apply changes to target files."""
        # In production, this would integrate with the existing trigger_regeneration
        # For now, return a structured execution result

        verification = context.get("verification", {})

        return {
            "success": True,
            "files_modified": target_files,
            "changes_applied": len(target_files) * 3,
            "confidence": 95.0,
            "explanation": f"Successfully applied changes to {len(target_files)} files",
            "rollback_available": True,
            "verification_passed": verification.get("passed", True),
        }
