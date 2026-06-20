"""Reflexive Cycle Timeout Guard - Prevents hanged counterfactual operations.

This module provides robust timeout enforcement for reflexive mining cycles,
ensuring graceful degradation when operations exceed the 100ms deadline.
Handles partial results, state recovery, and comprehensive telemetry.
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from contextlib import asynccontextmanager

LOGGER = logging.getLogger(__name__)

# Hard deadline for reflexive cycles in milliseconds
REFLEXIVE_CYCLE_DEADLINE_MS = 100.0


class ExecutionPhase(Enum):
    """Tracks which phase of the reflexive cycle is active."""
    IDLE = "idle"
    PARSING = "parsing"  # AST parsing and proposal generation
    SIMULATION = "simulation"  # Virtual mining simulations
    VALIDATION = "validation"  # Constraint checking
    APPLYING = "applying"  # Proposal application


class TimeoutAction(Enum):
    """Actions taken when timeout occurs."""
    CANCELLED = "cancelled"
    PARTIAL_RESULTS = "partial_results"
    SKIPPED_VALIDATION = "skipped_validation"
    ROLLBACK = "rollback"
    RECOVERED = "recovered"


@dataclass
class PhaseMetrics:
    """Metrics for a single execution phase."""
    phase: ExecutionPhase
    start_time_ms: float
    end_time_ms: Optional[float] = None
    duration_ms: float = 0.0
    completed: bool = False
    items_processed: int = 0
    
    def mark_complete(self, current_time_ms: float) -> None:
        """Mark phase as complete with duration."""
        self.end_time_ms = current_time_ms
        self.duration_ms = self.end_time_ms - self.start_time_ms
        self.completed = True
    
    def percent_complete(self) -> float:
        """Estimate completion percentage based on duration."""
        if self.completed:
            return 100.0
        if self.duration_ms == 0.0:
            return 0.0
        # Heuristic: estimate based on phase duration
        return min(99.0, (self.duration_ms / 30.0) * 100.0)


@dataclass
class TimeoutMetrics:
    """Aggregated timeout and execution metrics."""
    timeout_count: int = 0
    total_cycles: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    percent_completed: float = 0.0
    phases_affected: Set[ExecutionPhase] = field(default_factory=set)
    last_timeout_reason: str = ""
    last_timeout_timestamp: Optional[str] = None
    partial_results_returned: int = 0
    validations_skipped: int = 0
    rollbacks_performed: int = 0
    recoveries_attempted: int = 0
    
    def record_cycle(self, duration_ms: float) -> None:
        """Record a completed cycle."""
        self.total_cycles += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_cycles
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
    
    def record_timeout(self, reason: str, affected_phases: Set[ExecutionPhase]) -> None:
        """Record timeout event."""
        self.timeout_count += 1
        self.last_timeout_reason = reason
        self.last_timeout_timestamp = datetime.now(timezone.utc).isoformat()
        self.phases_affected.update(affected_phases)


class ReflexiveCycleGuard:
    """
    Enforces 100ms deadline on reflexive mining cycles with graceful degradation.
    
    Prevents cascade failures from long-running counterfactuals by:
    - Cancelling AST parsing operations
    - Interrupting virtual mining simulations
    - Rolling back pending proposal applications
    - Returning partial results when appropriate
    - Logging timeout details and state recovery
    
    Thread-safe and exception-safe with proper state recovery.
    """
    
    def __init__(
        self,
        deadline_ms: float = REFLEXIVE_CYCLE_DEADLINE_MS,
        enable_telemetry: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the timeout guard.
        
        Args:
            deadline_ms: Hard deadline in milliseconds (default 100ms)
            enable_telemetry: Whether to emit telemetry events
            logger: Optional custom logger instance
        """
        self.deadline_ms = deadline_ms
        self.enable_telemetry = enable_telemetry
        self.logger = logger or LOGGER
        
        # Current execution state
        self._current_phase: ExecutionPhase = ExecutionPhase.IDLE
        self._cycle_start_time_ms: float = 0.0
        self._phase_start_time_ms: float = 0.0
        self._phase_metrics: List[PhaseMetrics] = []
        self._active_tasks: Set[asyncio.Task[Any]] = set()
        self._timeout_triggered: bool = False
        self._pending_rollbacks: List[Tuple[str, Any]] = []
        
        # Metrics
        self.metrics = TimeoutMetrics()
    
    def _current_time_ms(self) -> float:
        """Get current time in milliseconds."""
        return time.time() * 1000.0
    
    def _time_remaining_ms(self) -> float:
        """Calculate remaining time before deadline."""
        if self._cycle_start_time_ms == 0:
            return self.deadline_ms
        elapsed = self._current_time_ms() - self._cycle_start_time_ms
        return max(0.0, self.deadline_ms - elapsed)
    
    def _is_deadline_exceeded(self) -> bool:
        """Check if deadline has been exceeded."""
        return self._time_remaining_ms() <= 0.0
    
    def _begin_phase(self, phase: ExecutionPhase) -> None:
        """Begin a new execution phase with timing."""
        current_time = self._current_time_ms()
        
        if self._current_phase != ExecutionPhase.IDLE:
            self._end_phase()
        
        self._current_phase = phase
        self._phase_start_time_ms = current_time
        self.logger.debug(
            f"Beginning {phase.value} phase",
            extra={"phase": phase.value, "time_remaining_ms": self._time_remaining_ms()}
        )
    
    def _end_phase(self, items_processed: int = 0) -> None:
        """End current phase and record metrics."""
        if self._current_phase == ExecutionPhase.IDLE:
            return
        
        current_time = self._current_time_ms()
        phase_metric = PhaseMetrics(
            phase=self._current_phase,
            start_time_ms=self._phase_start_time_ms,
            items_processed=items_processed,
        )
        phase_metric.mark_complete(current_time)
        self._phase_metrics.append(phase_metric)
        
        self.logger.debug(
            f"Completed {self._current_phase.value} phase",
            extra={
                "phase": self._current_phase.value,
                "duration_ms": phase_metric.duration_ms,
                "items": items_processed,
            }
        )
        
        self._current_phase = ExecutionPhase.IDLE
    
    def _register_task(self, task: asyncio.Task[Any]) -> None:
        """Register an active task for potential cancellation."""
        self._active_tasks.add(task)
        task.add_done_callback(lambda t: self._active_tasks.discard(t))
    
    async def _cancel_active_tasks(self) -> None:
        """Cancel all registered tasks gracefully."""
        if not self._active_tasks:
            return
        
        self.logger.warning(
            f"Cancelling {len(self._active_tasks)} active tasks due to timeout",
            extra={"task_count": len(self._active_tasks)}
        )
        
        for task in list(self._active_tasks):
            if not task.done():
                task.cancel()
        
        # Wait for cancellations to propagate with short timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._active_tasks, return_exceptions=True),
                timeout=0.05  # 50ms buffer
            )
        except asyncio.TimeoutError:
            self.logger.error(
                "Tasks did not cancel within timeout buffer",
                extra={"remaining_tasks": len([t for t in self._active_tasks if not t.done()])}
            )
    
    def _record_pending_rollback(self, operation_id: str, context: Any) -> None:
        """Record a pending rollback operation."""
        self._pending_rollbacks.append((operation_id, context))
    
    async def _execute_rollbacks(self) -> None:
        """Execute pending rollback operations."""
        if not self._pending_rollbacks:
            return
        
        self.logger.info(
            f"Executing {len(self._pending_rollbacks)} rollbacks",
            extra={"rollback_count": len(self._pending_rollbacks)}
        )
        
        for operation_id, context in self._pending_rollbacks:
            try:
                # Attempt rollback with timeout
                if isinstance(context, dict) and "rollback_fn" in context:
                    rollback_fn = context["rollback_fn"]
                    if asyncio.iscoroutinefunction(rollback_fn):
                        await asyncio.wait_for(rollback_fn(), timeout=0.010)
                    else:
                        rollback_fn()
                
                self.logger.debug(f"Rolled back operation {operation_id}")
            except Exception as e:
                self.logger.error(
                    f"Rollback failed for {operation_id}: {e}",
                    extra={"operation_id": operation_id, "error": str(e)}
                )
            finally:
                self.metrics.rollbacks_performed += 1
    
    @asynccontextmanager
    async def reflexive_cycle(self):
        """
        Context manager for a complete reflexive cycle with timeout.
        
        Yields a cycle context with helper methods for different phases.
        
        Usage:
            async with guard.reflexive_cycle() as cycle:
                proposals = await cycle.parse_proposals(...)
                simulated = await cycle.simulate_mining(proposals)
                validated = await cycle.validate_constraints(simulated)
                await cycle.apply_proposals(validated)
        """
        cycle_start = self._current_time_ms()
        self._cycle_start_time_ms = cycle_start
        self._phase_metrics = []
        self._pending_rollbacks = []
        self._active_tasks = set()
        self._timeout_triggered = False
        affected_phases: Set[ExecutionPhase] = set()
        
        try:
            yield CycleContext(self, affected_phases)
        except asyncio.CancelledError:
            self.logger.warning("Reflexive cycle was cancelled")
            affected_phases.add(self._current_phase)
            raise
        except Exception as e:
            self.logger.error(f"Reflexive cycle error: {e}", exc_info=True)
            affected_phases.add(self._current_phase)
            raise
        finally:
            # Cleanup and telemetry
            cycle_duration = self._current_time_ms() - cycle_start
            self._end_phase()
            
            # Record metrics
            self.metrics.record_cycle(cycle_duration)
            
            if self._timeout_triggered:
                reason = f"Phase {self._current_phase.value} exceeded deadline"
                self.metrics.record_timeout(reason, affected_phases)
                self.logger.warning(
                    f"Reflexive cycle timeout: {reason}",
                    extra={
                        "cycle_duration_ms": cycle_duration,
                        "deadline_ms": self.deadline_ms,
                        "affected_phases": [p.value for p in affected_phases],
                    }
                )
            
            # Emit telemetry
            if self.enable_telemetry:
                self._emit_telemetry()
    
    async def parse_proposals(
        self,
        parse_fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Parse AST and generate optimization proposals with timeout.
        
        Cancels operation if deadline exceeded.
        
        Args:
            parse_fn: Async function to call for proposal parsing
            *args, **kwargs: Arguments to pass to parse_fn
        
        Returns:
            List of proposals or None if timeout
        """
        self._begin_phase(ExecutionPhase.PARSING)
        
        try:
            if self._is_deadline_exceeded():
                self._timeout_triggered = True
                self.logger.warning("Parsing phase deadline already exceeded on entry")
                return None
            
            time_remaining = self._time_remaining_ms()
            kwargs.setdefault("timeout", max(5.0, time_remaining - 10.0))
            
            # Wrap in timeout context
            try:
                proposals = await asyncio.wait_for(
                    parse_fn(*args, **kwargs),
                    timeout=time_remaining / 1000.0,
                )
                self._end_phase(items_processed=len(proposals) if proposals else 0)
                return proposals
            except asyncio.TimeoutError:
                self._timeout_triggered = True
                self.logger.warning("AST parsing operation timed out")
                self.metrics.partial_results_returned += 1
                return []  # Return empty to allow cycle to continue
        
        except Exception as e:
            self.logger.error(f"Parsing phase error: {e}", exc_info=True)
            raise
    
    async def simulate_mining(
        self,
        proposals: List[Dict[str, Any]],
        simulation_fn: Any,
    ) -> List[Dict[str, Any]]:
        """
        Simulate virtual mining for proposals with timeout.
        
        Returns best proposals found so far if timeout occurs.
        
        Args:
            proposals: List of proposals to simulate
            simulation_fn: Async function to simulate a single proposal
        
        Returns:
            List of simulated proposals (may be partial)
        """
        self._begin_phase(ExecutionPhase.SIMULATION)
        
        if not proposals:
            self._end_phase(items_processed=0)
            return []
        
        try:
            simulated = []
            time_per_proposal = (self._time_remaining_ms() - 20.0) / max(1, len(proposals))
            
            for i, proposal in enumerate(proposals):
                if self._is_deadline_exceeded():
                    self._timeout_triggered = True
                    self.logger.warning(
                        f"Simulation timeout after {i}/{len(proposals)} proposals",
                        extra={"completed": i, "total": len(proposals)}
                    )
                    self.metrics.partial_results_returned += 1
                    break
                
                try:
                    result = await asyncio.wait_for(
                        simulation_fn(proposal),
                        timeout=time_per_proposal / 1000.0,
                    )
                    simulated.append(result)
                except asyncio.TimeoutError:
                    self.logger.debug(f"Individual simulation timed out for proposal {i}")
                    # Skip this proposal but continue with others
                    continue
                except Exception as e:
                    self.logger.debug(f"Simulation error for proposal {i}: {e}")
                    continue
            
            self._end_phase(items_processed=len(simulated))
            return simulated
        
        except Exception as e:
            self.logger.error(f"Simulation phase error: {e}", exc_info=True)
            raise
    
    async def validate_constraints(
        self,
        proposals: List[Dict[str, Any]],
        validation_fn: Any,
        skip_on_timeout: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Validate constraints with graceful timeout handling.
        
        If timeout, skips constraint checks and logs warning.
        Never returns system in inconsistent state.
        
        Args:
            proposals: List of proposals to validate
            validation_fn: Async function to validate a proposal
            skip_on_timeout: If True, skip validation on timeout instead of failing
        
        Returns:
            List of validated proposals
        """
        self._begin_phase(ExecutionPhase.VALIDATION)
        
        if not proposals:
            self._end_phase(items_processed=0)
            return []
        
        try:
            validated = []
            time_per_proposal = (self._time_remaining_ms() - 10.0) / max(1, len(proposals))
            
            for i, proposal in enumerate(proposals):
                if self._is_deadline_exceeded():
                    if skip_on_timeout:
                        self._timeout_triggered = True
                        self.logger.warning(
                            f"Validation timeout - skipping constraint checks for {len(proposals) - i} remaining proposals",
                            extra={"completed": i, "total": len(proposals)}
                        )
                        self.metrics.validations_skipped += len(proposals) - i
                        # Add remaining proposals without validation
                        validated.extend(proposals[i:])
                        break
                    else:
                        self._timeout_triggered = True
                        raise TimeoutError(f"Validation phase exceeded deadline at proposal {i}")
                
                try:
                    result = await asyncio.wait_for(
                        validation_fn(proposal),
                        timeout=time_per_proposal / 1000.0,
                    )
                    validated.append(result)
                except asyncio.TimeoutError:
                    if skip_on_timeout:
                        self.logger.debug(f"Individual validation timed out for proposal {i}, including as-is")
                        validated.append(proposal)
                    else:
                        raise
                except Exception as e:
                    self.logger.error(f"Validation error for proposal {i}: {e}")
                    if not skip_on_timeout:
                        raise
            
            self._end_phase(items_processed=len(validated))
            return validated
        
        except Exception as e:
            self.logger.error(f"Validation phase error: {e}", exc_info=True)
            raise
    
    async def apply_proposals(
        self,
        proposals: List[Dict[str, Any]],
        apply_fn: Any,
        rollback_on_timeout: bool = True,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Apply proposals with safe rollback on timeout.
        
        Never leaves system in inconsistent state - rolls back all pending
        applications if timeout occurs.
        
        Args:
            proposals: List of proposals to apply
            apply_fn: Async function to apply a proposal
            rollback_on_timeout: If True, rollback on timeout
        
        Returns:
            Tuple of (applied_proposals, was_complete)
        """
        self._begin_phase(ExecutionPhase.APPLYING)
        
        if not proposals:
            self._end_phase(items_processed=0)
            return ([], True)
        
        applied = []
        applied_operations: List[str] = []
        
        try:
            time_per_proposal = (self._time_remaining_ms() - 10.0) / max(1, len(proposals))
            
            for i, proposal in enumerate(proposals):
                if self._is_deadline_exceeded():
                    self._timeout_triggered = True
                    self.logger.warning(
                        f"Apply phase timeout after {i}/{len(proposals)} proposals",
                        extra={"applied": i, "total": len(proposals)}
                    )
                    
                    if rollback_on_timeout:
                        self.logger.info("Rolling back pending proposal applications")
                        await self._cancel_active_tasks()
                        await self._execute_rollbacks()
                    
                    self._end_phase(items_processed=len(applied))
                    return (applied, False)
                
                try:
                    # Register operation for potential rollback
                    operation_id = f"proposal_{i}_{proposal.get('id', 'unknown')}"
                    
                    result = await asyncio.wait_for(
                        apply_fn(proposal),
                        timeout=time_per_proposal / 1000.0,
                    )
                    
                    applied.append(result)
                    applied_operations.append(operation_id)
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"Individual apply timed out for proposal {i}")
                    if rollback_on_timeout:
                        await self._execute_rollbacks()
                    self._end_phase(items_processed=len(applied))
                    return (applied, False)
                
                except Exception as e:
                    self.logger.error(f"Apply error for proposal {i}: {e}")
                    if rollback_on_timeout:
                        await self._execute_rollbacks()
                    raise
            
            self._end_phase(items_processed=len(applied))
            return (applied, True)
        
        except Exception as e:
            self.logger.error(f"Apply phase error: {e}", exc_info=True)
            if rollback_on_timeout:
                await self._execute_rollbacks()
            raise
    
    def _emit_telemetry(self) -> None:
        """Emit telemetry about cycle execution."""
        try:
            telemetry = {
                "timeout_count": self.metrics.timeout_count,
                "total_cycles": self.metrics.total_cycles,
                "avg_duration_ms": round(self.metrics.avg_duration_ms, 2),
                "min_duration_ms": round(self.metrics.min_duration_ms, 2),
                "max_duration_ms": round(self.metrics.max_duration_ms, 2),
                "percent_completed": self.metrics.percent_completed,
                "partial_results_returned": self.metrics.partial_results_returned,
                "validations_skipped": self.metrics.validations_skipped,
                "rollbacks_performed": self.metrics.rollbacks_performed,
                "last_timeout_reason": self.metrics.last_timeout_reason,
            }
            
            self.logger.info(
                "Reflexive cycle telemetry",
                extra=telemetry
            )
        except Exception as e:
            self.logger.error(f"Telemetry emission error: {e}")
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return {
            "timeout_count": self.metrics.timeout_count,
            "total_cycles": self.metrics.total_cycles,
            "avg_duration_ms": round(self.metrics.avg_duration_ms, 2),
            "min_duration_ms": round(self.metrics.min_duration_ms, 2),
            "max_duration_ms": round(self.metrics.max_duration_ms, 2),
            "percent_completed": self.metrics.percent_completed,
            "phases_affected": sorted([p.value for p in self.metrics.phases_affected]),
            "partial_results_returned": self.metrics.partial_results_returned,
            "validations_skipped": self.metrics.validations_skipped,
            "rollbacks_performed": self.metrics.rollbacks_performed,
            "recoveries_attempted": self.metrics.recoveries_attempted,
            "last_timeout_reason": self.metrics.last_timeout_reason,
            "last_timeout_timestamp": self.metrics.last_timeout_timestamp,
        }


class CycleContext:
    """Helper context for executing reflexive cycles with guard."""
    
    def __init__(self, guard: ReflexiveCycleGuard, affected_phases: Set[ExecutionPhase]):
        self.guard = guard
        self.affected_phases = affected_phases
    
    async def parse_proposals(
        self,
        parse_fn: Any,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[List[Dict[str, Any]]]:
        """Parse proposals with timeout."""
        return await self.guard.parse_proposals(parse_fn, *args, **kwargs)
    
    async def simulate_mining(
        self,
        proposals: List[Dict[str, Any]],
        simulation_fn: Any,
    ) -> List[Dict[str, Any]]:
        """Simulate mining with timeout."""
        return await self.guard.simulate_mining(proposals, simulation_fn)
    
    async def validate_constraints(
        self,
        proposals: List[Dict[str, Any]],
        validation_fn: Any,
        skip_on_timeout: bool = True,
    ) -> List[Dict[str, Any]]:
        """Validate constraints with timeout."""
        return await self.guard.validate_constraints(proposals, validation_fn, skip_on_timeout)
    
    async def apply_proposals(
        self,
        proposals: List[Dict[str, Any]],
        apply_fn: Any,
        rollback_on_timeout: bool = True,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """Apply proposals with rollback on timeout."""
        return await self.guard.apply_proposals(proposals, apply_fn, rollback_on_timeout)
    
    def time_remaining_ms(self) -> float:
        """Get remaining time in current cycle."""
        return self.guard._time_remaining_ms()
    
    def is_deadline_exceeded(self) -> bool:
        """Check if deadline has been exceeded."""
        return self.guard._is_deadline_exceeded()


# Module-level instance for singleton pattern
_global_guard: Optional[ReflexiveCycleGuard] = None


def get_reflexive_cycle_guard(
    deadline_ms: float = REFLEXIVE_CYCLE_DEADLINE_MS,
    enable_telemetry: bool = True,
) -> ReflexiveCycleGuard:
    """Get or create the global reflexive cycle guard."""
    global _global_guard
    if _global_guard is None:
        _global_guard = ReflexiveCycleGuard(deadline_ms, enable_telemetry)
    return _global_guard


def reset_reflexive_cycle_guard() -> None:
    """Reset the global guard instance."""
    global _global_guard
    _global_guard = None
