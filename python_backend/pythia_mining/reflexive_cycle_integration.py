"""Integration guide for ReflexiveCycleGuard with AutonomousMiningController.

This module demonstrates how to integrate the timeout guard into reflexive
mining cycles, replacing or enhancing existing _run_reflexive_cycle implementations.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List, Dict, Any, Optional

from reflexive_cycle_timeout import (
    ReflexiveCycleGuard,
    get_reflexive_cycle_guard,
)

LOGGER = logging.getLogger(__name__)


class ReflexiveCycleIntegration:
    """
    Helper class to integrate ReflexiveCycleGuard with AutonomousMiningController.
    
    Usage in AutonomousMiningController:
        
        # In __init__:
        self.reflexive_guard = ReflexiveCycleGuard(deadline_ms=100.0)
        
        # In _run_reflexive_cycle:
        integration = ReflexiveCycleIntegration(self, self.reflexive_guard)
        proposals = await integration.run_protected_reflexive_cycle()
    """
    
    def __init__(
        self,
        mining_controller: Any,  # AutonomousMiningController
        guard: Optional[ReflexiveCycleGuard] = None,
    ):
        """
        Initialize the integration.
        
        Args:
            mining_controller: Reference to AutonomousMiningController instance
            guard: Optional custom ReflexiveCycleGuard (uses global if None)
        """
        self.controller = mining_controller
        self.guard = guard or get_reflexive_cycle_guard()
        self.logger = logging.getLogger(__name__)
    
    async def run_protected_reflexive_cycle(
        self,
        targets: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a complete reflexive cycle with timeout protection.
        
        This replaces or wraps the AutonomousMiningController._run_reflexive_cycle
        method, adding comprehensive timeout protection and partial result handling.
        
        Args:
            targets: Optional list of reflexive targets to optimize
        
        Returns:
            List of proposals generated (may be partial if timeout)
        
        Example:
            # Replace existing cycle in AutonomousMiningController
            async def _run_reflexive_cycle(self):
                integration = ReflexiveCycleIntegration(self, self.reflexive_guard)
                return await integration.run_protected_reflexive_cycle()
        """
        async with self.guard.reflexive_cycle() as cycle:
            # PARSE PHASE: Generate proposals from code analysis
            proposals = await cycle.parse_proposals(
                self._parse_optimization_proposals,
                targets=targets,
            )
            
            if not proposals:
                self.logger.info("No proposals generated in parse phase")
                return []
            
            # SIMULATION PHASE: Simulate mining impact
            simulated = await cycle.simulate_mining(
                proposals,
                self._simulate_proposal,
            )
            
            if not simulated:
                self.logger.warning("No simulations completed")
                return []
            
            # VALIDATION PHASE: Check constraints (gracefully skip on timeout)
            validated = await cycle.validate_constraints(
                simulated,
                self._validate_proposal_constraints,
                skip_on_timeout=True,  # Don't fail cycle on validation timeout
            )
            
            if not validated:
                self.logger.warning("No proposals passed validation")
                return []
            
            # APPLY PHASE: Apply accepted proposals with rollback safety
            applied, was_complete = await cycle.apply_proposals(
                validated,
                self._apply_proposal,
                rollback_on_timeout=True,  # Rollback pending changes on timeout
            )
            
            if not was_complete:
                self.logger.warning(
                    f"Reflexive cycle did not complete: "
                    f"{len(applied)}/{len(validated)} proposals applied"
                )
            
            return applied
    
    async def _parse_optimization_proposals(
        self,
        targets: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Parse AST and generate optimization proposals.
        
        This wraps controller's _generate_counterfactual logic with timeout safety.
        
        Args:
            targets: Optional list of optimization targets
        
        Returns:
            List of generated proposals
        """
        try:
            if targets is None:
                targets = self.controller._select_reflexive_targets()
            
            proposals = []
            for target in targets:
                try:
                    proposal = self.controller._generate_counterfactual(target)
                    if proposal:
                        proposals.append(proposal)
                except Exception as e:
                    self.logger.warning(f"Failed to generate proposal for {target}: {e}")
                    continue
            
            return proposals
        
        except Exception as e:
            self.logger.error(f"Error parsing proposals: {e}", exc_info=True)
            raise
    
    async def _simulate_proposal(
        self,
        proposal: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Simulate mining with a proposal.
        
        Args:
            proposal: Proposal to simulate
        
        Returns:
            Proposal with simulated metrics
        """
        try:
            # Use controller's virtual mining simulation
            simulated_phi = self.controller._simulate_virtual_mining(proposal)
            
            return {
                **proposal,
                "simulated_phi": simulated_phi,
                "simulation_status": "completed",
            }
        
        except Exception as e:
            self.logger.warning(f"Simulation failed for proposal: {e}")
            # Return proposal as-is to allow other proposals to be simulated
            return {**proposal, "simulation_status": "failed", "error": str(e)}
    
    async def _validate_proposal_constraints(
        self,
        proposal: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate proposal against constraints.
        
        Args:
            proposal: Proposal to validate
        
        Returns:
            Proposal with validation results
        """
        try:
            # Use controller's constraint validation
            is_valid = self.controller.validate_constraints(proposal)
            
            return {
                **proposal,
                "validation_passed": is_valid,
                "validation_status": "completed",
            }
        
        except Exception as e:
            self.logger.warning(f"Validation failed for proposal: {e}")
            # On validation error, include anyway but mark as unvalidated
            return {
                **proposal,
                "validation_passed": False,
                "validation_status": "error",
                "validation_error": str(e),
            }
    
    async def _apply_proposal(
        self,
        proposal: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply a validated proposal.
        
        Args:
            proposal: Validated proposal to apply
        
        Returns:
            Proposal with application results
        """
        try:
            # Store original state for rollback
            proposal_id = proposal.get("id", "unknown")
            
            # Use controller's apply method
            self.controller.apply_self_optimization(proposal)
            
            return {
                **proposal,
                "applied": True,
                "apply_status": "completed",
            }
        
        except Exception as e:
            self.logger.error(f"Failed to apply proposal: {e}")
            # Don't fail the cycle - return error but allow other proposals to continue
            return {
                **proposal,
                "applied": False,
                "apply_status": "failed",
                "apply_error": str(e),
            }


class ReflexiveCycleMonitor:
    """Monitor and report on reflexive cycle execution."""
    
    def __init__(self, guard: Optional[ReflexiveCycleGuard] = None):
        """
        Initialize monitor.
        
        Args:
            guard: Optional custom ReflexiveCycleGuard
        """
        self.guard = guard or get_reflexive_cycle_guard()
        self.logger = logging.getLogger(__name__)
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get comprehensive health report.
        
        Returns:
            Dictionary with health metrics
        """
        metrics = self.guard.get_metrics_snapshot()
        
        # Calculate derived metrics
        timeout_rate = (
            metrics["timeout_count"] / metrics["total_cycles"]
            if metrics["total_cycles"] > 0
            else 0.0
        )
        
        deadline_ms = self.guard.deadline_ms
        avg_duration = metrics["avg_duration_ms"]
        safety_margin = deadline_ms - avg_duration
        safety_margin_percent = (safety_margin / deadline_ms * 100) if deadline_ms > 0 else 0
        
        return {
            "deadline_ms": deadline_ms,
            "avg_duration_ms": avg_duration,
            "safety_margin_ms": round(safety_margin, 2),
            "safety_margin_percent": round(safety_margin_percent, 1),
            "timeout_rate_percent": round(timeout_rate * 100, 1),
            "health_status": self._assess_health(timeout_rate, safety_margin_percent),
            **metrics,
        }
    
    def _assess_health(self, timeout_rate: float, safety_margin_percent: float) -> str:
        """Assess reflexive cycle health."""
        if timeout_rate > 0.1:
            return "CRITICAL"  # >10% timeout rate
        if timeout_rate > 0.05:
            return "WARNING"  # >5% timeout rate
        if safety_margin_percent < 10:
            return "WARNING"  # <10% safety margin
        return "HEALTHY"
    
    def log_health_report(self) -> None:
        """Log comprehensive health report."""
        report = self.get_health_report()
        self.logger.info(
            f"Reflexive cycle health: {report['health_status']}",
            extra=report
        )


# Example of how to use in AutonomousMiningController
EXAMPLE_INTEGRATION = """
# In AutonomousMiningController class:

class AutonomousMiningController:
    def __init__(self, ...):
        ...
        # Initialize reflexive guard
        self.reflexive_guard = ReflexiveCycleGuard(
            deadline_ms=100.0,
            enable_telemetry=True
        )
        self.reflexive_integration = ReflexiveCycleIntegration(
            self,
            self.reflexive_guard
        )
        self.reflexive_monitor = ReflexiveCycleMonitor(self.reflexive_guard)
        ...
    
    async def _run_reflexive_cycle(self) -> List[SelfOptimizationProposal]:
        '''Run reflexive cycle with timeout protection.'''
        return await self.reflexive_integration.run_protected_reflexive_cycle(
            targets=self._select_reflexive_targets()
        )
    
    async def seek_improvement(self) -> Dict[str, Any]:
        '''Seek improvements with comprehensive monitoring.'''
        try:
            proposals = await self._run_reflexive_cycle()
            
            # Log health report
            self.reflexive_monitor.log_health_report()
            
            return {
                "proposals": proposals,
                "health": self.reflexive_monitor.get_health_report(),
            }
        except Exception as e:
            self.logger.error(f"Reflexive cycle error: {e}", exc_info=True)
            raise
"""
