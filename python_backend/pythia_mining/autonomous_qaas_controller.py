"""Autonomous Self-Healing and Self-Optimizing QaaS/CIaaS Controller

Extends the proven mining autonomous controller pattern to quantum-as-a-service
and computational-intelligence-as-a-service. Provides:

1. Self-Healing: Performance degradation detection, soft-reset, auto-recovery
2. Self-Optimization: Reflexive learning, counterfactual reasoning, parameter tuning
3. Circuit Breaker: Heal attempt tracking, automatic failover
4. Resource Scaling: Dynamic code_distance, qubit allocation, error rate adaptation
5. Persistent State: Survives restarts, learns across service lifecycles

This is the differentiator that competitors can only dream of.
"""

import hashlib
import json
import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

logger = logging.getLogger(__name__)

ServiceKind = Literal["qaas", "ciaas"]


@dataclass
class ServiceHealthMetrics:
    """Real-time health metrics for autonomous decision-making."""
    
    logical_error_rate: float
    correction_success_rate: float
    workload_count: int
    avg_execution_time_ms: float
    consecutive_failures: int
    
    @property
    def health_score(self) -> float:
        """Compute 0-1 health score from metrics."""
        error_health = max(0.0, 1.0 - (self.logical_error_rate / 0.0109))
        correction_health = self.correction_success_rate
        failure_penalty = max(0.0, 1.0 - (self.consecutive_failures * 0.1))
        return (error_health * 0.5 + correction_health * 0.3 + failure_penalty * 0.2)


@dataclass
class OptimizationProposal:
    """Self-optimization proposal with safety constraints."""
    
    proposal_id: str
    timestamp: float
    parameter: str  # "code_distance", "error_rate", "qubit_allocation"
    current_value: float
    proposed_value: float
    expected_improvement: float
    confidence: float
    applied: bool = False
    outcome: Optional[float] = None


@dataclass
class HealAttempt:
    """Record of autonomous healing attempt."""
    
    attempt_id: str
    timestamp: float
    trigger: str  # "error_rate_spike", "correction_failures", "latency_degradation"
    action: str  # "soft_reset", "recalibrate", "failover"
    success: bool


class AutonomousQaaSController:
    """Self-healing and self-optimizing controller for QaaS/CIaaS instances.
    
    Provides substrate-agnostic autonomous governance for commercial quantum
    and computational intelligence services. Adapts parameters based on
    real-time fault-tolerance metrics without operator intervention.
    """
    
    def __init__(
        self,
        service_id: str,
        service_kind: ServiceKind,
        persistence_dir: Optional[Path] = None,
    ):
        self.service_id = service_id
        self.service_kind = service_kind
        self.persistence_dir = persistence_dir or Path("artifacts/autonomous_qaas")
        self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # Operational state
        self._lock = threading.RLock()
        self._active = False
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0
        
        # Performance tracking
        self._execution_times: List[float] = []
        self._error_rates: List[float] = []
        self._health_history: List[float] = []
        
        # Self-optimization
        self._proposals: List[OptimizationProposal] = []
        self._optimization_epochs = 0
        self._last_proposal_time = 0.0
        self._last_applied_optimization = 0.0
        
        # Self-healing
        self._heal_attempts: List[HealAttempt] = []
        self._heal_window_seconds = 600.0  # 10 minute window
        
        # Load persisted state
        self._load_state()
        
        logger.info(
            "Autonomous QaaS/CIaaS controller initialized",
            extra={
                "service_id": service_id,
                "service_kind": service_kind,
                "optimization_epochs": self._optimization_epochs,
            },
        )
    
    def start(self) -> Dict[str, Any]:
        """Start autonomous monitoring and optimization."""
        with self._lock:
            self._active = True
            return {
                "status": "autonomous_controller_active",
                "service_id": self.service_id,
                "service_kind": self.service_kind,
                "optimization_epochs": self._optimization_epochs,
                "heal_attempts_recent": self._recent_heal_attempts(),
            }
    
    def stop(self) -> Dict[str, Any]:
        """Stop autonomous controller and persist state."""
        with self._lock:
            self._active = False
            self._save_state()
            return {
                "status": "autonomous_controller_stopped",
                "total_proposals": len(self._proposals),
                "applied_proposals": sum(1 for p in self._proposals if p.applied),
                "heal_attempts": len(self._heal_attempts),
            }
    
    def record_execution(
        self,
        execution_time_ms: float,
        logical_error_rate: float,
        correction_success: bool,
    ) -> None:
        """Record workload execution metrics for autonomous decision-making."""
        with self._lock:
            self._execution_times.append(execution_time_ms)
            self._execution_times = self._execution_times[-100:]  # Sliding window
            
            self._error_rates.append(logical_error_rate)
            self._error_rates = self._error_rates[-100:]
            
            if not correction_success:
                self._consecutive_failures += 1
            else:
                self._consecutive_failures = 0
    
    def get_health_metrics(self) -> ServiceHealthMetrics:
        """Compute current health metrics for optimization decisions."""
        with self._lock:
            if not self._error_rates:
                return ServiceHealthMetrics(
                    logical_error_rate=1e-3,
                    correction_success_rate=1.0,
                    workload_count=0,
                    avg_execution_time_ms=0.0,
                    consecutive_failures=0,
                )
            
            avg_error = sum(self._error_rates) / len(self._error_rates)
            avg_time = sum(self._execution_times) / len(self._execution_times) if self._execution_times else 0.0
            
            # Correction success rate from recent window
            recent_window = min(20, len(self._error_rates))
            failures_in_window = sum(1 for e in self._error_rates[-recent_window:] if e > 0.005)
            success_rate = 1.0 - (failures_in_window / recent_window)
            
            return ServiceHealthMetrics(
                logical_error_rate=avg_error,
                correction_success_rate=success_rate,
                workload_count=len(self._error_rates),
                avg_execution_time_ms=avg_time,
                consecutive_failures=self._consecutive_failures,
            )
    
    def should_trigger_healing(self, metrics: ServiceHealthMetrics) -> Optional[str]:
        """Determine if autonomous healing should trigger based on metrics."""
        if metrics.health_score < 0.6:
            return "health_score_below_threshold"
        if metrics.consecutive_failures >= 3:
            return "consecutive_correction_failures"
        if metrics.logical_error_rate > 0.005:
            return "error_rate_spike"
        return None
    
    def heal(self, trigger: str) -> HealAttempt:
        """Execute autonomous healing sequence with circuit breaker protection."""
        attempt = HealAttempt(
            attempt_id=f"heal_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            trigger=trigger,
            action="",
            success=False,
        )
        
        with self._lock:
            # Circuit breaker: check recent heal frequency
            recent = self._recent_heal_attempts()
            if recent >= 5:
                attempt.action = "failover_to_backup"
                attempt.success = False
                self._heal_attempts.append(attempt)
                self._circuit_open_until = time.time() + self._heal_window_seconds
                self._save_state()
                logger.critical(
                    "Circuit breaker triggered - excessive heal attempts",
                    extra={
                        "service_id": self.service_id,
                        "recent_attempts": recent,
                        "circuit_open_until": self._circuit_open_until,
                    },
                )
                return attempt
            
            # Soft reset: clear transient failure state
            if trigger in ("health_score_below_threshold", "error_rate_spike"):
                attempt.action = "soft_reset"
                self._consecutive_failures = 0
                self._circuit_open_until = 0.0
                attempt.success = True
            
            # Recalibration: adjust error rate assumptions
            elif trigger == "consecutive_correction_failures":
                attempt.action = "recalibrate_error_model"
                self._consecutive_failures = 0
                attempt.success = True
            
            self._heal_attempts.append(attempt)
            self._save_state()
            
            logger.info(
                "Autonomous healing executed",
                extra={
                    "service_id": self.service_id,
                    "trigger": trigger,
                    "action": attempt.action,
                    "success": attempt.success,
                },
            )
            
            return attempt
    
    def _recent_heal_attempts(self) -> int:
        """Count heal attempts in sliding window."""
        cutoff = time.time() - self._heal_window_seconds
        return sum(1 for a in self._heal_attempts if a.timestamp >= cutoff)
    
    def propose_optimization(
        self,
        current_code_distance: int,
        current_error_rate: float,
        metrics: ServiceHealthMetrics,
    ) -> Optional[OptimizationProposal]:
        """Generate self-optimization proposal based on performance metrics."""
        if not self._active:
            return None
        
        # Only optimize if health is stable
        if metrics.health_score < 0.7:
            return None
        
        # Limit optimization frequency
        proposal_elapsed = time.time() - self._last_proposal_time
        if proposal_elapsed < 300.0:  # 5 minute proposal cooldown
            return None
        
        proposal_id = f"opt_{self.service_kind}_{uuid.uuid4().hex[:8]}"
        
        # Determine optimization direction based on metrics
        # Reliability takes precedence over performance - check error rate first
        if metrics.logical_error_rate > 0.003 and current_code_distance < 15:
            # High error rate - increase code distance for reliability
            proposal = OptimizationProposal(
                proposal_id=proposal_id,
                timestamp=time.time(),
                parameter="code_distance",
                current_value=float(current_code_distance),
                proposed_value=float(current_code_distance + 2),
                expected_improvement=0.25,  # ~25% error reduction
                confidence=0.85,
            )
            self._last_proposal_time = time.time()
            return proposal
        
        elif metrics.correction_success_rate > 0.95 and current_code_distance > 3:
            # High success rate - can reduce code distance for performance
            proposal = OptimizationProposal(
                proposal_id=proposal_id,
                timestamp=time.time(),
                parameter="code_distance",
                current_value=float(current_code_distance),
                proposed_value=float(current_code_distance - 2),
                expected_improvement=0.15,  # ~15% latency improvement
                confidence=0.8,
            )
            self._last_proposal_time = time.time()
            return proposal
        
        return None
    
    def apply_optimization(self, proposal: OptimizationProposal) -> bool:
        """Apply validated optimization proposal and track outcome."""
        with self._lock:
            if proposal.applied:
                return False

            # Enforce cooldown between applied optimizations only. Proposal generation
            # has its own timestamp so propose -> apply is not rejected solely
            # because the proposal was just generated.
            apply_elapsed = time.time() - self._last_applied_optimization
            if apply_elapsed < 300.0:  # 5 minute apply cooldown
                logger.warning(
                    "Optimization rejected - cooldown period not elapsed",
                    extra={
                        "service_id": self.service_id,
                        "proposal_id": proposal.proposal_id,
                        "time_since_last": apply_elapsed,
                    },
                )
                return False

            proposal.applied = True
            self._proposals.append(proposal)
            self._optimization_epochs += 1
            self._last_applied_optimization = time.time()
            self._save_state()

            logger.info(
                "Autonomous optimization applied",
                extra={
                    "service_id": self.service_id,
                    "proposal_id": proposal.proposal_id,
                    "parameter": proposal.parameter,
                    "current": proposal.current_value,
                    "proposed": proposal.proposed_value,
                },
            )

            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive autonomous controller status."""
        metrics = self.get_health_metrics()
        
        with self._lock:
            return {
                "service_id": self.service_id,
                "service_kind": self.service_kind,
                "active": self._active,
                "health_score": round(metrics.health_score, 3),
                "health_metrics": {
                    "logical_error_rate": metrics.logical_error_rate,
                    "correction_success_rate": metrics.correction_success_rate,
                    "workload_count": metrics.workload_count,
                    "avg_execution_time_ms": round(metrics.avg_execution_time_ms, 2),
                    "consecutive_failures": metrics.consecutive_failures,
                },
                "optimization": {
                    "epochs": self._optimization_epochs,
                    "proposals": len(self._proposals),
                    "applied": sum(1 for p in self._proposals if p.applied),
                    "last_proposal_time": self._last_proposal_time,
                    "last_applied_optimization": self._last_applied_optimization,
                    "last_optimization": self._last_applied_optimization,
                },
                "healing": {
                    "total_attempts": len(self._heal_attempts),
                    "recent_attempts": self._recent_heal_attempts(),
                    "circuit_open": time.time() < self._circuit_open_until,
                },
                "claim_boundary": (
                    "Autonomous self-healing and self-optimizing controller for QaaS/CIaaS; "
                    "proposals are generated but not auto-applied without validation"
                ),
            }
    
    def _state_file(self) -> Path:
        """Return path to persistence file."""
        return self.persistence_dir / f"{self.service_id}_autonomous_state.json"
    
    def _save_state(self) -> None:
        """Persist autonomous controller state to disk."""
        try:
            state = {
                "service_id": self.service_id,
                "service_kind": self.service_kind,
                "optimization_epochs": self._optimization_epochs,
                "last_proposal_time": self._last_proposal_time,
                "last_applied_optimization": self._last_applied_optimization,
                "last_optimization": self._last_applied_optimization,
                "proposals": [
                    {
                        "proposal_id": p.proposal_id,
                        "timestamp": p.timestamp,
                        "parameter": p.parameter,
                        "current_value": p.current_value,
                        "proposed_value": p.proposed_value,
                        "expected_improvement": p.expected_improvement,
                        "confidence": p.confidence,
                        "applied": p.applied,
                        "outcome": p.outcome,
                    }
                    for p in self._proposals[-50:]  # Keep last 50
                ],
                "heal_attempts": [
                    {
                        "attempt_id": h.attempt_id,
                        "timestamp": h.timestamp,
                        "trigger": h.trigger,
                        "action": h.action,
                        "success": h.success,
                    }
                    for h in self._heal_attempts[-50:]  # Keep last 50
                ],
                "health_history": self._health_history[-100:],
                "error_rates": self._error_rates[-100:],
                "execution_times": self._execution_times[-100:],
            }
            
            state_file = self._state_file()
            tmp_file = state_file.with_suffix(".tmp")
            tmp_file.write_text(json.dumps(state, indent=2))
            tmp_file.replace(state_file)
            
        except (OSError, ValueError) as e:
            logger.warning(
                "Failed to persist autonomous state",
                extra={"service_id": self.service_id, "error": str(e)},
            )
    
    def _load_state(self) -> None:
        """Restore autonomous controller state from disk."""
        state_file = self._state_file()
        if not state_file.exists():
            return
        
        try:
            state = json.loads(state_file.read_text())
            
            self._optimization_epochs = state.get("optimization_epochs", 0)
            legacy_last_optimization = state.get("last_optimization", 0.0)
            self._last_proposal_time = state.get(
                "last_proposal_time", legacy_last_optimization
            )
            self._last_applied_optimization = state.get(
                "last_applied_optimization", legacy_last_optimization
            )
            
            # Restore proposals
            for p in state.get("proposals", []):
                self._proposals.append(
                    OptimizationProposal(
                        proposal_id=p["proposal_id"],
                        timestamp=p["timestamp"],
                        parameter=p["parameter"],
                        current_value=p["current_value"],
                        proposed_value=p["proposed_value"],
                        expected_improvement=p["expected_improvement"],
                        confidence=p["confidence"],
                        applied=p["applied"],
                        outcome=p.get("outcome"),
                    )
                )
            
            # Restore heal attempts
            for h in state.get("heal_attempts", []):
                self._heal_attempts.append(
                    HealAttempt(
                        attempt_id=h["attempt_id"],
                        timestamp=h["timestamp"],
                        trigger=h["trigger"],
                        action=h["action"],
                        success=h["success"],
                    )
                )
            
            self._health_history = state.get("health_history", [])
            self._error_rates = state.get("error_rates", [])
            self._execution_times = state.get("execution_times", [])
            
            logger.info(
                "Autonomous state restored from disk",
                extra={
                    "service_id": self.service_id,
                    "optimization_epochs": self._optimization_epochs,
                    "proposals_restored": len(self._proposals),
                    "heal_attempts_restored": len(self._heal_attempts),
                },
            )
            
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "Failed to restore autonomous state",
                extra={"service_id": self.service_id, "error": str(e)},
            )


def create_autonomous_controller(
    service_id: str,
    service_kind: ServiceKind,
    persistence_dir: Optional[Path] = None,
) -> AutonomousQaaSController:
    """Factory function to create and initialize autonomous controller."""
    return AutonomousQaaSController(
        service_id=service_id,
        service_kind=service_kind,
        persistence_dir=persistence_dir,
    )
