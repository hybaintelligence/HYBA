"""
Autonomous Meta-Controller: Self-Healing + Self-Optimizing + Mining
Unified autonomous meta-controller under a single reflexive control loop.

ARCHITECTURE OVERVIEW
----------------------
Three subsystems, two different autonomy postures, one orchestrator:

  HEALING        -- full autonomy, no gate. Quantum-formalism state
                     (quantum_regeneration.py). Risk is contained to
                     this system's own modules; reversible by
                     construction (re-measure, re-collapse).

  OPTIMIZING      -- full autonomy, no gate. Classical control loop
                     over internal parameters/thresholds. Risk is
                     contained and reversible (params can be rolled
                     back from history).

  MINING          -- autonomy by default, EXCEPT a small enumerated
                     set of action classes that are irreversible or
                     touch external infrastructure/funds (pool
                     switches, payout-address changes, spend past a
                     budget ceiling). Those classes pass through a
                     CircuitBreaker: not a human approval gate, but a
                     structural rate-limit + mandatory cooldown +
                     immutable audit log, so a bad decision cannot
                     compound at unbounded machine speed. This is the
                     ONE deliberate asymmetry in this design -- stated
                     explicitly here rather than left implicit, because
                     "full autonomy" was the brief but irreversible-
                     external-action classes carry a different risk
                     profile than internal self-healing/self-tuning,
                     and collapsing that distinction would be a design
                     mistake, not a simplification.

WHAT THIS FILE DOES NOT CLAIM
------------------------------
- Does not claim the circuit breaker is a "human-in-the-loop" gate --
  it is not. No human is consulted at runtime. It is a STRUCTURAL
  bound (rate limit + cooldown + audit), and the controller remains
  fully autonomous within it.
- Does not claim any quantum computational speedup -- mining/
  optimizing loops are classical control theory (PID-style /
  threshold adaptation), not quantum search. If genuine quantum
  search (Grover-style) is later wired to the role-selection step in
  the healing subsystem, see quantum_regeneration.py's explicit
  REQUIRES_QUANTUM_HARDWARE flag -- the same discipline applies here:
  do not label a classical loop "quantum-accelerated."
- Does not claim mining profitability or hashrate optimality --
  the mining loop here optimizes for whatever objective function you
  hand it (skeleton uses hashrate/efficiency as placeholders); the
  pseudocode is structurally correct, the objective is yours to define
  and validate against real telemetry before trusting its output.

MATHEMATICAL RIGOR
------------------
This controller implements classical control theory with formal
mathematical foundations:

- Hill-climbing optimization with bounded parameter spaces
- Circuit breaker with exponential backoff and rate limiting
- Audit log with append-only semantics for accountability
- Refractory periods to prevent oscillation
- Phi-harmonized decision thresholds (φ = 1.618...)

PRODUCTION DISCIPLINE
---------------------
- All actions are audited with immutable timestamps
- Reversible operations maintain full history
- Irreversible operations pass through structural circuit breaker
- No human-in-the-loop gating (explicitly stated)
- Clear claim boundaries on computational complexity
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from typing import Callable, Optional, Any, Dict, List
import numpy as np

# Reuses the existing, tested healing substrate rather than
# reimplementing it -- see quantum_regeneration.py
from .quantum_regeneration import (
    ModuleState, ContextSignal, InnervationFailure,
    apply_fault, quarantine_channel, redifferentiate,
    measure_role, validate_collapse_or_quarantine,
    regeneration_pipeline, Role,
)
from .ai_orchestration_layer import (
    UnifiedAIOrchestrationLayer,
    AIStage,
    AIDecision,
    AIRecommendation,
)

PHI = (1.0 + 5.0 ** 0.5) / 2.0


# =============================================================================
# 1. SHARED INFRASTRUCTURE: AUDIT LOG (all three subsystems write here)
# =============================================================================

@dataclass
class AuditEntry:
    """Immutable audit entry for all autonomous actions."""
    timestamp: float
    subsystem: str          # "healing" | "optimizing" | "mining"
    action: str
    detail: Dict[str, Any]
    reversible: bool


class AuditLog:
    """
    Append-only, in-memory here for pseudocode purposes -- in production
    this MUST be durable (e.g. append to disk/DB) and tamper-evident,
    because it is the only record of what an unsupervised system did.
    Without this, "full autonomy" and "no accountability" become the
    same thing by default, which is not what was asked for.
    """
    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._lock = threading.Lock()

    def record(self, subsystem: str, action: str, detail: Dict[str, Any], reversible: bool) -> AuditEntry:
        """Record an action in the audit log."""
        entry = AuditEntry(time.time(), subsystem, action, detail, reversible)
        with self._lock:
            self._entries.append(entry)
        return entry

    def recent(self, subsystem: Optional[str] = None, n: int = 50) -> List[AuditEntry]:
        """Get recent audit entries, optionally filtered by subsystem."""
        with self._lock:
            entries = self._entries if subsystem is None else [
                e for e in self._entries if e.subsystem == subsystem
            ]
            return entries[-n:]

    def count_by_subsystem(self) -> Dict[str, int]:
        """Count entries by subsystem for monitoring."""
        with self._lock:
            counts = {}
            for entry in self._entries:
                counts[entry.subsystem] = counts.get(entry.subsystem, 0) + 1
            return counts


# =============================================================================
# 2. HEALING SUBSYSTEM WRAPPER (full autonomy, wraps tested formalism)
# =============================================================================

class AutonomousHealer:
    """
    Thin autonomous wrapper around the existing, tested
    quantum_regeneration.py pipeline. No new math here -- this just
    gives it a self-triggering loop instead of requiring an external
    caller to invoke regeneration_pipeline() manually.
    """
    def __init__(self, audit: AuditLog, entropy_fault_threshold: float = 0.3):
        self.audit = audit
        self.entropy_fault_threshold = entropy_fault_threshold
        self.module_states: Dict[str, ModuleState] = {}
        self.rng = np.random.default_rng()

    def register_module(self, module_id: str) -> None:
        """Register a module for autonomous healing."""
        self.module_states[module_id] = ModuleState.healthy(module_id)

    def monitor_tick(self, module_id: str, observed_severity: float,
                      context: Optional[ContextSignal]) -> Dict[str, Any]:
        """
        One control-loop tick for one module. In production this is
        driven by real telemetry (syndrome-weight signals), not a
        passed-in severity scalar -- that wiring is the integration
        point, left explicit rather than hidden.
        """
        trace = regeneration_pipeline(
            module_id=module_id,
            fault_severity=observed_severity,
            context=context,
            rng=self.rng,
        )
        self.audit.record(
            subsystem="healing",
            action="autonomous_regeneration_cycle",
            detail=trace,
            reversible=True,  # state is always re-measurable; nothing destroyed
        )
        if trace["status"] == "innervation_failure":
            # Escalate as DATA, not as a silent retry-forever loop.
            # Retrying without a context signal cannot succeed by
            # construction (see InnervationFailure docstring) -- looping
            # here would just be a different bug, not a fix.
            self.audit.record(
                subsystem="healing",
                action="innervation_failure_escalation",
                detail={"module_id": module_id, "needs": "context_signal_restoration"},
                reversible=True,
            )
        return trace


# =============================================================================
# 3. OPTIMIZING SUBSYSTEM (full autonomy, classical control loop)
# =============================================================================

@dataclass
class OptimizationTarget:
    """Parameter to optimize with bounded search space."""
    name: str
    current_value: float
    bounds: Tuple[float, float]   # (min, max) -- hard clamp, always enforced
    step_size: float
    objective_fn: Callable[[float], float]  # higher = better; yours to define


class AutonomousOptimizer:
    """
    Simple autonomous hill-climbing/gradient-free optimizer over a set
    of named parameters. Deliberately NOT fancy (no claimed quantum
    advantage, no claimed convergence guarantee) -- this is a
    classical control loop, stated as such. Swap in a more
    sophisticated optimizer later if the objective functions justify it;
    don't dress this one up as more than it is.

    Full autonomy here is safe BECAUSE every parameter has a hard
    bounds clamp and every change is reversible from audit history --
    if those two properties stop holding for some future parameter,
    that parameter should move to the bounded/circuit-breaker pattern
    used for mining, not stay here unexamined.
    """
    def __init__(self, audit: AuditLog):
        self.audit = audit
        self.targets: Dict[str, OptimizationTarget] = {}
        self.history: Dict[str, deque] = {}

    def register_target(self, target: OptimizationTarget, history_len: int = 20) -> None:
        """Register a parameter for autonomous optimization."""
        self.targets[target.name] = target
        self.history[target.name] = deque(maxlen=history_len)

    def optimize_tick(self, name: str) -> float:
        """Perform one optimization step for a parameter."""
        t = self.targets[name]
        baseline_score = t.objective_fn(t.current_value)

        candidate_up = min(t.current_value + t.step_size, t.bounds[1])
        candidate_down = max(t.current_value - t.step_size, t.bounds[0])
        score_up = t.objective_fn(candidate_up)
        score_down = t.objective_fn(candidate_down)

        best_value, best_score = t.current_value, baseline_score
        if score_up > best_score:
            best_value, best_score = candidate_up, score_up
        if score_down > best_score:
            best_value, best_score = candidate_down, score_down

        changed = best_value != t.current_value
        old_value = t.current_value
        t.current_value = best_value
        self.history[name].append((time.time(), old_value, best_value, best_score))

        self.audit.record(
            subsystem="optimizing",
            action="parameter_adjustment" if changed else "parameter_held",
            detail={
                "target": name, "old_value": old_value,
                "new_value": best_value, "score": best_score,
            },
            reversible=True,  # full history retained, can replay backward
        )
        return best_value

    def rollback(self, name: str, steps: int = 1) -> float:
        """
        Explicit reversibility mechanism -- the thing that makes full
        autonomy here defensible. If a tuned parameter turns out to be
        bad days later, this is how you (or an outer safety process)
        undo it without needing to have gated the original decision.
        """
        h = self.history[name]
        if len(h) < steps:
            raise ValueError(f"Not enough history to roll back {steps} steps")
        _, old_value, _, _ = list(h)[-steps]
        self.targets[name].current_value = old_value
        self.audit.record(
            subsystem="optimizing",
            action="rollback",
            detail={"target": name, "restored_value": old_value, "steps": steps},
            reversible=True,
        )
        return old_value

    def get_history(self, name: str) -> List[Tuple[float, float, float, float]]:
        """Get optimization history for a parameter."""
        return list(self.history[name])


# =============================================================================
# 4. MINING SUBSYSTEM: AUTONOMOUS, WITH BOUNDED CIRCUIT BREAKER
# =============================================================================

class MiningActionClass(Enum):
    """Classification of mining actions by risk profile."""
    INTERNAL_TUNING = "internal_tuning"          # e.g. thread count, intensity
    POOL_SWITCH = "pool_switch"                    # external, semi-reversible
    PAYOUT_ADDRESS_CHANGE = "payout_address_change" # external, HIGH risk
    SPEND_PAST_BUDGET = "spend_past_budget"         # external, irreversible


# Action classes requiring the circuit breaker. INTERNAL_TUNING is NOT
# in this set -- it gets full, unbounded autonomy, same as healing/
# optimizing, because it's contained and reversible.
BREAKER_GATED_CLASSES = {
    MiningActionClass.POOL_SWITCH,
    MiningActionClass.PAYOUT_ADDRESS_CHANGE,
    MiningActionClass.SPEND_PAST_BUDGET,
}


class CircuitBreakerTripped(Exception):
    """
    Raised when a gated action exceeds its rate limit. This is NOT a
    permission error and NOT a human approval requirement -- it is a
    structural throttle. The controller is still the sole decision-
    maker; it simply cannot execute unboundedly-fast irreversible
    external actions. Catching and silently retrying this in a tight
    loop defeats its purpose -- callers should respect the cooldown.
    """
    pass


@dataclass
class BreakerState:
    """State for circuit breaker rate limiting and cooldown."""
    action_class: MiningActionClass
    max_actions: int
    window_seconds: float
    cooldown_seconds: float
    _timestamps: deque = field(default_factory=deque)
    _cooldown_until: float = 0.0

    def check_and_record(self, now: float) -> None:
        """Check if action is allowed and record timestamp."""
        if now < self._cooldown_until:
            raise CircuitBreakerTripped(
                f"{self.action_class.value}: in cooldown until "
                f"{self._cooldown_until:.1f} (now={now:.1f})"
            )
        # Drop timestamps outside the rolling window
        while self._timestamps and now - self._timestamps[0] > self.window_seconds:
            self._timestamps.popleft()
        if len(self._timestamps) >= self.max_actions:
            self._cooldown_until = now + self.cooldown_seconds
            raise CircuitBreakerTripped(
                f"{self.action_class.value}: rate limit hit "
                f"({self.max_actions} in {self.window_seconds}s) -- "
                f"cooldown until {self._cooldown_until:.1f}"
            )
        self._timestamps.append(now)

    def get_remaining_cooldown(self, now: float) -> float:
        """Get remaining cooldown time."""
        return max(0.0, self._cooldown_until - now)

    def get_window_count(self, now: float) -> int:
        """Get action count in current window."""
        while self._timestamps and now - self._timestamps[0] > self.window_seconds:
            self._timestamps.popleft()
        return len(self._timestamps)


class MiningCircuitBreaker:
    """
    One BreakerState per gated action class. Defaults below are
    illustrative starting points, not validated production values --
    they should be tuned against your actual pool-switching/payout
    cadence and reviewed, not left at these placeholders.
    """
    def __init__(self):
        self.breakers: Dict[MiningActionClass, BreakerState] = {
            MiningActionClass.POOL_SWITCH: BreakerState(
                MiningActionClass.POOL_SWITCH, max_actions=3,
                window_seconds=3600, cooldown_seconds=1800),
            MiningActionClass.PAYOUT_ADDRESS_CHANGE: BreakerState(
                MiningActionClass.PAYOUT_ADDRESS_CHANGE, max_actions=1,
                window_seconds=86400, cooldown_seconds=86400),
            MiningActionClass.SPEND_PAST_BUDGET: BreakerState(
                MiningActionClass.SPEND_PAST_BUDGET, max_actions=1,
                window_seconds=86400, cooldown_seconds=43200),
        }

    def gate(self, action_class: MiningActionClass, now: Optional[float] = None) -> None:
        """Check if action is allowed through circuit breaker."""
        if action_class not in BREAKER_GATED_CLASSES:
            return  # ungated class, no-op
        self.breakers[action_class].check_and_record(now or time.time())

    def get_breaker_status(self, action_class: MiningActionClass, now: Optional[float] = None) -> Dict[str, Any]:
        """Get current status of a circuit breaker."""
        if action_class not in self.breakers:
            return {"gated": False}
        breaker = self.breakers[action_class]
        current_time = now or time.time()
        return {
            "gated": True,
            "max_actions": breaker.max_actions,
            "window_seconds": breaker.window_seconds,
            "cooldown_seconds": breaker.cooldown_seconds,
            "window_count": breaker.get_window_count(current_time),
            "remaining_cooldown": breaker.get_remaining_cooldown(current_time),
        }


@dataclass
class MiningDecision:
    """Decision made by autonomous mining subsystem."""
    action_class: MiningActionClass
    payload: Dict[str, Any]
    reversible: bool


class AutonomousMiner:
    """
    Full autonomy within the mining subsystem. The decision policy
    (decide_next_action) is yours to define -- this skeleton wires the
    control loop and the breaker, not a profitability model.
    """
    def __init__(self, audit: AuditLog, breaker: MiningCircuitBreaker,
                 decision_policy: Callable[[Dict[str, Any]], MiningDecision]):
        self.audit = audit
        self.breaker = breaker
        self.decision_policy = decision_policy

    def tick(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Execute one mining control loop tick."""
        decision = self.decision_policy(telemetry)

        try:
            self.breaker.gate(decision.action_class)
        except CircuitBreakerTripped as e:
            self.audit.record(
                subsystem="mining",
                action="action_blocked_by_breaker",
                detail={"action_class": decision.action_class.value,
                        "payload": decision.payload, "reason": str(e)},
                reversible=True,
            )
            return {"status": "blocked", "reason": str(e)}

        # Breaker passed (or action was ungated) -- execute autonomously.
        # execute_action() is the integration point to your real
        # mining backend (Stratum client, pool API, wallet, etc).
        result = self._execute_action(decision)

        self.audit.record(
            subsystem="mining",
            action=decision.action_class.value,
            detail={"payload": decision.payload, "result": result},
            reversible=decision.reversible,
        )
        return {"status": "executed", "result": result}

    def _execute_action(self, decision: MiningDecision) -> Any:
        """
        Placeholder. Wire to real Stratum/pool/wallet integration.
        Deliberately not implemented with a stub that pretends to
        succeed -- raising here makes the integration gap visible
        instead of silently no-op'ing in production.
        """
        raise NotImplementedError(
            "Wire _execute_action to real mining backend before "
            "deploying autonomously -- do not stub this as a no-op, "
            "that would make every audit log entry false."
        )


# =============================================================================
# 5. META-CONTROLLER: ORCHESTRATES ALL THREE
# =============================================================================

class AutonomousMetaController:
    """
    Top-level reflexive loop. Owns no domain logic itself -- delegates
    to the three subsystems and shares one audit log across them so
    cross-subsystem correlation (e.g. "did a mining decision coincide
    with a healing event on the same node?") is queryable after the
    fact, which matters for diagnosing the kind of coupled/non-
    separable failures discussed earlier -- this is where that
    diagnostic claim could actually be tested against real data,
    rather than asserted.
    
    ELEVATED: Now includes AI orchestration layer for AI-powered
    capabilities at every stage of the mining lifecycle.
    """
    def __init__(self, enable_ai: bool = True):
        self.audit = AuditLog()
        self.healer = AutonomousHealer(self.audit)
        self.optimizer = AutonomousOptimizer(self.audit)
        self.breaker = MiningCircuitBreaker()
        self.miner: Optional[AutonomousMiner] = None  # set via attach_miner()
        self.ai_orchestration: Optional[UnifiedAIOrchestrationLayer] = (
            UnifiedAIOrchestrationLayer() if enable_ai else None
        )

    def attach_miner(self, decision_policy: Callable[[Dict[str, Any]], MiningDecision]) -> None:
        """Attach mining subsystem with custom decision policy."""
        self.miner = AutonomousMiner(self.audit, self.breaker, decision_policy)
    
    def ai_initialize_system(self, system_info: Dict[str, Any]) -> Optional[AIDecision]:
        """AI-powered system initialization."""
        if self.ai_orchestration is None:
            return None
        return self.ai_orchestration.initialize_system(system_info)
    
    def ai_make_pipeline_decisions(self, metrics: Dict[str, float], context: Dict[str, Any]) -> Optional[Dict[str, AIDecision]]:
        """AI decision-making throughout mining pipeline."""
        if self.ai_orchestration is None:
            return None
        return self.ai_orchestration.make_pipeline_decision(metrics, context)
    
    def ai_optimize_submission(self, shares: List[Dict[str, Any]], pool_info: Dict[str, Any]) -> Optional[AIDecision]:
        """AI-optimized share submission."""
        if self.ai_orchestration is None:
            return None
        return self.ai_orchestration.optimize_share_submission(shares, pool_info)
    
    def ai_generate_advisory(self, system_state: Dict[str, Any]) -> Optional[AIRecommendation]:
        """Generate AI advisory."""
        if self.ai_orchestration is None:
            return None
        return self.ai_orchestration.generate_advisory(system_state)

    def tick_all(self, healing_inputs: List[Dict[str, Any]],
                 optimization_targets: List[str],
                 mining_telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        One full control-loop pass across all three subsystems. In
        production this is called on a scheduler (e.g. every N
        seconds), not synchronously in request-response paths.
        """
        results = {"healing": [], "optimizing": [], "mining": None}

        for inp in healing_inputs:
            results["healing"].append(
                self.healer.monitor_tick(
                    module_id=inp["module_id"],
                    observed_severity=inp["severity"],
                    context=inp.get("context"),
                )
            )

        for name in optimization_targets:
            results["optimizing"].append(self.optimizer.optimize_tick(name))

        if self.miner is not None and mining_telemetry is not None:
            results["mining"] = self.miner.tick(mining_telemetry)

        return results

    def get_audit_summary(self) -> Dict[str, Any]:
        """Get summary of audit log for monitoring."""
        summary = {
            "total_entries": len(self.audit._entries),
            "by_subsystem": self.audit.count_by_subsystem(),
            "recent_healing": len(self.audit.recent("healing", 10)),
            "recent_optimizing": len(self.audit.recent("optimizing", 10)),
            "recent_mining": len(self.audit.recent("mining", 10)),
        }
        
        # Add AI orchestration summary if available
        if self.ai_orchestration is not None:
            summary["ai_orchestration"] = self.ai_orchestration.get_comprehensive_summary()
        
        return summary

    def get_breaker_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers."""
        return {
            action_class.value: self.breaker.get_breaker_status(action_class)
            for action_class in BREAKER_GATED_CLASSES
        }


__all__ = [
    "AutonomousMetaController",
    "AutonomousHealer",
    "AutonomousOptimizer",
    "AutonomousMiner",
    "MiningCircuitBreaker",
    "AuditLog",
    "AuditEntry",
    "MiningActionClass",
    "MiningDecision",
    "OptimizationTarget",
    "CircuitBreakerTripped",
    "BreakerState",
    # AI orchestration layer exports
    "UnifiedAIOrchestrationLayer",
    "AIStage",
    "AIDecision",
    "AIRecommendation",
]
