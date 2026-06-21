"""
Salamander Multi-Agent System - Orchestrator

Phase 5: Hierarchical Multi-Agent Coordination
The Orchestrator is the strategic layer that coordinates all agents, manages task delegation,
and ensures proper escalation and communication between agents.
"""

from typing import Dict, List, Optional, Any
from .base_agent import SalamanderAgent, AgentTask, AgentResult, AgentCapability
import time
import asyncio
from datetime import datetime, timezone


class SalamanderOrchestrator:
    """
    Strategic layer agent that coordinates all other agents.
    
    Responsibilities:
    - Task decomposition and delegation
    - Agent selection and routing
    - Escalation and error handling
    - Result aggregation and verification
    - Communication with CEO Terminal
    """
    
    def __init__(self):
        self.agents: Dict[str, SalamanderAgent] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        self.escalation_queue: List[Dict[str, Any]] = []
        self.max_concurrent_tasks = 10
        self.task_timeout_seconds = 300  # 5 minutes per task
    
    def register_agent(self, agent: SalamanderAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        print(f"Registered agent: {agent.name} ({agent.role})")
    
    def get_agent(self, agent_name: str) -> Optional[SalamanderAgent]:
        """Get an agent by name."""
        return self.agents.get(agent_name)
    
    def get_available_agents(self) -> List[SalamanderAgent]:
        """Get all registered agents."""
        return list(self.agents.values())
    
    def get_agent_for_task(self, task: AgentTask) -> Optional[SalamanderAgent]:
        """
        Select the best agent for a given task based on capabilities.
        """
        candidates = []
        
        for agent in self.agents.values():
            if await agent.can_handle_task(task):
                candidates.append(agent)
        
        if not candidates:
            return None
        
        # Select agent with highest success rate
        candidates.sort(key=lambda a: a.get_success_rate(), reverse=True)
        return candidates[0]
    
    async def handle_regeneration(
        self,
        prompt: str,
        target_files: List[str],
        context: Dict[str, Any] = None,
        auto_approve_threshold: float = 85.0
    ) -> Dict[str, Any]:
        """
        Main entry point for regeneration requests.
        
        Orchestrates the full multi-agent pipeline:
        1. Diagnosis
        2. Planning
        3. Specialist delegation
        4. Verification
        5. Execution
        """
        regeneration_id = f"regen-{int(time.time() * 1000)}"
        context = context or {}
        
        # Track this regeneration
        self.active_tasks[regeneration_id] = {
            "status": "in_progress",
            "start_time": time.time(),
            "prompt": prompt,
            "target_files": target_files,
            "steps": []
        }
        
        try:
            # Step 1: Diagnosis
            diagnosis_result = await self._execute_step(
                regeneration_id,
                "diagnosis",
                prompt,
                target_files,
                context
            )
            
            if diagnosis_result["status"] == "failed":
                return self._handle_failure(regeneration_id, diagnosis_result)
            
            # Step 2: Planning
            planning_result = await self._execute_step(
                regeneration_id,
                "planning",
                diagnosis_result["data"]["diagnosis"],
                target_files,
                {**context, "diagnosis": diagnosis_result["data"]}
            )
            
            if planning_result["status"] == "failed":
                return self._handle_failure(regeneration_id, planning_result)
            
            # Step 3: Specialist Delegation
            specialist_results = await self._delegate_to_specialists(
                regeneration_id,
                planning_result["data"]["plan"],
                target_files,
                {**context, "diagnosis": diagnosis_result["data"], "plan": planning_result["data"]}
            )
            
            # Step 4: Verification
            verification_result = await self._execute_step(
                regeneration_id,
                "verification",
                specialist_results,
                target_files,
                {**context, "specialist_results": specialist_results}
            )
            
            # Step 5: Execution (if verification passed)
            if verification_result["data"].get("passed", False):
                execution_result = await self._execute_step(
                    regeneration_id,
                    "execution",
                    specialist_results,
                    target_files,
                    {**context, "verification": verification_result["data"]}
                )
                
                if execution_result["status"] == "completed":
                    self.active_tasks[regeneration_id]["status"] = "completed"
                    self.active_tasks[regeneration_id]["end_time"] = time.time()
                    
                    # Move to history
                    self.task_history.append(self.active_tasks[regeneration_id].copy())
                    del self.active_tasks[regeneration_id]
                    
                    return {
                        "regeneration_id": regeneration_id,
                        "status": "success",
                        "steps": self.active_tasks.get(regeneration_id, {}).get("steps", []),
                        "diagnosis": diagnosis_result["data"],
                        "plan": planning_result["data"],
                        "specialist_results": specialist_results,
                        "verification": verification_result["data"],
                        "execution": execution_result["data"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                else:
                    return self._handle_failure(regeneration_id, execution_result)
            else:
                # Verification failed, trigger self-healing
                return await self._handle_verification_failure(
                    regeneration_id,
                    verification_result,
                    specialist_results
                )
        
        except Exception as e:
            error_result = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            return self._handle_failure(regeneration_id, error_result)
    
    async def _execute_step(
        self,
        regeneration_id: str,
        step_name: str,
        prompt: str,
        target_files: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single step in the regeneration pipeline.
        """
        step_id = f"{regeneration_id}-{step_name}"
        
        task = AgentTask(
            task_id=step_id,
            task_type=step_name,
            prompt=str(prompt),
            target_files=target_files,
            context=context,
            priority="high",
            parent_task_id=regeneration_id
        )
        
        # Select appropriate agent
        agent = self.get_agent_for_task(task)
        
        if not agent:
            return {
                "status": "failed",
                "error": f"No agent available for task type: {step_name}",
                "step": step_name,
            }
        
        # Execute task with timeout
        try:
            result = await asyncio.wait_for(
                agent.execute_task(task),
                timeout=self.task_timeout_seconds
            )
            
            step_result = {
                "status": result.status,
                "step": step_name,
                "agent": agent.name,
                "data": result.data,
                "confidence": result.confidence,
                "explanation": result.explanation,
                "execution_time_ms": result.execution_time_ms,
                "timestamp": result.timestamp,
            }
            
            # Log step
            self.active_tasks[regeneration_id]["steps"].append(step_result)
            
            # Broadcast to CEO Terminal
            await self._broadcast_step_update(regeneration_id, step_result)
            
            return step_result
        
        except asyncio.TimeoutError:
            return {
                "status": "failed",
                "error": f"Task timeout after {self.task_timeout_seconds}s",
                "step": step_name,
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "step": step_name,
            }
    
    async def _delegate_to_specialists(
        self,
        regeneration_id: str,
        plan: Dict[str, Any],
        target_files: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delegate subtasks to specialist agents based on the plan.
        """
        subtasks = plan.get("subtasks", [])
        results = {}
        
        for subtask in subtasks:
            agent_name = subtask.get("assigned_agent")
            
            if not agent_name or agent_name not in self.agents:
                # Skip if no agent assigned or agent not found
                continue
            
            agent = self.agents[agent_name]
            
            task = AgentTask(
                task_id=f"{regeneration_id}-{subtask['name']}",
                task_type=subtask.get("type", "general"),
                prompt=subtask.get("prompt", ""),
                target_files=subtask.get("files", target_files),
                context={**context, "subtask": subtask},
                priority=subtask.get("priority", "medium"),
                parent_task_id=regeneration_id
            )
            
            try:
                result = await asyncio.wait_for(
                    agent.execute_task(task),
                    timeout=self.task_timeout_seconds
                )
                
                results[agent_name] = {
                    "status": result.status,
                    "data": result.data,
                    "confidence": result.confidence,
                    "explanation": result.explanation,
                }
                
                # Broadcast specialist update
                await self._broadcast_specialist_update(regeneration_id, agent_name, result)
            
            except asyncio.TimeoutError:
                results[agent_name] = {
                    "status": "failed",
                    "error": "Task timeout",
                }
            except Exception as e:
                results[agent_name] = {
                    "status": "failed",
                    "error": str(e),
                }
        
        return results
    
    async def _handle_verification_failure(
        self,
        regeneration_id: str,
        verification_result: Dict[str, Any],
        specialist_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle verification failure with self-healing retry logic.
        """
        # Add to escalation queue for human review if retries exhausted
        self.escalation_queue.append({
            "regeneration_id": regeneration_id,
            "reason": "verification_failed",
            "verification_result": verification_result,
            "specialist_results": specialist_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        
        return {
            "regeneration_id": regeneration_id,
            "status": "verification_failed",
            "escalated": True,
            "verification": verification_result,
            "specialist_results": specialist_results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def _handle_failure(self, regeneration_id: str, failure_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle task failure with proper cleanup and escalation.
        """
        if regeneration_id in self.active_tasks:
            self.active_tasks[regeneration_id]["status"] = "failed"
            self.active_tasks[regeneration_id]["end_time"] = time.time()
            self.active_tasks[regeneration_id]["error"] = failure_result.get("error", "Unknown error")
            
            # Move to history
            self.task_history.append(self.active_tasks[regeneration_id].copy())
            del self.active_tasks[regeneration_id]
        
        return {
            "regeneration_id": regeneration_id,
            "status": "failed",
            "error": failure_result.get("error", "Unknown error"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    async def _broadcast_step_update(self, regeneration_id: str, step_result: Dict[str, Any]):
        """
        Broadcast step update to CEO Terminal via WebSocket.
        """
        # Import here to avoid circular dependency
        from ..security import _manager
        
        await _manager.broadcast({
            "type": "regeneration_step",
            "regeneration_id": regeneration_id,
            "step": step_result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    async def _broadcast_specialist_update(self, regeneration_id: str, agent_name: str, result):
        """
        Broadcast specialist agent update to CEO Terminal.
        """
        from ..security import _manager
        
        await _manager.broadcast({
            "type": "agent_update",
            "regeneration_id": regeneration_id,
            "agent": agent_name,
            "result": {
                "status": result.status,
                "confidence": result.confidence,
                "explanation": result.explanation,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get overall orchestrator status and statistics."""
        return {
            "registered_agents": len(self.agents),
            "active_tasks": len(self.active_tasks),
            "task_history_size": len(self.task_history),
            "escalation_queue_size": len(self.escalation_queue),
            "agents": {name: agent.get_agent_info() for name, agent in self.agents.items()},
        }
    
    def get_task_status(self, regeneration_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific regeneration task."""
        if regeneration_id in self.active_tasks:
            return self.active_tasks[regeneration_id]
        
        # Check history
        for task in reversed(self.task_history):
            if task.get("prompt") == regeneration_id or task.get("regeneration_id") == regeneration_id:
                return task
        
        return None


# Global orchestrator instance
_orchestrator = SalamanderOrchestrator()


def get_orchestrator() -> SalamanderOrchestrator:
    """Get the global orchestrator instance."""
    return _orchestrator
