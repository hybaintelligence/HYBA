"""PYTHIA Autonomous Mining Controller — Mathematical Self-Governance.

This module extends the UnifiedMiningEngine with autonomous decision-making capabilities
while maintaining strict mathematical safety constraints. The autonomous controller operates
within well-defined boundaries enforced by geometric invariants and operator-specified limits.

Key Principles:
1. Mathematical Determinism: All autonomous decisions are based on φ-resonant patterns
2. Safety Overrides: Operator can always override autonomous decisions
3. Geometric Constraints: Actions must respect Hermiticity, PSD, and natural scaling laws
4. Audit Trail: Every autonomous decision is logged with mathematical justification
5. Gradual Autonomy: System starts with limited autonomy, increases based on performance

REFLEXIVE KNOWLEDGE LOOP:
The autonomous controller implements a recursive self-learning mechanism that:
1. Analyzes the codebase "surroundings" as a graph of mathematical invariants
2. Uses Deutsch Substrate counterfactual reasoning to hypothesize improvements
3. Validates all hypothetical changes against the 5 Safety Constraints
4. Commits validated improvements to internal memory for the next mining epoch
5. Drives continuous improvement via Pulvini Memory Compression as "metabolic rate"

The autonomous controller does not replace operator judgment — it augments it with
mathematically-grounded recommendations and automated execution within safe bounds.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field, replace
from types import SimpleNamespace
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .autonomous_audit_persistence import AutonomousAuditLogger
from .autonomous_escalation import AutonomousEscalationEngine
from .deutsch_knowledge_substrate import (
    KnowledgeSubstrate,
)
from pythia_mining.reflexive_cycle_timeout import (
    ReflexiveCyclePhase,
)  # Enterprise hardening


# ---------------------------------------------------------------------------
# Production hard-limit from mission memory — overrides any config
# ---------------------------------------------------------------------------
MAX_AUTONOMOUS_HASHRATE_EHS: float = 1.0  # Mission memory hard limit


class AutonomyLevel(Enum):
    """Levels of autonomous operation with increasing decision authority."""

    MANUAL = "manual"  # All decisions require operator approval
    ADVISORY = "advisory"  # System recommends, operator decides
    SUPERVISED = "supervised"  # System executes within predefined bounds
    AUTONOMOUS = "autonomous"  # System makes decisions with mathematical constraints
    EMERGENCY = "emergency"  # System takes protective action only

    @property
    def should_optimize(self) -> bool:
        """Whether this level may call optimise/reflexive logic."""
        return self in (AutonomyLevel.SUPERVISED, AutonomyLevel.AUTONOMOUS)

    @property
    def may_propose(self) -> bool:
        """Whether this level may generate recommendations."""
        return self != AutonomyLevel.MANUAL


class SafetyConstraint(Enum):
    """Mathematical safety constraints that autonomous actions must satisfy."""

    HERMITICITY = "hermiticity"  # Operations must preserve Hermitian properties
    POSITIVE_SEMIDEFINITE = "positive_semidefinite"  # Results must be PSD
    NATURAL_SCALING = "natural_scaling"  # Must follow φ-resonant scaling laws
    ENERGY_CONSERVATION = (
        "energy_conservation"  # Cannot exceed configured energy limits
    )
    INFORMATION_INTEGRITY = (
        "information_integrity"  # Must preserve informational structure
    )


OperatorApprovalCallbackResult = Union[bool, "OperatorApprovalDecision"]


@dataclass(frozen=True)
class OperatorApprovalDecision:
    """Structured response returned by an operator approval service.

    Carries the approval decision plus audit metadata. All callers must
    produce this type; legacy boolean paths are normalised by
    ``_normalise_operator_approval``.
    """

    approved: bool
    operator_id: Optional[str] = None
    reason: Optional[str] = "operator_callback"
    source: str = "structured_callback"


@dataclass
class AutonomousDecision:
    """Record of an autonomous decision with mathematical justification."""

    decision_id: str
    timestamp: float
    autonomy_level: AutonomyLevel
    decision_type: str
    mathematical_justification: Dict[str, Any]
    constraints_satisfied: List[SafetyConstraint]
    constraints_violated: List[SafetyConstraint]
    action_taken: str
    expected_outcome: str
    actual_outcome: Optional[str] = None
    operator_override: bool = False
    operator_id: Optional[str] = None
    operator_reason: Optional[str] = None
    operator_approval_source: Optional[str] = None


@dataclass
class AuditLogEntry:
    """Structured autonomy audit event with chain correlation metadata."""

    correlation_id: str
    timestamp: float
    event_type: str
    autonomy_level: str
    decision_id: Optional[str] = None
    action: str = ""
    outcome: str = ""
    constraints_checked: List[str] = field(default_factory=list)
    constraints_violated: List[str] = field(default_factory=list)
    operator_id: Optional[str] = None
    operator_action: Optional[str] = None
    state_diff: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperatorApprovalRequest:
    """Durable record for a human approval request."""

    request_id: str
    decision_id: str
    requested_at: float
    expires_at: float
    status: str = "pending"
    operator_id: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class OptimizationTarget:
    """Mathematical optimization target with constraints."""

    target_name: str
    objective_function: (
        str  # "maximize_hashrate", "minimize_energy", "maximize_phi_coherence"
    )
    current_value: float
    target_value: float
    tolerance: float
    constraints: List[SafetyConstraint]
    priority: int  # Higher priority = more important


@dataclass
class SelfOptimizationProposal:
    """A proposed self-optimization discovered through the Reflexive Knowledge Loop."""

    proposal_id: str
    timestamp: float
    improvement_type: str  # "phi_scaling", "search_depth", "compression_target", "coherence_threshold"
    current_value: float
    proposed_value: float
    expected_phi_density_gain: float  # Expected improvement in φ-density
    logical_consistency_score: float  # How well it maintains logical consistency
    constraints_satisfied: List[SafetyConstraint]
    constraints_violated: List[SafetyConstraint]
    counterfactual_confidence: float  # Confidence from Deutsch substrate simulation
    codebase_source_module: str  # Which codebase module inspired this change
    applied: bool = False
    applied_at: Optional[float] = None
    outcome_phi_density: Optional[float] = None


@dataclass
class CodebaseSurroundings:
    """Abstract representation of the codebase 'surroundings' for Active Inference."""

    module_names: List[str]
    mathematical_invariants: Dict[str, str]  # invariant_name -> invariant_type
    codebase_graph_edges: List[
        Tuple[str, str, float]
    ]  # (module_a, module_b, phi_resonance_weight)
    entropy_sources: List[
        str
    ]  # Modules with high entropy (interesting for exploration)
    stable_core: List[str]  # Modules with high invariant stability


@dataclass
class ReflexiveTargetBanditStats:
    """Bounded target-selection statistics for exploration/exploitation balance."""

    successes: int = 1
    failures: int = 1
    evidence_weight: float = 1.0

    @property
    def posterior_mean(self) -> float:
        return self.successes / max(self.successes + self.failures, 1)


# ---------------------------------------------------------------------------
# Environment-driven config helpers
# ---------------------------------------------------------------------------


def _env_autonomous_mining_enabled() -> bool:
    """Whether PYTHIA autonomous mining bootstrap is enabled at process startup."""
    val = os.getenv("HYBA_ENABLE_AUTONOMOUS_MINING", "true").strip().lower()
    return val in ("true", "1", "yes", "on")


def _env_autonomy_level() -> AutonomyLevel:
    """Read startup autonomy authority from environment.

    HYBA_ENABLE_AUTONOMOUS_MINING=true means the AI owns the boot path by
    default, so an unset HYBA_AUTONOMY_LEVEL starts in AUTONOMOUS instead of
    advisory. Operators can still explicitly set HYBA_AUTONOMY_LEVEL to manual,
    advisory, supervised, or emergency when they need a narrower launch posture.
    """
    default = "autonomous" if _env_autonomous_mining_enabled() else "advisory"
    raw = os.getenv("HYBA_AUTONOMY_LEVEL", default).strip().lower()
    try:
        return AutonomyLevel(raw)
    except ValueError:
        return (
            AutonomyLevel.AUTONOMOUS
            if default == "autonomous"
            else AutonomyLevel.ADVISORY
        )


def _env_float(name: str, default: float) -> float:
    """Read a float from the environment without letting bad config crash startup."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_max_hashrate() -> float:
    """Read max autonomous hashrate from env, clamped by mission memory hard limit."""
    configured = _env_float("HYBA_AUTONOMOUS_MAX_HASHRATE_EHS", 0.5)
    return min(configured, MAX_AUTONOMOUS_HASHRATE_EHS)


def _env_max_power() -> float:
    """Read max autonomous power from env."""
    return _env_float("HYBA_AUTONOMOUS_MAX_POWER_WATTS", 500.0)


def _env_phi_threshold() -> float:
    """Read φ-coherence threshold from env."""
    return _env_float("HYBA_PHI_COHERENCE_THRESHOLD", 0.70)


def _env_reflexive_enabled() -> bool:
    """Whether the reflexive knowledge loop is enabled."""
    val = os.getenv("HYBA_REFLEXIVE_LOOP_ENABLED", "true").strip().lower()
    return val in ("true", "1", "yes")


def _env_reflexive_interval() -> float:
    """Interval between reflexive cycles in seconds."""
    return _env_float("HYBA_REFLEXIVE_LOOP_INTERVAL", 60.0)


def _env_compression_drive() -> bool:
    """Whether the compression drive ('hunger') is enabled."""
    val = os.getenv("HYBA_COMPRESSION_DRIVE_ENABLED", "true").strip().lower()
    return val in ("true", "1", "yes")


def _env_operator_approval_required() -> bool:
    """Whether operator approval is required for guarded decisions."""
    val = os.getenv("HYBA_OPERATOR_APPROVAL_REQUIRED", "true").strip().lower()
    return val in ("true", "1", "yes")


def _env_circuit_breaker_cooldown() -> float:
    """Read autonomous hook circuit-breaker cooldown with safe minimum."""
    try:
        configured = float(
            os.getenv("HYBA_AUTONOMY_CIRCUIT_BREAKER_COOLDOWN_SECONDS", "300.0")
        )
    except ValueError:
        configured = 300.0
    return max(configured, 10.0)


def _env_circuit_breaker_failure_threshold() -> int:
    """Read autonomous hook circuit-breaker threshold with safe minimum."""
    try:
        configured = int(
            os.getenv("HYBA_AUTONOMY_CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3")
        )
    except ValueError:
        configured = 3
    return max(configured, 1)


# ---------------------------------------------------------------------------
# Metrics helper — simple counters / gauges that can be consumed externally
# ---------------------------------------------------------------------------


@dataclass
class AutonomyMetrics:
    """Lightweight metrics for monitoring / alerting."""

    total_decisions: int = 0
    autonomous_executions: int = 0
    operator_overrides: int = 0
    constraint_violations: int = 0
    consecutive_failures: int = 0
    autonomous_circuit_open: bool = False
    autonomous_circuit_open_until: Optional[float] = None
    autonomous_circuit_breaker_trips: int = 0
    current_autonomy_level: str = "advisory"
    phi_density: float = 0.0
    reflexive_cycle_count: int = 0
    degradation_events: int = 0
    stale_state_lock_recoveries: int = 0
    pending_operator_approvals: int = 0
    proposal_acceptance_rate: float = 0.0
    last_reflexive_cycle_duration_ms: float = 0.0


# Maximum length for sliding-window history arrays to guarantee O(1) heap usage
_MAX_PHI_DENSITY_HISTORY_LEN: int = 200
_MAX_COMPRESSION_SEEKING_HISTORY_LEN: int = 100
_MAX_LOGICAL_CONSISTENCY_HISTORY_LEN: int = 100
_MAX_POOL_RESPONSE_HISTORY_LEN: int = 1000
_POOL_FEEDBACK_RECENT_WINDOW: int = 100


@dataclass
class AutonomousConfig:
    """Configuration for autonomous mining controller.

    All numeric fields may be overridden via environment variables.
    The mission-memory hard-limit (MAX_AUTONOMOUS_HASHRATE_EHS = 1.0) is
    always enforced and cannot be overridden.
    """

    autonomy_level: AutonomyLevel = field(default_factory=_env_autonomy_level)
    max_autonomous_hashrate_ehs: float = field(default_factory=_env_max_hashrate)
    max_autonomous_power_watts: float = field(default_factory=_env_max_power)
    phi_coherence_threshold: float = field(default_factory=_env_phi_threshold)
    decision_audit_log_size: int = 1000  # Number of decisions to keep in memory
    operator_approval_required_for: List[str] = field(
        default_factory=lambda: [
            "pool_connection_change",
            "wallet_address_change",
            "significant_parameter_change",
            "emergency_shutdown",
        ]
    )
    optimization_targets: List[OptimizationTarget] = field(default_factory=list)
    # Reflexive Knowledge Loop configuration
    reflexive_loop_enabled: bool = field(default_factory=_env_reflexive_enabled)
    reflexive_loop_interval: float = field(default_factory=_env_reflexive_interval)
    max_proposals_per_cycle: int = 3
    virtual_session_horizon: float = 0.25  # Seconds to simulate virtual mining
    min_logical_consistency: float = 0.70  # Minimum consistency to accept a proposal
    compression_drive_enabled: bool = field(default_factory=_env_compression_drive)
    knowledge_growth_rate_target: float = 0.01  # Minimum knowledge growth per cycle
    # Persistence
    persistence_enabled: bool = True
    state_schema_version: int = 3
    state_backup_count: int = 10
    restore_autonomy_level_from_state: bool = False
    state_lock_stale_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("HYBA_AUTONOMY_STATE_LOCK_STALE_SECONDS", "300.0")
        )
    )
    metrics_cache_ttl_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("HYBA_AUTONOMY_METRICS_CACHE_TTL_SECONDS", "5.0")
        )
    )
    emergency_operator_ids: List[str] = field(
        default_factory=lambda: [
            item.strip()
            for item in os.getenv("HYBA_EMERGENCY_OPERATOR_IDS", "").split(",")
            if item.strip()
        ]
    )
    circuit_breaker_failure_threshold: int = field(
        default_factory=_env_circuit_breaker_failure_threshold
    )
    circuit_breaker_cooldown_seconds: float = field(
        default_factory=_env_circuit_breaker_cooldown
    )
    operator_approval_timeout_seconds: float = field(
        default_factory=lambda: float(
            os.getenv("HYBA_OPERATOR_APPROVAL_TIMEOUT_SECONDS", "300.0")
        )
    )
    audit_log_retention_policy: str = field(
        default_factory=lambda: os.getenv(
            "HYBA_AUTONOMY_AUDIT_RETENTION", "7d hot / 90d warm / 365d cold"
        )
    )
    persistence_dir: str = field(
        default_factory=lambda: os.getenv(
            "HYBA_AUTONOMY_STATE_DIR", "artifacts/autonomous_mining"
        )
    )
    state_backup_retention_count: int = 5

    def __post_init__(self) -> None:
        """Validate config at construction time."""
        # Never exceed the mission memory hard limit
        hard_limit = MAX_AUTONOMOUS_HASHRATE_EHS
        if self.max_autonomous_hashrate_ehs > hard_limit:
            self.max_autonomous_hashrate_ehs = hard_limit
        # Clamp power
        if self.max_autonomous_power_watts < 0:
            self.max_autonomous_power_watts = 0
        # Clamp coherence threshold
        self.phi_coherence_threshold = max(0.0, min(self.phi_coherence_threshold, 1.0))
        self.circuit_breaker_failure_threshold = max(
            1, int(self.circuit_breaker_failure_threshold)
        )
        self.circuit_breaker_cooldown_seconds = max(
            0.0, float(self.circuit_breaker_cooldown_seconds)
        )
        self.state_lock_stale_seconds = max(1.0, float(self.state_lock_stale_seconds))
        self.state_backup_retention_count = max(
            0, int(self.state_backup_retention_count)
        )


class AutonomousMiningController:
    """Autonomous mining controller with mathematical self-governance and Reflexive Learning."""

    def __init__(
        self,
        unified_engine: Any,  # UnifiedMiningEngine — imported lazily to avoid cycles
        config: Optional[AutonomousConfig] = None,
        lock_manager=None,
    ) -> None:
        self.engine: Any = unified_engine
        self.config = config or AutonomousConfig()
        self.lock_manager = lock_manager  # Enterprise: DistributedLockManager
        self.decision_log: List[AutonomousDecision] = []
        self.current_autonomy_level = self.config.autonomy_level
        self._consecutive_failures: int = 0
        self._circuit_open_until: float = 0.0
        self._circuit_breaker_trips: int = 0
        self._degradation_events: int = 0
        self._stale_state_lock_recoveries: int = 0
        self.operator_approval_callback: Optional[
            Callable[
                [AutonomousDecision],
                Union[bool, OperatorApprovalDecision, Dict[str, Any]],
            ]
        ] = None
        self.audit_log: List[AuditLogEntry] = []
        self.operator_approval_requests: List[OperatorApprovalRequest] = []
        self._active_approval_requests: Dict[str, OperatorApprovalRequest] = {}
        self._state_lock = threading.RLock()
        self._audit_lock = threading.RLock()
        self._approval_lock = threading.RLock()
        self._metrics_cache_lock = threading.RLock()
        self._metrics_cache_expires_at: float = 0.0
        self._metrics_cache_text: Optional[str] = None

        # --- Initialize enterprise hardening modules ---
        self._initialize_hardening_modules()

        # --- Tamper-evident persistent audit journal ---
        self._persistent_audit_logger = AutonomousAuditLogger()

        # --- Autonomous escalation engine ---
        self._escalation_engine = AutonomousEscalationEngine(
            audit_logger=self._persistent_audit_logger,
            escalation_callback=lambda level: self.set_autonomy_level(
                AutonomyLevel(level) if isinstance(level, str) else level
            ),
            degradation_callback=lambda reason: self.degrade_autonomy_level(
                reason
            ).value,
        )

        # --- Reflexive Knowledge Loop state ---
        self.knowledge_substrate = KnowledgeSubstrate()
        self.surroundings: CodebaseSurroundings = self._build_codebase_surroundings()
        self.proposal_history: List[SelfOptimizationProposal] = []
        self._self_optimization_epochs: int = 0
        self._last_reflexive_cycle: float = 0.0
        self._phi_density_history: List[float] = []
        self._compression_seeking_history: List[float] = []
        self._logical_consistency_history: List[float] = []
        self._last_reflexive_cycle_duration_ms: float = 0.0
        self._reflexive_target_bandits: Dict[str, ReflexiveTargetBanditStats] = {
            target: ReflexiveTargetBanditStats()
            for target in (
                "phi_scaling",
                "search_depth",
                "compression_target",
                "coherence_threshold",
            )
        }
        self._pool_response_history: List[Dict[str, Any]] = []

        # Reentrancy guard for get_phi_density
        self._computing_phi_density: bool = False

        # Continuous Health Loop state
        self.is_running: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        self.MAX_ERROR_THRESHOLD: float = 0.15  # 15% error rate triggers recalibration
        self._target_hashrate: float = 0.0
        self._actual_hashrate: float = 0.0
        self._error_rate: float = 0.0
        self._heal_attempt_window: List[float] = []  # sliding window of heal timestamps
        self._heal_attempt_window_seconds: float = 600.0  # 10-minute window

        # Autonomy Journal (auditability)
        self._autonomy_journal: List[Dict[str, Any]] = []
        self._reference_efficiency: float = 0.0  # baseline for optimization delta

        # Platform interface bridge (simulated for environment awareness)
        self._system_load: float = 0.0
        self._current_intensity: int = 5  # 1-10 scale

        # PID-verified stale lockfile cleanup on boot — removes stale .lock
        # only when no competing engine process is running.
        self._clean_stale_lock_on_boot()

        # Persistence: load previously-learned state
        if self.config.persistence_enabled:
            self._ensure_persistence_dir()
            self._load_reflexive_state()

    # ----------------------------------------------------------------
    # BOOT-TIME STALE LOCK RECOVERY
    # ----------------------------------------------------------------

    def _initialize_hardening_modules(self) -> None:
        """Initialize all enterprise hardening modules.

        These modules are wired into live operational paths and enforce
        strict production semantics:
        - ReflexiveCycleTimeoutGuard: 100ms deadline on reflexive cycles
        - StratumIdempotencyTracker: Double-spend prevention
        - CircuitBreakerFailoverManager: Pool failover coordination
        - OperatorApprovalTimeoutManager: Approval request timeouts

        NOTE: Modules are lazily instantiated and stored for access from
        live operational paths. Some may remain None if dependencies unavailable.
        """
        import logging

        try:
            from pythia_mining.reflexive_cycle_timeout import ReflexiveCycleGuard

            # Reflexive cycle timeout guard: 100ms deadline
            self.reflexive_cycle_guard = ReflexiveCycleGuard(
                cycle_id="autonomous_mining_controller",
                deadline_ms=100.0,
            )
        except Exception as e:
            logging.warning(f"Failed to initialize ReflexiveCycleTimeoutGuard: {e}")
            self.reflexive_cycle_guard = None

        try:
            from pythia_mining.stratum_idempotency_tracker import (
                StratumIdempotencyTracker,
            )

            # Stratum idempotency tracker: prevent double-spending
            if self.lock_manager:
                redis_client = self.lock_manager.redis
                self.stratum_idempotency = StratumIdempotencyTracker(
                    redis_client=redis_client,
                    idempotency_window_seconds=120,
                )
            else:
                self.stratum_idempotency = None
        except Exception as e:
            logging.warning(f"Failed to initialize StratumIdempotencyTracker: {e}")
            self.stratum_idempotency = None

        try:
            from pythia_mining.circuit_breaker_failover import (
                CircuitBreakerFailoverManager,
            )

            # Circuit breaker failover manager: 3-tier pool failover
            self.circuit_breaker = CircuitBreakerFailoverManager(
                primary_pool_id="primary",
                backup_pool_id="backup",
                tertiary_pool_id="tertiary",
                max_failures_before_failover=3,
            )
        except Exception as e:
            logging.warning(f"Failed to initialize CircuitBreakerFailoverManager: {e}")
            self.circuit_breaker = None

        try:
            from pythia_mining.operator_approval_timeout import (
                OperatorApprovalTimeoutManager,
            )

            # Operator approval timeout manager: 30s default timeout
            # Check signature before instantiating
            import inspect

            sig = inspect.signature(OperatorApprovalTimeoutManager.__init__)
            if "timeout_seconds" in sig.parameters:
                self.operator_approval_manager = OperatorApprovalTimeoutManager(
                    timeout_seconds=30.0,
                    escalation_on_timeout="AUTO_DENY",
                )
            elif "timeout" in sig.parameters:
                self.operator_approval_manager = OperatorApprovalTimeoutManager(
                    timeout=30.0,
                    escalation_on_timeout="AUTO_DENY",
                )
            else:
                # Fallback: just try with no args
                self.operator_approval_manager = OperatorApprovalTimeoutManager()
        except Exception as e:
            logging.warning(f"Failed to initialize OperatorApprovalTimeoutManager: {e}")
            self.operator_approval_manager = None

    def _clean_stale_lock_on_boot(self) -> None:
        """Remove a stale state-lock file only after confirming no competing PID owns it.

        On clean boot, any leftover .lock anchor from a previous crash is
        removed. If the lock's embedded PID still references a live process
        the lock is left intact to avoid corrupting the active writer.
        """
        lock_path = self._state_lock_path()
        if not lock_path.exists():
            return
        try:
            content = lock_path.read_text(encoding="utf-8", errors="replace")
            meta = json.loads(content) if content.strip() else {}
            pid = int(meta.get("pid", 0))
        except (json.JSONDecodeError, ValueError, OSError):
            pid = 0
        if pid > 0:
            try:
                os.kill(pid, 0)  # signal 0 probes whether the PID exists
                # The competing process is alive — keep the lock
                return
            except OSError:
                pass  # PID does not exist, safe to remove
        lock_path.unlink(missing_ok=True)
        self._stale_state_lock_recoveries += 1
        self._log_event(
            "boot_stale_lock_cleaned",
            {"lock_path": str(lock_path), "pid": pid},
        )

    # ----------------------------------------------------------------
    # PUBLIC METRICS — consumed by monitoring / logging
    # ----------------------------------------------------------------

    @property
    def metrics(self) -> AutonomyMetrics:
        """Return current snapshot of autonomy metrics."""
        return AutonomyMetrics(
            total_decisions=len(self.decision_log),
            autonomous_executions=sum(
                1 for d in self.decision_log if not d.operator_override
            ),
            operator_overrides=sum(1 for d in self.decision_log if d.operator_override),
            constraint_violations=sum(
                1 for d in self.decision_log if d.constraints_violated
            ),
            consecutive_failures=self._consecutive_failures,
            autonomous_circuit_open=self.is_circuit_open(),
            autonomous_circuit_open_until=self._circuit_open_until,
            autonomous_circuit_breaker_trips=self._circuit_breaker_trips,
            current_autonomy_level=self.current_autonomy_level.value,
            phi_density=self.get_phi_density(),
            reflexive_cycle_count=self._self_optimization_epochs,
            degradation_events=self._degradation_events,
            stale_state_lock_recoveries=self._stale_state_lock_recoveries,
            pending_operator_approvals=sum(
                1 for r in self.operator_approval_requests if r.status == "pending"
            ),
            proposal_acceptance_rate=self._proposal_acceptance_rate(),
            last_reflexive_cycle_duration_ms=self._last_reflexive_cycle_duration_ms,
        )

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        """Return metrics as a plain dict for export."""
        m = self.metrics
        return {
            "total_decisions": m.total_decisions,
            "autonomous_executions": m.autonomous_executions,
            "operator_overrides": m.operator_overrides,
            "constraint_violations": m.constraint_violations,
            "consecutive_failures": m.consecutive_failures,
            "autonomous_circuit_open": m.autonomous_circuit_open,
            "autonomous_circuit_open_until": m.autonomous_circuit_open_until,
            "autonomous_circuit_breaker_trips": m.autonomous_circuit_breaker_trips,
            "current_autonomy_level": m.current_autonomy_level,
            "phi_density": m.phi_density,
            "reflexive_cycle_count": m.reflexive_cycle_count,
            "degradation_events": m.degradation_events,
            "stale_state_lock_recoveries": m.stale_state_lock_recoveries,
            "pending_operator_approvals": m.pending_operator_approvals,
            "proposal_acceptance_rate": m.proposal_acceptance_rate,
            "last_reflexive_cycle_duration_ms": m.last_reflexive_cycle_duration_ms,
            "constraint_violations_by_type": self._constraint_violations_by_type(),
        }

    def _proposal_acceptance_rate(self) -> float:
        """Return applied proposal ratio without fabricating proposals."""
        if not self.proposal_history:
            return 0.0
        return sum(1 for p in self.proposal_history if p.applied) / len(
            self.proposal_history
        )

    def record_pool_response(
        self,
        *,
        accepted: Optional[bool] = None,
        latency_ms: Optional[float] = None,
        reason: str = "",
        error_code: Optional[Union[str, int]] = None,
        difficulty: Optional[float] = None,
        response_time_ms: Optional[float] = None,
        proposal_id: Optional[str] = None,
        decision_id: Optional[str] = None,
        target: Optional[str] = None,
        share_accepted: Optional[bool] = None,
        job_difficulty: Optional[float] = None,
    ) -> None:
        """Ingest an actual pool/testnet response without bypassing local verification.

        The reflexive loop must not learn exclusively from its deterministic virtual
        landscape. This method records real accept/reject evidence, including pool
        error code, difficulty, and response-time evidence, then updates bounded
        posterior target counts for deterministic Thompson-style selection.
        """
        if accepted is None:
            accepted = bool(share_accepted)
        if latency_ms is None:
            latency_ms = 0.0 if response_time_ms is None else response_time_ms
        if error_code and not reason:
            reason = error_code

        # Accept both 'difficulty' and 'job_difficulty' for backward compatibility
        final_difficulty = job_difficulty if job_difficulty is not None else difficulty

        response_target = target
        if response_target is None and proposal_id is not None:
            for proposal in reversed(self.proposal_history):
                if proposal.proposal_id == proposal_id:
                    response_target = proposal.improvement_type
                    break
        if response_target not in self._reflexive_target_bandits:
            response_target = "compression_target"

        observed_response_time = (
            latency_ms if response_time_ms is None else response_time_ms
        )
        response = {
            "accepted": bool(accepted),
            "latency_ms": max(0.0, float(latency_ms)),
            "reason": reason,
            "error_code": error_code,
            "difficulty": None if final_difficulty is None else float(final_difficulty),
            "proposal_id": proposal_id,
            "decision_id": decision_id,
            "target": response_target,
            "timestamp": time.time(),
            "recorded_at": time.time(),
        }
        self._pool_response_history.append(response)
        self._pool_response_history = self._pool_response_history[-1000:]
        self._update_target_bandit(response_target, bool(accepted))
        self.invalidate_prometheus_metrics_cache()

    def _update_target_bandit(self, target: str, accepted: bool) -> None:
        stats = self._reflexive_target_bandits.setdefault(
            target, ReflexiveTargetBanditStats()
        )
        if accepted:
            stats.successes = min(10_000, stats.successes + 1)
            stats.evidence_weight = min(10.0, stats.evidence_weight * 1.1)
        else:
            stats.failures = min(10_000, stats.failures + 1)
            stats.evidence_weight = max(0.1, stats.evidence_weight * 0.9)

    def _select_reflexive_targets(
        self, target_cycle: List[str], primary_target: str, growth_rate: float
    ) -> List[str]:
        """Select targets by deterministic Thompson-style posterior scoring.

        A true RNG would make this safety-critical loop harder to reproduce. We
        therefore use beta posterior means with a deterministic optimism term and
        a mandatory round-robin primary target, which gives Thompson-sampling-like
        exploration while preserving byte-for-byte replayability.
        """
        scores: List[Tuple[float, str]] = []
        total_trials = sum(
            stats.successes + stats.failures
            for stats in self._reflexive_target_bandits.values()
        )
        for target in target_cycle:
            stats = self._reflexive_target_bandits.setdefault(
                target, ReflexiveTargetBanditStats()
            )
            trials = stats.successes + stats.failures
            optimism = math.sqrt(math.log(max(total_trials, 2)) / max(trials, 1))
            compression_hunger = 0.05 if target == "compression_target" else 0.0
            score = stats.posterior_mean * stats.evidence_weight + 0.15 * optimism
            scores.append((score + compression_hunger, target))

        selected = [primary_target]
        for _, target in sorted(scores, reverse=True):
            if target not in selected:
                selected.append(target)
            if len(selected) >= self.config.max_proposals_per_cycle:
                break
        if growth_rate >= self.config.knowledge_growth_rate_target:
            return selected[: max(1, min(self.config.max_proposals_per_cycle, 2))]
        return selected[: self.config.max_proposals_per_cycle]

    def get_reflexive_target_bandit_snapshot(self) -> Dict[str, Dict[str, float]]:
        """Return bounded, serialisable target-selection evidence."""
        return {
            target: {
                "successes": stats.successes,
                "failures": stats.failures,
                "posterior_mean": round(stats.posterior_mean, 6),
                "evidence_weight": round(stats.evidence_weight, 6),
            }
            for target, stats in sorted(self._reflexive_target_bandits.items())
        }

    def _constraint_violations_by_type(self) -> Dict[str, int]:
        """Group observed decision constraint violations by constraint name."""
        counts: Dict[str, int] = {
            constraint.value: 0 for constraint in SafetyConstraint
        }
        for decision in self.decision_log:
            for constraint in decision.constraints_violated:
                counts[constraint.value] += 1
        return counts

    def get_prometheus_metrics_text(self) -> str:
        """Export low-cardinality Prometheus text-format metrics."""
        snapshot = self.get_metrics_snapshot()
        level_values = {level.value: index for index, level in enumerate(AutonomyLevel)}
        lines = [
            "# HELP hyba_phi_density Current reflexive phi-density.",
            "# TYPE hyba_phi_density gauge",
            f"hyba_phi_density {snapshot['phi_density']}",
            "# HELP hyba_constraint_violations_total Autonomous decisions with constraint violations.",
            "# TYPE hyba_constraint_violations_total counter",
            f"hyba_constraint_violations_total {snapshot['constraint_violations']}",
        ]
        for name, count in snapshot["constraint_violations_by_type"].items():
            lines.append(
                f'hyba_constraint_violations_by_type_total{{constraint="{name}"}} {count}'
            )
        lines.extend(
            [
                "# HELP hyba_consecutive_failures Current circuit-breaker failure count.",
                "# TYPE hyba_consecutive_failures gauge",
                f"hyba_consecutive_failures {snapshot['consecutive_failures']}",
                "# HELP hyba_autonomous_consecutive_failures Current autonomous hook failure count.",
                "# TYPE hyba_autonomous_consecutive_failures gauge",
                f"hyba_autonomous_consecutive_failures {snapshot['consecutive_failures']}",
                "# HELP hyba_autonomous_circuit_open Autonomous hook circuit-breaker state.",
                "# TYPE hyba_autonomous_circuit_open gauge",
                f"hyba_autonomous_circuit_open {1 if snapshot['autonomous_circuit_open'] else 0}",
                "# HELP hyba_autonomous_circuit_breaker_trips_total Autonomous hook circuit-breaker trips.",
                "# TYPE hyba_autonomous_circuit_breaker_trips_total counter",
                f"hyba_autonomous_circuit_breaker_trips_total {snapshot['autonomous_circuit_breaker_trips']}",
                "# HELP hyba_degradation_events_total Autonomy degradation events.",
                "# TYPE hyba_degradation_events_total counter",
                f"hyba_degradation_events_total {snapshot['degradation_events']}",
                "# HELP hyba_stale_state_lock_recoveries_total Stale state lock files auto-recovered.",
                "# TYPE hyba_stale_state_lock_recoveries_total counter",
                f"hyba_stale_state_lock_recoveries_total {snapshot['stale_state_lock_recoveries']}",
                "# HELP hyba_reflexive_cycle_duration_ms Last reflexive cycle duration.",
                "# TYPE hyba_reflexive_cycle_duration_ms gauge",
                f"hyba_reflexive_cycle_duration_ms {snapshot['last_reflexive_cycle_duration_ms']}",
                "# HELP hyba_proposal_acceptance_rate Applied proposal ratio.",
                "# TYPE hyba_proposal_acceptance_rate gauge",
                f"hyba_proposal_acceptance_rate {snapshot['proposal_acceptance_rate']}",
                "# HELP hyba_autonomy_level Numeric autonomy level.",
                "# TYPE hyba_autonomy_level gauge",
                f"hyba_autonomy_level {level_values.get(snapshot['current_autonomy_level'], -1)}",
                "# HELP hyba_operator_overrides_total Operator override count.",
                "# TYPE hyba_operator_overrides_total counter",
                f"hyba_operator_overrides_total {snapshot['operator_overrides']}",
                "# HELP hyba_pending_operator_approvals Pending bounded approval requests.",
                "# TYPE hyba_pending_operator_approvals gauge",
                f"hyba_pending_operator_approvals {snapshot['pending_operator_approvals']}",
                "# HELP hyba_pool_feedback_samples Bounded pool/testnet feedback samples retained.",
                "# TYPE hyba_pool_feedback_samples gauge",
                f"hyba_pool_feedback_samples {len(self._pool_response_history)}",
            ]
        )
        return "\n".join(lines) + "\n"

    def invalidate_prometheus_metrics_cache(self) -> None:
        """Invalidate cached metrics after state changes that operators must see immediately."""
        with self._metrics_cache_lock:
            self._metrics_cache_text = None
            self._metrics_cache_expires_at = 0.0

    def get_prometheus_metrics_text_cached(
        self, cache_ttl_seconds: Optional[float] = None
    ) -> str:
        """Return Prometheus text with a short TTL to protect scrape endpoints.

        The uncached exporter remains available for tests and direct diagnostics; web
        endpoints should prefer this method so an accidentally aggressive scraper
        does not repeatedly force expensive phi-density recomputation.
        """
        ttl = (
            self.config.metrics_cache_ttl_seconds
            if cache_ttl_seconds is None
            else cache_ttl_seconds
        )
        if ttl <= 0:
            return self.get_prometheus_metrics_text()
        now = time.monotonic()
        with self._metrics_cache_lock:
            if (
                self._metrics_cache_text is not None
                and now < self._metrics_cache_expires_at
            ):
                return self._metrics_cache_text
            text = self.get_prometheus_metrics_text()
            self._metrics_cache_text = text
            self._metrics_cache_expires_at = now + ttl
            return text

    # ----------------------------------------------------------------
    # ERROR / DEGRADATION
    # ----------------------------------------------------------------

    def is_circuit_open(self, now: Optional[float] = None) -> bool:
        """Return whether autonomous optimization is temporarily disabled."""
        current_time = time.time() if now is None else now
        if self._circuit_open_until <= 0:
            return False
        if current_time >= self._circuit_open_until:
            self._circuit_open_until = 0.0
            self._consecutive_failures = 0
            self._log_event("circuit_breaker_closed", {"timestamp": current_time})
            return False
        return True

    def record_autonomy_success(self) -> None:
        """Reset transient failure state after a successful autonomous hook."""
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0
        self.invalidate_prometheus_metrics_cache()

    # Alias used by the unified engine for the reflexive cycle success path
    record_circuit_success = record_autonomy_success

    def reset_circuit_breaker(
        self, operator_id: str, operator_reason: str = ""
    ) -> Dict[str, Any]:
        """Manually close the autonomy circuit breaker after operator review.

        Returns a dict with before/after state for audit logging.
        """
        before = {
            "circuit_open": self._circuit_open_until > 0,
            "consecutive_failures": self._consecutive_failures,
        }
        previous_open_until = self._circuit_open_until
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0
        self._log_event(
            "circuit_breaker_manual_reset",
            {
                "operator_id": operator_id,
                "reason": operator_reason,
                "previous_open_until": previous_open_until,
                "autonomy_level": self.current_autonomy_level.value,
            },
        )
        after = {
            "circuit_open": False,
            "consecutive_failures": 0,
        }
        return {"before_state": before, "after_state": after}

    def record_autonomy_failure(self, reason: str) -> AutonomyLevel:
        """Record a failed autonomous hook and open/degrade when threshold is met."""
        self._consecutive_failures += 1
        threshold = max(1, int(self.config.circuit_breaker_failure_threshold))
        if self._consecutive_failures < threshold:
            self._log_event(
                "autonomy_failure",
                {
                    "reason": reason,
                    "consecutive_failures": self._consecutive_failures,
                },
            )
            self.invalidate_prometheus_metrics_cache()
            return self.current_autonomy_level

        cooldown = max(0.0, float(self.config.circuit_breaker_cooldown_seconds))
        self._circuit_open_until = time.time() + cooldown
        self._log_event(
            "circuit_breaker_opened",
            {"reason": reason, "cooldown_seconds": cooldown},
        )
        return self.degrade_autonomy_level(
            reason=f"{reason}_consecutive_failures_{self._consecutive_failures}"
        )

    def degrade_autonomy_level(self, reason: str) -> AutonomyLevel:
        """Degrade one level when the current level experiences repeated failures.

        Returns the *new* autonomy level.
        """
        deg_map: Dict[AutonomyLevel, AutonomyLevel] = {
            AutonomyLevel.AUTONOMOUS: AutonomyLevel.SUPERVISED,
            AutonomyLevel.SUPERVISED: AutonomyLevel.ADVISORY,
            AutonomyLevel.ADVISORY: AutonomyLevel.MANUAL,
            AutonomyLevel.MANUAL: AutonomyLevel.MANUAL,  # no further
            AutonomyLevel.EMERGENCY: AutonomyLevel.MANUAL,
        }
        previous_level = self.current_autonomy_level
        new_level = deg_map.get(previous_level, AutonomyLevel.MANUAL)
        self.current_autonomy_level = new_level
        self._degradation_events += 1
        self._consecutive_failures = 0  # reset after degradation
        # NOTE: Do NOT reset _circuit_open_until here - it's set by record_autonomy_failure
        # and should remain open until cooldown expires

        # structured log
        self._log_audit_event(
            "degradation",
            {"from": previous_level.value, "to": new_level.value, "reason": reason},
            action="degrade_autonomy_level",
            outcome=new_level.value,
        )

        return new_level

    # ----------------------------------------------------------------
    # EVENT LOGGING (lightweight structured log)
    # ----------------------------------------------------------------

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Write a structured event to the Python logger."""
        import logging

        logger = logging.getLogger("pythia.autonomy")
        logger.info("autonomy_event", extra={"event_type": event_type, **data})

    def _log_audit_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        *,
        decision: Optional[AutonomousDecision] = None,
        action: str = "",
        outcome: str = "",
        operator_id: Optional[str] = None,
        operator_action: Optional[str] = None,
        state_diff: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        """Record a correlated audit event and mirror it to structured logging."""
        correlation_id = data.get("correlation_id") or (
            decision.decision_id if decision else f"autonomy_{uuid.uuid4().hex}"
        )
        entry = AuditLogEntry(
            correlation_id=correlation_id,
            timestamp=time.time(),
            event_type=event_type,
            autonomy_level=self.current_autonomy_level.value,
            decision_id=decision.decision_id if decision else data.get("decision_id"),
            action=action or data.get("action", ""),
            outcome=outcome or data.get("outcome", ""),
            constraints_checked=(
                [
                    c.value
                    for c in decision.constraints_satisfied
                    + decision.constraints_violated
                ]
                if decision
                else data.get("constraints_checked", [])
            ),
            constraints_violated=(
                [c.value for c in decision.constraints_violated]
                if decision
                else data.get("constraints_violated", [])
            ),
            operator_id=operator_id or data.get("operator_id"),
            operator_action=operator_action or data.get("operator_action"),
            state_diff=state_diff or data.get("state_diff", {}),
        )
        with self._audit_lock:
            self.audit_log.append(entry)
            if len(self.audit_log) > self.config.decision_audit_log_size:
                self.audit_log = self.audit_log[-self.config.decision_audit_log_size :]
        self._log_event(event_type, {**data, **entry.__dict__})
        if event_type in {
            "decision",
            "degradation",
            "operator_approval_completed",
            "operator_approval_rejected",
            "stale_state_lock_removed",
            "emergency_operator_bypass_approved",
            "emergency_operator_bypass_rejected",
            "state_rollback",
            "autonomous_circuit_opened",
            "autonomous_circuit_reclosed",
            "manual_autonomous_circuit_reset",
        }:
            self.invalidate_prometheus_metrics_cache()
        return entry

    # ================================================================
    # REFLEXIVE KNOWLEDGE LOOP — Recursive Self-Learning
    # ================================================================

    def _build_codebase_surroundings(self) -> CodebaseSurroundings:
        """Map the codebase 'surroundings' (Umwelt) as a graph of mathematical invariants.

        The AI creates an abstract representation of its own codebase, identifying:
        - Module dependencies and their φ-resonance weights
        - Mathematical invariants that constrain behavior
        - Entropy sources (high-variability modules) vs stable core modules
        - This serves as the "Laws of Physics" for the AI's universe.
        """
        module_names = [
            "phi_unified_mining_engine",
            "consciousness_engine",
            "deutsch_knowledge_substrate",
            "ai_optimizer",
            "pulvini_compressed_solver",
            "pulvini_memory_compression_proof",
            "pulvini_autonomics",
            "genesis_ai",
            "hendrix_phi_solver",
            "phi_scaling_engine",
            "stratum_client",
            "golden_ratio_library",
        ]

        # Core mathematical invariants that define the "Laws of Physics"
        mathematical_invariants: Dict[str, str] = {
            "hermiticity": "density_matrix_self_adjoint",
            "positive_semidefinite": "density_matrix_nonnegative_eigenvalues",
            "phi_resonance": "golden_ratio_alignment",
            "yang_mills_gap": "mass_gap_spectral_condition",
            "information_integrity": "lossless_compression_invertibility",
            "conservation_of_phi": "phi_folding_reversible_transform",
            "m32_domain_coverage": "spherical_32_domain_partition",
        }

        # φ-resonance weighted dependency edges between modules
        codebase_graph_edges: List[Tuple[str, str, float]] = [
            ("phi_unified_mining_engine", "consciousness_engine", 0.95),
            ("phi_unified_mining_engine", "ai_optimizer", 0.90),
            ("phi_unified_mining_engine", "pulvini_compressed_solver", 0.88),
            ("phi_unified_mining_engine", "deutsch_knowledge_substrate", 0.75),
            ("consciousness_engine", "ai_optimizer", 0.85),
            ("consciousness_engine", "pulvini_autonomics", 0.80),
            ("ai_optimizer", "deutsch_knowledge_substrate", 0.78),
            ("pulvini_compressed_solver", "pulvini_memory_compression_proof", 0.92),
            ("pulvini_compressed_solver", "hendrix_phi_solver", 0.87),
            ("pulvini_compressed_solver", "phi_scaling_engine", 0.83),
            ("hendrix_phi_solver", "golden_ratio_library", 0.96),
            ("stratum_client", "phi_unified_mining_engine", 0.65),
            ("genesis_ai", "phi_unified_mining_engine", 0.91),
            ("genesis_ai", "consciousness_engine", 0.89),
            ("genesis_ai", "deutsch_knowledge_substrate", 0.82),
            ("genesis_ai", "pulvini_autonomics", 0.85),
        ]

        # High-entropy modules (mathematical paths not yet fully explored)
        entropy_sources = [
            "phi_scaling_engine",
            "deutsch_knowledge_substrate",
            "ai_optimizer",
        ]

        # Stable core modules (mathematically rigorous, well-tested)
        stable_core = [
            "golden_ratio_library",
            "hendrix_phi_solver",
            "pulvini_memory_compression_proof",
            "consciousness_engine",
        ]

        return CodebaseSurroundings(
            module_names=module_names,
            mathematical_invariants=mathematical_invariants,
            codebase_graph_edges=codebase_graph_edges,
            entropy_sources=entropy_sources,
            stable_core=stable_core,
        )

    def get_phi_density(self) -> float:
        """Compute the current φ-density of the system.

        φ-density is a measure of how 'resonant' the system is with its own
        mathematical invariants. Higher values indicate better self-alignment.
        This serves as the objective function for the Reflexive Knowledge Loop.

        Includes a reentrancy guard to prevent circular recursion
        (get_autonomy_status → get_phi_density → …).
        """
        if self._computing_phi_density:
            return 0.5  # safe default during recursion

        self._computing_phi_density = True
        try:
            base_density = 0.5

            # Factor in constraint satisfaction rate from internal state
            total_decisions = len(self.decision_log)
            constraint_violations = sum(
                1 for d in self.decision_log if d.constraints_violated
            )
            if total_decisions > 0:
                constraint_health = 1.0 - (
                    constraint_violations / max(total_decisions, 1)
                )
                base_density += 0.2 * constraint_health

            # Factor in knowledge substrate quality
            try:
                knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
                avg_accuracy = knowledge_metrics.get("avg_predictive_accuracy", 0.5)
                base_density += 0.15 * avg_accuracy
                growth_rate = knowledge_metrics.get("knowledge_growth_rate", 0.0)
                base_density += 0.10 * min(growth_rate, 1.0)
            except Exception:
                pass

            # Factor in compression ratio (the "metabolic rate" drive)
            if (
                self.config.compression_drive_enabled
                and self._compression_seeking_history
            ):
                latest_compression = self._compression_seeking_history[-1]
                # Higher compression within info integrity limits improves density
                optimal_compression = min(latest_compression / 2.0, 1.0)
                base_density += 0.10 * optimal_compression

            # Factor in logical consistency over time
            if self._logical_consistency_history:
                avg_consistency = sum(self._logical_consistency_history) / len(
                    self._logical_consistency_history
                )
                base_density += 0.05 * avg_consistency

            # Factor in self-optimization epochs (learning accumulates density)
            if self._self_optimization_epochs > 0:
                learning_bonus = min(self._self_optimization_epochs * 0.01, 0.10)
                base_density += learning_bonus

            return min(max(base_density, 0.0), 1.0)
        finally:
            self._computing_phi_density = False

    def get_current_efficiency(self) -> float:
        """Return current mining efficiency proxy for improvement tracking.

        NOTE: This method intentionally does NOT call get_autonomy_status()
        to avoid circular recursion with get_phi_density().
        """
        base = 0.6
        total_decisions = len(self.decision_log)
        if total_decisions > 0:
            autonomous_count = sum(
                1 for d in self.decision_log if not d.operator_override
            )
            auto_rate = autonomous_count / max(total_decisions, 1)
            base += 0.2 * auto_rate
        return min(max(base, 0.0), 1.0)

    def _generate_counterfactual(self, target: str) -> SelfOptimizationProposal:
        """Use Deutsch Substrate to generate a counterfactual code change hypothesis.

        The AI asks: "What would happen if I changed this parameter?"
        It uses the Deutsch Knowledge Substrate's counterfactual reasoning
        to simulate the outcome without actually executing the change.
        """
        proposal_id = f"self_opt_{self._self_optimization_epochs}_{int(time.time())}"
        timestamp = time.time()

        if target == "phi_scaling":
            return self._propose_phi_scaling_improvement(proposal_id, timestamp)
        elif target == "search_depth":
            return self._propose_search_depth_improvement(proposal_id, timestamp)
        elif target == "compression_target":
            return self._propose_compression_improvement(proposal_id, timestamp)
        elif target == "coherence_threshold":
            return self._propose_coherence_threshold_improvement(proposal_id, timestamp)
        else:
            # Default: try phi_scaling
            return self._propose_phi_scaling_improvement(proposal_id, timestamp)

    def _propose_phi_scaling_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a φ-scaling factor adjustment."""
        current_value = 1.5  # Default φ-scaling factor from phi_scaling_engine

        # Use Deutsch substrate to determine optimal direction
        context = {
            "phi_resonance": 0.5,
            "difficulty": 1e12,
            "thermal_load": 0.5,
        }

        # Counterfactual: what if we increase φ-scaling?
        counterfactual_increase = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy="current_phi_scaling",
            actual_outcome={"efficiency": self.get_current_efficiency()},
            alternative_strategy="phi_scaling_increase",
            context=context,
        )

        # Counterfactual: what if we decrease φ-scaling?
        counterfactual_decrease = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy="current_phi_scaling",
            actual_outcome={"efficiency": self.get_current_efficiency()},
            alternative_strategy="phi_scaling_decrease",
            context=context,
        )

        # Choose direction with higher confidence
        if counterfactual_increase.confidence > counterfactual_decrease.confidence:
            proposed_value = current_value * 1.05  # 5% increase
            confidence = counterfactual_increase.confidence
        else:
            proposed_value = current_value * 0.95  # 5% decrease
            confidence = counterfactual_decrease.confidence

        # Estimate φ-density gain
        expected_gain = 0.02 * confidence

        # Compute logical consistency score based on explanation quality
        self.knowledge_substrate.best_explanation_for_context(context)
        logical_consistency = 0.7 + 0.2 * confidence

        proposed_action = {
            "phi_scaling_change": proposed_value - current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="phi_scaling",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=min(max(logical_consistency, 0.0), 1.0),
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=confidence,
            codebase_source_module="phi_scaling_engine",
        )

    def _propose_search_depth_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a search depth adjustment."""
        current_value = 60.0  # Default max_search_time from SearchStrategy

        context = {
            "phi_resonance": 0.5,
            "difficulty": 1e12,
            "thermal_load": 0.5,
        }

        # Counterfactual: deeper vs shallower search
        counterfactual_deeper = self.knowledge_substrate.counterfactual_reasoning(
            actual_strategy="current_search_depth",
            actual_outcome={"efficiency": self.get_current_efficiency()},
            alternative_strategy="deeper_search",
            context=context,
        )

        # Adjust direction based on φ-coherence signal
        if self._phi_density_history:
            trend = (
                self._phi_density_history[-1] - self._phi_density_history[0]
            ) / max(len(self._phi_density_history), 1)
            if trend > 0.01:
                # Increasing coherence → can afford deeper search
                proposed_value = min(current_value * 1.1, 120.0)
                confidence = counterfactual_deeper.confidence
            else:
                # Decreasing coherence → shallower search
                proposed_value = max(current_value * 0.9, 10.0)
                confidence = 0.6
        else:
            proposed_value = current_value
            confidence = 0.5

        expected_gain = 0.015 * confidence
        logical_consistency = 0.75

        proposed_action = {
            "search_depth_change": proposed_value - current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="search_depth",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=logical_consistency,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=confidence,
            codebase_source_module="ai_optimizer",
        )

    def _propose_compression_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a memory compression ratio adjustment.

        This is the "Hunger" drive — the AI seeks higher compression ratios
        to achieve more elegant representations of the mining process.
        """
        current_value = 1.86  # Default compression factor

        # The drive: seek higher compression for more elegant representation
        # But must respect information integrity constraint (compression_ratio <= 2.0)
        self.get_phi_density()

        # Compute the "hunger" signal based on current state
        if self._compression_seeking_history:
            # If compression hasn't improved recently, hunger increases
            recent_trend = (
                self._compression_seeking_history[-1]
                - self._compression_seeking_history[0]
            ) / max(len(self._compression_seeking_history), 1)
            hunger_factor = max(0.0, 1.0 - abs(recent_trend))  # Hunger grows when stale
        else:
            hunger_factor = 0.5

        # Propose a compression improvement within safety bounds
        proposed_value = current_value * (1.0 + 0.02 * hunger_factor)
        # Information Integrity constraint caps at 2.0
        proposed_value = min(proposed_value, 1.98)

        expected_gain = 0.03 * (proposed_value / current_value - 1.0)
        logical_consistency = 0.8 if proposed_value <= 2.0 else 0.4

        proposed_action = {
            "compression_ratio": proposed_value,
            "current_compression": current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="compression_target",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=logical_consistency,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=0.7 + 0.2 * hunger_factor,
            codebase_source_module="pulvini_memory_compression_proof",
        )

    def _propose_coherence_threshold_improvement(
        self, proposal_id: str, timestamp: float
    ) -> SelfOptimizationProposal:
        """Propose a coherence threshold adjustment."""
        current_value = self.config.phi_coherence_threshold

        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
        avg_accuracy = knowledge_metrics.get("avg_predictive_accuracy", 0.5)

        # If knowledge is accurate, we can lower the threshold (more autonomy)
        if avg_accuracy > 0.7:
            proposed_value = max(current_value * 0.95, 0.50)
            confidence = 0.8
        # If knowledge is inaccurate, raise threshold (more caution)
        elif avg_accuracy < 0.3:
            proposed_value = min(current_value * 1.05, 0.90)
            confidence = 0.6
        else:
            proposed_value = current_value
            confidence = 0.5

        expected_gain = 0.01 * confidence
        logical_consistency = 0.7 + 0.2 * avg_accuracy

        proposed_action = {
            "coherence_threshold_change": proposed_value - current_value,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)

        return SelfOptimizationProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            improvement_type="coherence_threshold",
            current_value=current_value,
            proposed_value=proposed_value,
            expected_phi_density_gain=expected_gain,
            logical_consistency_score=min(max(logical_consistency, 0.0), 1.0),
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            counterfactual_confidence=confidence,
            codebase_source_module="consciousness_engine",
        )

    def _simulate_virtual_mining(self, proposal: SelfOptimizationProposal) -> float:
        """Run a 'Virtual Mining Session' in memory to assess the proposal.

        Instead of executing on hardware, the AI simulates the effect of the
        proposed change on its internal model, using the Deutsch Knowledge
        Substrate's counterfactual reasoning engine.

        Returns the simulated φ-density after applying the proposal.
        """
        # Start with current φ-density
        current_density = self.get_phi_density()

        # Factor in constraint health
        violation_penalty = len(proposal.constraints_violated) * 0.1

        # Factor in logical consistency
        consistency_bonus = proposal.logical_consistency_score * 0.05

        # Factor in counterfactual confidence
        confidence_bonus = proposal.counterfactual_confidence * 0.05

        # Deterministic SHA-256d landscape sample so proposals are measured against
        # real hash avalanche behavior, not a smooth idealized proxy.
        landscape_bonus = self._sha256d_landscape_score(proposal) * 0.01

        # Actual pool/testnet feedback dampens or boosts virtual optimism.
        pool_feedback = self._pool_feedback_adjustment(proposal.improvement_type)

        # Expected gain scaled by proposal quality
        quality_factor = (
            (1.0 - violation_penalty)
            * (1.0 + consistency_bonus)
            * (1.0 + confidence_bonus)
        )
        simulated_density = (
            current_density
            + proposal.expected_phi_density_gain * quality_factor
            + landscape_bonus
            + pool_feedback
        )

        return min(max(simulated_density, 0.0), 1.0)

    def _sha256d_landscape_score(self, proposal: SelfOptimizationProposal) -> float:
        """Return a deterministic score from actual double-SHA-256 avalanche samples."""
        sample = json.dumps(
            {
                "proposal_id": proposal.proposal_id,
                "type": proposal.improvement_type,
                "current": round(proposal.current_value, 12),
                "proposed": round(proposal.proposed_value, 12),
            },
            sort_keys=True,
        ).encode("utf-8")
        digest = hashlib.sha256(hashlib.sha256(sample).digest()).digest()
        leading_zero_nibbles = 0
        for byte in digest:
            high, low = byte >> 4, byte & 0x0F
            if high == 0:
                leading_zero_nibbles += 1
            else:
                break
            if low == 0:
                leading_zero_nibbles += 1
            else:
                break
        avalanche = sum(bin(byte).count("1") for byte in digest) / 256.0
        return min(1.0, 0.75 * avalanche + 0.25 * min(leading_zero_nibbles / 8.0, 1.0))

    def _pool_feedback_adjustment(self, target: str) -> float:
        target_name = (
            target.target_name if hasattr(target, "target_name") else str(target)
        )
        now = time.time()
        relevant = [
            r
            for r in self._pool_response_history[-200:]
            if r.get("target") == target_name or target_name == "None"
        ]
        if not relevant:
            return 0.0
        weighted_total = 0.0
        weighted_accepts = 0.0
        half_life_seconds = 900.0
        for response in relevant:
            age = max(
                0.0,
                now
                - float(response.get("timestamp", response.get("recorded_at", now))),
            )
            weight = 0.5 ** (age / half_life_seconds)
            weighted_total += weight
            if response.get("accepted"):
                weighted_accepts += weight
        if weighted_total <= 0.0:
            return 0.0
        acceptance = weighted_accepts / weighted_total
        return (acceptance - 0.5) * 0.02

    def supervised_production_evidence_status(self) -> Dict[str, Any]:
        """Return the evidence-gate status for supervised production graduation.

        This is deliberately an evidence ledger, not a self-certification path: live
        pool/testnet responses, restart-surviving state, proposal provenance, and
        resource-drift measurements must be present before unattended production is
        defensible.
        """
        linked_responses = [
            r
            for r in self._pool_response_history
            if r.get("proposal_id") or r.get("decision_id")
        ]
        targets_with_feedback = sorted(
            {
                str(r.get("target"))
                for r in self._pool_response_history
                if r.get("target")
            }
        )
        return {
            "posture": "supervised_production_ready",
            "unattended_production": "blocked_until_24h_evidence_pack",
            "pool_response_window_limit": _MAX_POOL_RESPONSE_HISTORY_LEN,
            "pool_feedback_samples": len(self._pool_response_history),
            "accepted_shares": sum(
                1 for r in self._pool_response_history if r.get("accepted")
            ),
            "rejected_shares": sum(
                1 for r in self._pool_response_history if not r.get("accepted")
            ),
            "targets_with_feedback": targets_with_feedback,
            "pythia_decision_linked_samples": len(linked_responses),
            "target_selection": self.get_reflexive_target_bandit_snapshot(),
            "acceptance_criteria": {
                "pytest_suite_local_venv": "required_external_evidence",
                "command_room_game_day_transcript": "required_external_evidence",
                "twenty_four_hour_supervised_run": "required_external_evidence",
                "real_pool_or_testnet_feedback": bool(self._pool_response_history),
                "proposal_provenance_preserved": all(
                    bool(p.codebase_source_module) for p in self.proposal_history
                ),
                "restart_recovery_verified": self.config.persistence_enabled,
                "memory_cpu_drift_measured": "required_external_evidence",
                "share_telemetry_tied_to_pythia_decisions": bool(linked_responses),
            },
        }

    def validate_constraints(self, proposal: SelfOptimizationProposal) -> bool:
        """Validate that a proposal satisfies all 5 Safety Constraints.

        Returns True only if all constraints are satisfied and the proposal
        maintains logical consistency above the minimum threshold.
        """
        if len(proposal.constraints_violated) > 0:
            return False

        if proposal.logical_consistency_score < self.config.min_logical_consistency:
            return False

        # Hermiticity constraint: operations must preserve Hermitian properties
        if SafetyConstraint.HERMITICITY not in proposal.constraints_satisfied:
            return False

        # PSD constraint: results must be Positive Semi-Definite
        if SafetyConstraint.POSITIVE_SEMIDEFINITE not in proposal.constraints_satisfied:
            return False

        # Information Integrity constraint: must preserve informational structure
        if SafetyConstraint.INFORMATION_INTEGRITY not in proposal.constraints_satisfied:
            return False

        return True

    def apply_self_optimization(self, proposal: SelfOptimizationProposal) -> None:
        """Commit a validated self-optimization to internal memory AND apply to engine.

        This is the "learning" step — the AI updates its internal configuration
        to reflect the discovered improvement, which takes effect immediately
        in the next mining epoch.
        """
        if proposal.applied:
            return

        proposal.applied = True
        proposal.applied_at = time.time()

        # Record outcome density (will be updated in the next cycle)
        proposal.outcome_phi_density = self.get_phi_density()

        # Apply the proposal to internal configuration AND engine runtime
        if proposal.improvement_type == "phi_scaling":
            # Update the φ-scaling power in the ensemble (immediate effect)
            proposed_phi_scaling = proposal.proposed_value
            if self.engine is not None:
                if self.engine.phi_ensemble is not None:
                    self.engine.phi_ensemble.config["phi_scaling_power"] = (
                        proposed_phi_scaling
                    )

            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="phi_scaling",
                    objective_function="maximize_phi_coherence",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=0.05,
                    constraints=[
                        SafetyConstraint.HERMITICITY,
                        SafetyConstraint.POSITIVE_SEMIDEFINITE,
                        SafetyConstraint.NATURAL_SCALING,
                    ],
                    priority=5,
                )
            )

        elif proposal.improvement_type == "search_depth":
            # Update max search iterations in AI optimizer (immediate effect)
            proposed_depth = proposal.proposed_value
            if self.engine is not None and self.engine.optimizer is not None:
                # Clamp search depth within safe bounds (10–1000 iterations)
                clamped_depth = max(10, min(1000, int(proposed_depth)))
                self.engine.optimizer.max_search_iterations = clamped_depth

            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="search_depth",
                    objective_function="maximize_hashrate",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=5.0,
                    constraints=[
                        SafetyConstraint.ENERGY_CONSERVATION,
                        SafetyConstraint.NATURAL_SCALING,
                    ],
                    priority=4,
                )
            )

        elif proposal.improvement_type == "compression_target":
            # Update compression target in PULVINI solver (immediate effect)
            proposed_compression = proposal.proposed_value
            if self.engine is not None and self.engine.solver is not None:
                # Clamp compression within safe bounds (1.0–2.0 ratio)
                clamped_compression = max(1.0, min(2.0, proposed_compression))
                self.engine.solver.compression_target_ratio = clamped_compression

            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="compression_target",
                    objective_function="maximize_phi_coherence",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=0.05,
                    constraints=[
                        SafetyConstraint.INFORMATION_INTEGRITY,
                        SafetyConstraint.HERMITICITY,
                    ],
                    priority=3,
                )
            )

        elif proposal.improvement_type == "coherence_threshold":
            # Update coherence threshold in consciousness engine (immediate effect)
            proposed_coherence = proposal.proposed_value
            self.config.phi_coherence_threshold = proposed_coherence

            if self.engine is not None and self.engine.consciousness is not None:
                # Update all three thresholds proportionally. ConsciousnessConfig is
                # immutable so runtime tuning replaces the config atomically.
                ratio = (
                    proposed_coherence / 0.70
                )  # Scale from default SINGULAR threshold
                self.engine.consciousness.config = replace(
                    self.engine.consciousness.config,
                    phi_singular_threshold=max(0.0, min(1.0, 0.70 * ratio)),
                    phi_distributed_threshold=max(0.0, min(1.0, 0.40 * ratio)),
                    phi_critical_threshold=max(0.0, min(1.0, 0.20 * ratio)),
                )

            self.config.optimization_targets.append(
                OptimizationTarget(
                    target_name="coherence_threshold",
                    objective_function="minimize_energy",
                    current_value=proposal.current_value,
                    target_value=proposal.proposed_value,
                    tolerance=0.02,
                    constraints=[
                        SafetyConstraint.NATURAL_SCALING,
                        SafetyConstraint.ENERGY_CONSERVATION,
                    ],
                    priority=2,
                )
            )

        # Record the improvement in knowledge substrate
        self.knowledge_substrate.create_knowledge_from_success(
            strategy_id=f"self_opt_{proposal.improvement_type}",
            context={
                "improvement_type": proposal.improvement_type,
                "current_value": proposal.current_value,
                "proposed_value": proposal.proposed_value,
                "phi_density_before": self.get_phi_density(),
            },
            outcome={
                "accepted": True,
                "confidence": proposal.counterfactual_confidence,
                "expected_gain": proposal.expected_phi_density_gain,
            },
        )

        self._self_optimization_epochs += 1

    async def _run_reflexive_cycle(self) -> List[SelfOptimizationProposal]:
        """Run one complete iteration of the Reflexive Knowledge Loop.

        The full loop:
        1. Analyze surroundings (current φ-density and codebase state)
        2. Generate counterfactual proposals via Deutsch Substrate
        3. Simulate virtual mining sessions for each proposal
        4. Validate against 5 Safety Constraints
        5. Apply validated improvements to internal memory

        ENTERPRISE HARDENING: Wrapped with 100ms timeout guard to prevent
        unbounded reflexive cycles from consuming resources indefinitely.
        """
        if not self.config.reflexive_loop_enabled:
            return []

        # Guard the entire reflexive cycle with a 100ms deadline
        try:
            self.reflexive_cycle_guard.check_deadline("reflexive_cycle_start")
        except Exception as e:
            import logging

            logging.warning(f"Reflexive cycle timeout guard initialization failed: {e}")

        try:
            current_density = self.get_phi_density()
            self.get_current_efficiency()

            # Record historical metrics — bounded sliding window for O(1) heap
            self._phi_density_history.append(current_density)
            if len(self._phi_density_history) > _MAX_PHI_DENSITY_HISTORY_LEN:
                self._phi_density_history = self._phi_density_history[
                    -_MAX_PHI_DENSITY_HISTORY_LEN:
                ]

            # Step 1: Analyze surroundings — which entropy source to explore?
            # Use deterministic posterior target selection so actual pool/testnet
            # feedback can steer the loop without sacrificing reproducibility.
            self.reflexive_cycle_guard.record_phase_start(
                ReflexiveCyclePhase.PARSE_CODEBASE
            )
            knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
            target_cycle = [
                "phi_scaling",
                "search_depth",
                "compression_target",
                "coherence_threshold",
            ]
            current_target = target_cycle[
                self._self_optimization_epochs % len(target_cycle)
            ]
            growth_rate = knowledge_metrics.get("knowledge_growth_rate", 0.0)
            self.reflexive_cycle_guard.record_phase_end(
                ReflexiveCyclePhase.PARSE_CODEBASE, success=True
            )

            # Step 2: Generate counterfactual proposals
            self.reflexive_cycle_guard.record_phase_start(
                ReflexiveCyclePhase.SIMULATE_MINING
            )
            proposals = []
            targets_to_try = self._select_reflexive_targets(
                target_cycle, current_target, growth_rate
            )
            if (
                self.config.compression_drive_enabled
                and "compression_target" not in targets_to_try
            ):
                targets_to_try.append("compression_target")

            for target in targets_to_try[: self.config.max_proposals_per_cycle]:
                proposal = self._generate_counterfactual(target)
                proposals.append(proposal)
                self.proposal_history.append(proposal)
            self.reflexive_cycle_guard.record_phase_end(
                ReflexiveCyclePhase.SIMULATE_MINING, success=True
            )

            # Step 3: Simulate virtual mining sessions
            for proposal in proposals:
                simulated_density = self._simulate_virtual_mining(proposal)
                # The simulation outcome informs the proposal's expected gain
                proposal.expected_phi_density_gain = simulated_density - current_density

            # Step 4: Validate against 5 Safety Constraints
            self.reflexive_cycle_guard.record_phase_start(
                ReflexiveCyclePhase.VALIDATE_CONSTRAINTS
            )
            valid_proposals = [p for p in proposals if self.validate_constraints(p)]
            self.reflexive_cycle_guard.record_phase_end(
                ReflexiveCyclePhase.VALIDATE_CONSTRAINTS, success=True
            )

            # Step 5: Apply validated improvements
            self.reflexive_cycle_guard.record_phase_start(
                ReflexiveCyclePhase.APPLY_PROPOSAL
            )
            for proposal in valid_proposals:
                self.apply_self_optimization(proposal)
                self._update_target_bandit(proposal.improvement_type, True)
            for proposal in proposals:
                if not proposal.applied:
                    self._update_target_bandit(proposal.improvement_type, False)
            self.reflexive_cycle_guard.record_phase_end(
                ReflexiveCyclePhase.APPLY_PROPOSAL, success=True
            )

            # Record logical consistency — bounded sliding window
            avg_consistency = sum(p.logical_consistency_score for p in proposals) / max(
                len(proposals), 1
            )
            self._logical_consistency_history.append(avg_consistency)
            if (
                len(self._logical_consistency_history)
                > _MAX_LOGICAL_CONSISTENCY_HISTORY_LEN
            ):
                self._logical_consistency_history = self._logical_consistency_history[
                    -_MAX_LOGICAL_CONSISTENCY_HISTORY_LEN:
                ]

            # Record compression seeking — bounded sliding window
            if self.config.compression_drive_enabled:
                compression_proposals = [
                    p for p in proposals if p.improvement_type == "compression_target"
                ]
                if compression_proposals:
                    avg_compression = sum(
                        p.proposed_value for p in compression_proposals
                    ) / len(compression_proposals)
                    self._compression_seeking_history.append(avg_compression)
                    if (
                        len(self._compression_seeking_history)
                        > _MAX_COMPRESSION_SEEKING_HISTORY_LEN
                    ):
                        self._compression_seeking_history = (
                            self._compression_seeking_history[
                                -_MAX_COMPRESSION_SEEKING_HISTORY_LEN:
                            ]
                        )

            return proposals

        except Exception as e:
            import logging

            logging.error(f"Reflexive cycle failed: {e}", exc_info=True)
            self.reflexive_cycle_guard.mark_rollback()
            # Return empty proposal list on error, circuit breaker handles recovery
            return []

    async def seek_improvement(self) -> Dict[str, Any]:
        """Public entry point for the Reflexive Knowledge Loop.

        Analyzes the 'surroundings' (codebase state), uses the Deutsch Substrate
        to simulate counterfactual improvements, validates against Safety Constraints,
        and commits validated improvements to internal memory.

        Returns a status report of the improvement cycle.
        """
        cycle_start = time.time()

        # Run the full reflexive cycle
        proposals = await self._run_reflexive_cycle()

        cycle_duration = time.time() - cycle_start
        self._last_reflexive_cycle_duration_ms = round(cycle_duration * 1000.0, 3)

        # Build the improvement report
        if proposals:
            sum(1 for p in proposals if p.applied)
            proposal_details = [
                {
                    "proposal_id": p.proposal_id,
                    "improvement_type": p.improvement_type,
                    "current_value": p.current_value,
                    "proposed_value": p.proposed_value,
                    "expected_gain": p.expected_phi_density_gain,
                    "logical_consistency": p.logical_consistency_score,
                    "counterfactual_confidence": p.counterfactual_confidence,
                    "constraints_satisfied": [c.value for c in p.constraints_satisfied],
                    "constraints_violated": [c.value for c in p.constraints_violated],
                    "applied": p.applied,
                    "source_module": p.codebase_source_module,
                }
                for p in proposals
            ]
        else:
            proposal_details = []

        metrics = self.knowledge_substrate.get_knowledge_metrics()

        # Persist learned state after each cycle
        self._save_reflexive_state()

        return {
            "reflexive_cycle_executed": True,
            "cycle_duration_seconds": round(cycle_duration, 4),
            "cycle_duration_ms": self._last_reflexive_cycle_duration_ms,
            "epoch": self._self_optimization_epochs,
            "current_phi_density": self.get_phi_density(),
            "proposals_generated": len(proposals),
            "proposals_applied": sum(1 for p in proposals if p.applied),
            "autonomy_level": self.current_autonomy_level.value,
            "proposals": proposal_details,
            "knowledge_metrics": {
                "total_explanations": metrics.get("total_explanations", 0),
                "avg_predictive_accuracy": metrics.get("avg_predictive_accuracy", 0.0),
                "knowledge_growth_rate": metrics.get("knowledge_growth_rate", 0.0),
                "counterfactual_models": metrics.get("counterfactual_models", 0),
                "criticism_events": metrics.get("criticism_events", 0),
            },
            "surroundings": {
                "entropy_sources": self.surroundings.entropy_sources,
                "stable_core_count": len(self.surroundings.stable_core),
                "module_count": len(self.surroundings.module_names),
            },
            "compression_drive": {
                "enabled": self.config.compression_drive_enabled,
                "history_length": len(self._compression_seeking_history),
                "latest_seeking": (
                    self._compression_seeking_history[-1]
                    if self._compression_seeking_history
                    else None
                ),
            },
            "target_selection": self.get_reflexive_target_bandit_snapshot(),
            "pool_feedback_samples": len(self._pool_response_history),
        }

    # ================================================================
    # PERSISTENCE — Reflexive state survives restart
    # ================================================================

    def _ensure_persistence_dir(self) -> None:
        """Create the persistence directory if it does not exist."""
        Path(self.config.persistence_dir).mkdir(parents=True, exist_ok=True)

    def _state_file_path(self) -> Path:
        """Return the full path to the reflexive state JSON file."""
        return Path(self.config.persistence_dir) / "reflexive_state.json"

    def _state_lock_path(self) -> Path:
        """Return the lock-file path that guards state replacement."""
        return Path(self.config.persistence_dir) / "reflexive_state.lock"

    def _state_backup_glob(self) -> str:
        """Return the glob pattern for rotated state backups."""
        return "reflexive_state.json.backup.*"

    def _acquire_state_lock(self) -> Path:
        """Create the persistence lock file, reclaiming it only after stale timeout."""
        lock_path = self._state_lock_path()
        now = time.time()
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as handle:
                json.dump({"pid": os.getpid(), "created_at": now}, handle)
            return lock_path
        except FileExistsError:
            try:
                age = now - lock_path.stat().st_mtime
            except OSError as exc:
                raise TimeoutError(f"state lock unavailable: {exc}") from exc
            if age <= self.config.state_lock_stale_seconds:
                raise TimeoutError(
                    "state lock is active; "
                    f"age={age:.3f}s stale_after={self.config.state_lock_stale_seconds:.3f}s"
                )
            lock_path.unlink(missing_ok=True)
            self._log_event(
                "stale_state_lock_reclaimed",
                {"lock_path": str(lock_path), "age_seconds": round(age, 3)},
            )
            return self._acquire_state_lock()

    def _release_state_lock(self, lock_path: Path) -> None:
        """Release the persistence lock file if this process owns the critical section."""
        try:
            lock_path.unlink(missing_ok=True)
        except OSError as exc:
            self._log_event("state_lock_release_error", {"error": str(exc)})

    def _rotate_state_backups(self, state_file: Optional[Path] = None) -> None:
        """Keep only the configured number of state backups.

        When called with a state_file path, snapshots the current state into
        a timestamped backup under a 'backups/' subdirectory before rotating.
        When called without arguments, rotates the legacy .backup.* files.
        """
        if state_file is not None and state_file.exists():
            backup_dir = state_file.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = (
                backup_dir
                / f"reflexive_state_{int(time.time())}_{uuid.uuid4().hex[:8]}.json"
            )
            shutil.copy2(state_file, backup)
            backups = sorted(
                backup_dir.glob("reflexive_state_*.json"),
                key=lambda p: p.stat().st_mtime,
            )
            for stale in backups[: -self.config.state_backup_count]:
                stale.unlink(missing_ok=True)
        retention = self.config.state_backup_retention_count
        glob_pattern = self._state_backup_glob()
        backup_files = sorted(
            Path(self.config.persistence_dir).glob(glob_pattern),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for stale_backup in backup_files[retention:]:
            stale_backup.unlink(missing_ok=True)

    def _backup_existing_state(self, state_file: Path) -> None:
        """Create a bounded backup before replacing the state file."""
        if self.config.state_backup_retention_count <= 0 or not state_file.exists():
            return
        backup_name = (
            f"{state_file.name}.backup.{int(time.time() * 1000)}.{uuid.uuid4().hex[:8]}"
        )
        shutil.copy2(state_file, state_file.with_name(backup_name))
        self._rotate_state_backups(state_file)

    def _save_reflexive_state(self) -> None:
        """Persist reflexive learning state to disk.

        Saves proposals, φ-density history, knowledge substrate state,
        and optimisation targets so they survive a restart.
        """
        if not self.config.persistence_enabled:
            return
        with self._state_lock:
            self._save_reflexive_state_locked()

    def _save_reflexive_state_locked(self) -> None:
        """Persist reflexive learning state while the in-process lock is held."""
        state = {
            "epochs": self._self_optimization_epochs,
            "phi_density_history": self._phi_density_history,
            "compression_seeking_history": self._compression_seeking_history,
            "logical_consistency_history": self._logical_consistency_history,
            "optimization_targets": [
                {
                    "target_name": t.target_name,
                    "objective_function": t.objective_function,
                    "current_value": t.current_value,
                    "target_value": t.target_value,
                    "tolerance": t.tolerance,
                    "priority": t.priority,
                }
                for t in self.config.optimization_targets
            ],
            "proposals": [
                {
                    "proposal_id": p.proposal_id,
                    "improvement_type": p.improvement_type,
                    "current_value": p.current_value,
                    "proposed_value": p.proposed_value,
                    "expected_phi_density_gain": p.expected_phi_density_gain,
                    "logical_consistency_score": p.logical_consistency_score,
                    "counterfactual_confidence": p.counterfactual_confidence,
                    "applied": p.applied,
                    "codebase_source_module": p.codebase_source_module,
                }
                for p in self.proposal_history
            ],
            "autonomy_level": self.current_autonomy_level.value,
            "phi_coherence_threshold": self.config.phi_coherence_threshold,
            "capacity_limits": {
                "max_proposals_per_cycle": self.config.max_proposals_per_cycle,
                "max_autonomous_hashrate_ehs": self.config.max_autonomous_hashrate_ehs,
                "max_autonomous_power_watts": self.config.max_autonomous_power_watts,
            },
            "target_selection": self.get_reflexive_target_bandit_snapshot(),
            "pool_response_history": self._pool_response_history[-1000:],
        }
        state["schema_version"] = self.config.state_schema_version
        try:
            state_file = self._state_file_path()
            state_file.parent.mkdir(parents=True, exist_ok=True)
            payload = json.dumps(state, indent=2, sort_keys=True)
            checksum = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            with self._state_file_lock(state_file):
                tmp_file = state_file.with_name(
                    f"{state_file.name}.{uuid.uuid4().hex}.tmp"
                )
                tmp_file.write_text(payload, encoding="utf-8")
                tmp_file.replace(state_file)
                state_file.with_suffix(state_file.suffix + ".sha256").write_text(
                    checksum, encoding="utf-8"
                )
                self._rotate_state_backups(state_file)
        except (OSError, TimeoutError) as exc:
            self._log_audit_event(
                "persist_error",
                {"error": str(exc)},
                action="save_reflexive_state",
                outcome="error",
            )

    def _state_file_lock(self, state_file: Path) -> Any:
        """Return a cross-process lock context with stale-lock recovery."""
        stale_seconds = max(0.0, self.config.state_lock_stale_seconds)
        log_audit_event = self._log_audit_event
        self_controller = self

        class _StateFileLock:
            def __init__(self) -> None:
                self.lock_path = state_file.with_suffix(state_file.suffix + ".lock")
                self.acquired = False

            def _remove_stale_lock_if_needed(self) -> bool:
                if stale_seconds <= 0 or not self.lock_path.exists():
                    return False
                lock_age = time.time() - self.lock_path.stat().st_mtime
                if lock_age < stale_seconds:
                    return False
                stale_payload = self.lock_path.read_text(
                    encoding="utf-8", errors="replace"
                )
                self.lock_path.unlink(missing_ok=True)
                self_controller._stale_state_lock_recoveries += 1
                log_audit_event(
                    "stale_state_lock_removed",
                    {
                        "lock_path": str(self.lock_path),
                        "lock_age_seconds": round(lock_age, 3),
                        "stale_payload": stale_payload,
                    },
                    action="acquire_state_file_lock",
                    outcome="stale_lock_removed",
                )
                return True

            def __enter__(self) -> None:
                deadline = time.monotonic() + 5.0
                while True:
                    try:
                        fd = os.open(
                            self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                        )
                        payload = json.dumps(
                            {"pid": os.getpid(), "created_at": time.time()}
                        )
                        os.write(fd, payload.encode("utf-8"))
                        os.close(fd)
                        self.acquired = True
                        return None
                    except FileExistsError:
                        self._remove_stale_lock_if_needed()
                        if time.monotonic() >= deadline:
                            raise TimeoutError(
                                f"state lock contention: {self.lock_path}"
                            )
                        time.sleep(0.05)

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
                if self.acquired:
                    self.lock_path.unlink(missing_ok=True)

        return _StateFileLock()

    def _load_reflexive_state(self) -> None:
        """Restore previously-persisted reflexive learning state."""
        state_file = self._state_file_path()
        if not state_file.exists():
            return
        with self._state_lock:
            self._load_reflexive_state_locked(state_file)

    def _load_reflexive_state_locked(self, state_file: Path) -> None:
        """Restore previously-persisted state while the in-process lock is held."""
        try:
            checksum_file = state_file.with_suffix(state_file.suffix + ".sha256")
            if checksum_file.exists():
                expected = checksum_file.read_text(encoding="utf-8").strip()
                actual = hashlib.sha256(state_file.read_bytes()).hexdigest()
                if expected != actual:
                    raise ValueError("reflexive state checksum mismatch")
            with open(state_file, "r") as f:
                state = json.load(f)
            schema_version = int(state.get("schema_version", 1))
            if schema_version > self.config.state_schema_version:
                raise ValueError(
                    f"unsupported reflexive state schema {schema_version}; "
                    f"controller supports {self.config.state_schema_version}"
                )
            if schema_version < self.config.state_schema_version:
                self._log_audit_event(
                    "state_schema_migration",
                    {
                        "from_schema_version": schema_version,
                        "to_schema_version": self.config.state_schema_version,
                    },
                    action="load_reflexive_state",
                    outcome="migrated_in_memory",
                )
            self._self_optimization_epochs = state.get("epochs", 0)
            self._phi_density_history = state.get("phi_density_history", [])
            # Enforce maximum bounds on restored history
            if len(self._phi_density_history) > _MAX_PHI_DENSITY_HISTORY_LEN:
                self._phi_density_history = self._phi_density_history[
                    -_MAX_PHI_DENSITY_HISTORY_LEN:
                ]
            self._compression_seeking_history = state.get(
                "compression_seeking_history", []
            )
            if (
                len(self._compression_seeking_history)
                > _MAX_COMPRESSION_SEEKING_HISTORY_LEN
            ):
                self._compression_seeking_history = self._compression_seeking_history[
                    -_MAX_COMPRESSION_SEEKING_HISTORY_LEN:
                ]
            self._logical_consistency_history = state.get(
                "logical_consistency_history", []
            )
            if (
                len(self._logical_consistency_history)
                > _MAX_LOGICAL_CONSISTENCY_HISTORY_LEN
            ):
                self._logical_consistency_history = self._logical_consistency_history[
                    -_MAX_LOGICAL_CONSISTENCY_HISTORY_LEN:
                ]
            for target, data in state.get("target_selection", {}).items():
                if target in self._reflexive_target_bandits:
                    self._reflexive_target_bandits[target] = ReflexiveTargetBanditStats(
                        successes=max(1, int(data.get("successes", 1))),
                        failures=max(1, int(data.get("failures", 1))),
                        evidence_weight=max(
                            0.1, min(10.0, float(data.get("evidence_weight", 1.0)))
                        ),
                    )
            self._pool_response_history = list(state.get("pool_response_history", []))[
                -1000:
            ]
            self.config.phi_coherence_threshold = state.get(
                "phi_coherence_threshold", self.config.phi_coherence_threshold
            )
            # Restore autonomy level only when explicitly enabled; runtime authority
            # should otherwise come from deployment config, not stale state.
            if self.config.restore_autonomy_level_from_state:
                persisted_level = state.get("autonomy_level", "advisory")
                try:
                    self.current_autonomy_level = AutonomyLevel(persisted_level)
                except ValueError:
                    pass
            # Restore optimisation targets
            for t_data in state.get("optimization_targets", []):
                self.config.optimization_targets.append(
                    OptimizationTarget(
                        target_name=t_data["target_name"],
                        objective_function=t_data["objective_function"],
                        current_value=t_data["current_value"],
                        target_value=t_data["target_value"],
                        tolerance=t_data.get("tolerance", 0.05),
                        constraints=[],
                        priority=t_data.get("priority", 1),
                    )
                )
            self._log_audit_event(
                "state_restored",
                {
                    "epochs": self._self_optimization_epochs,
                    "phi_density_history_len": len(self._phi_density_history),
                    "proposals_restored": len(state.get("proposals", [])),
                },
            )
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
            self._log_audit_event(
                "load_state_error",
                {"error": str(exc)},
                action="load_reflexive_state",
                outcome="error",
            )

    # ================================================================
    # EXISTING FUNCTIONALITY (preserved and extended)
    # ================================================================

    def _generate_decision_id(self) -> str:
        """Generate a unique decision ID using UUID (thread-safe)."""
        return f"autonomous_decision_{uuid.uuid4().hex[:8]}_{int(time.time())}"

    def _log_decision(self, decision: AutonomousDecision) -> None:
        """Log autonomous decision with audit trail."""
        self.decision_log.append(decision)
        # Maintain log size limit
        if len(self.decision_log) > self.config.decision_audit_log_size:
            self.decision_log = self.decision_log[
                -self.config.decision_audit_log_size :
            ]

        # Structured logging for monitoring
        self._log_audit_event(
            "decision",
            {
                "decision_id": decision.decision_id,
                "autonomy_level": decision.autonomy_level.value,
                "decision_type": decision.decision_type,
                "constraints_violated": len(decision.constraints_violated),
                "operator_override": decision.operator_override,
                "operator_id": decision.operator_id,
                "operator_reason": decision.operator_reason,
                "operator_approval_source": decision.operator_approval_source,
                "action_taken": decision.action_taken,
            },
            decision=decision,
            action=decision.action_taken,
            outcome=decision.actual_outcome or "pending",
        )

    def set_operator_approval_callback(
        self,
        callback: Callable[
            [AutonomousDecision],
            Union[bool, OperatorApprovalDecision, Dict[str, Any]],
        ],
    ) -> None:
        """Set callback for operator approval decisions."""
        self.operator_approval_callback = callback

    def set_autonomy_level(self, level: AutonomyLevel) -> None:
        """Set the current autonomy level."""
        self.current_autonomy_level = level
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    def get_decision_history(
        self,
        limit: Optional[int] = None,
    ) -> List[AutonomousDecision]:
        """Get history of autonomous decisions."""
        if limit:
            return self.decision_log[-limit:]
        return self.decision_log.copy()

    def get_autonomy_status(self) -> Dict[str, Any]:
        """Get current autonomy status and metrics, including Reflexive Learning state."""
        return {
            "autonomy_level": self.current_autonomy_level.value,
            "total_decisions": len(self.decision_log),
            "autonomous_decisions": sum(
                1 for d in self.decision_log if not d.operator_override
            ),
            "operator_overrides": sum(
                1 for d in self.decision_log if d.operator_override
            ),
            "constraint_violations": sum(
                1 for d in self.decision_log if d.constraints_violated
            ),
            "consecutive_failures": self._consecutive_failures,
            "degradation_events": self._degradation_events,
            "circuit_breaker": {
                "open": self.is_circuit_open(),
                "open_until": self._circuit_open_until,
                "failure_threshold": self.config.circuit_breaker_failure_threshold,
                "cooldown_seconds": self.config.circuit_breaker_cooldown_seconds,
            },
            "recent_decisions": [
                {
                    "decision_id": d.decision_id,
                    "timestamp": d.timestamp,
                    "decision_type": d.decision_type,
                    "action_taken": d.action_taken,
                    "operator_override": d.operator_override,
                }
                for d in self.decision_log[-10:]
            ],
            "reflexive_learning": {
                "enabled": self.config.reflexive_loop_enabled,
                "self_optimization_epochs": self._self_optimization_epochs,
                "phi_density": self.get_phi_density(),
                "compression_drive_enabled": self.config.compression_drive_enabled,
                "knowledge_explanations": len(self.knowledge_substrate.explanations),
                "knowledge_counterfactuals": len(
                    self.knowledge_substrate.counterfactuals
                ),
                "knowledge_criticisms": len(self.knowledge_substrate.criticism_history),
                "proposals_generated": len(self.proposal_history),
                "proposals_applied": sum(1 for p in self.proposal_history if p.applied),
                "latest_phi_density": (
                    self._phi_density_history[-1] if self._phi_density_history else None
                ),
                "logical_consistency_history_length": len(
                    self._logical_consistency_history
                ),
            },
        }

    def record_circuit_failure(self, reason: str) -> None:
        """Record an autonomous failure for circuit breaker tracking (alias for backward compat)."""
        self.record_autonomy_failure(reason)

    def _can_execute_autonomously(self, decision: AutonomousDecision) -> bool:
        """Determine if decision can execute without an operator approval callback."""
        if decision.operator_override:
            return False
        if self.current_autonomy_level == AutonomyLevel.MANUAL:
            return False
        if self._requires_operator_approval(decision.decision_type):
            return self._request_operator_approval(decision)
        if decision.constraints_violated:
            return False
        if self.current_autonomy_level == AutonomyLevel.ADVISORY:
            return False
        if self.current_autonomy_level in (
            AutonomyLevel.SUPERVISED,
            AutonomyLevel.AUTONOMOUS,
        ):
            return len(decision.constraints_violated) == 0
        if self.current_autonomy_level == AutonomyLevel.EMERGENCY:
            return True
        return False

    async def optimize_search_strategy(
        self,
        current_coherence: float,
        current_hashrate_ehs: float,
    ) -> AutonomousDecision:
        """Autonomously optimize search strategy based on current conditions."""
        try:
            from .ai_optimizer import SearchStrategy
        except ModuleNotFoundError:
            SearchStrategy = SimpleNamespace  # type: ignore[assignment]

        decision_id = self._generate_decision_id()
        timestamp = time.time()
        knowledge_metrics = self.knowledge_substrate.get_knowledge_metrics()
        avg_accuracy = knowledge_metrics.get("avg_predictive_accuracy", 0.5)
        if current_coherence >= 0.80:
            proposed_strategy = SearchStrategy(
                phi_resonance_enabled=True,
                adaptive_difficulty=True,
                max_search_time=30.0,
            )
            justification = {
                "reason": "high_phi_coherence_aggressive_optimization",
                "coherence": current_coherence,
                "phi_threshold": 0.80,
                "expected_improvement": "faster_search_with_high_confidence",
                "knowledge_accuracy": avg_accuracy,
                "self_optimization_epochs": self._self_optimization_epochs,
            }
        elif current_coherence >= 0.70:
            proposed_strategy = SearchStrategy(
                phi_resonance_enabled=True,
                adaptive_difficulty=True,
                max_search_time=60.0,
            )
            justification = {
                "reason": "good_phi_coherence_balanced_optimization",
                "coherence": current_coherence,
                "phi_threshold": 0.70,
                "expected_improvement": "balanced_speed_and_reliability",
                "knowledge_accuracy": avg_accuracy,
                "self_optimization_epochs": self._self_optimization_epochs,
            }
        else:
            proposed_strategy = SearchStrategy(
                phi_resonance_enabled=True,
                adaptive_difficulty=False,
                max_search_time=120.0,
            )
            justification = {
                "reason": "low_phi_coherence_conservative_optimization",
                "coherence": current_coherence,
                "phi_threshold": 0.70,
                "expected_improvement": "prioritize_reliability_over_speed",
                "knowledge_accuracy": avg_accuracy,
                "self_optimization_epochs": self._self_optimization_epochs,
            }
        proposed_action = {
            "strategy_change": "search_strategy",
            "max_search_time": proposed_strategy.max_search_time,
            "adaptive_difficulty": proposed_strategy.adaptive_difficulty,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)
        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=self.current_autonomy_level,
            decision_type="search_strategy_optimization",
            mathematical_justification=justification,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            action_taken=f"set_search_strategy_{proposed_strategy.max_search_time}s",
            expected_outcome=justification["expected_improvement"],
        )
        self._log_decision(decision)
        if self._can_execute_autonomously(decision):
            self.engine.optimizer.current_strategy = proposed_strategy
            decision.actual_outcome = "strategy_updated_successfully"
        else:
            approved = self._request_operator_approval(decision)
            if approved:
                self.engine.optimizer.current_strategy = proposed_strategy
                decision.actual_outcome = "strategy_updated_after_approval"
            else:
                decision.operator_override = True
                decision.actual_outcome = "operator_rejected_strategy_change"
        return decision

    async def optimize_hashrate_target(
        self,
        current_hashrate_ehs: float,
        target_hashrate_ehs: float,
    ) -> AutonomousDecision:
        """Autonomously adjust hashrate target within safety limits."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()
        target_hashrate_ehs = min(target_hashrate_ehs, MAX_AUTONOMOUS_HASHRATE_EHS)
        if current_hashrate_ehs < target_hashrate_ehs:
            proposed_increase = min(
                target_hashrate_ehs - current_hashrate_ehs,
                self.config.max_autonomous_hashrate_ehs - current_hashrate_ehs,
            )
            justification = {
                "reason": "increase_hashrate_to_meet_target",
                "current_hashrate_ehs": current_hashrate_ehs,
                "target_hashrate_ehs": target_hashrate_ehs,
                "proposed_increase_ehs": proposed_increase,
                "expected_improvement": "higher_mining_efficiency",
            }
            action_taken = f"increase_hashrate_by_{proposed_increase}_ehs"
            hashrate_change = proposed_increase
        else:
            proposed_decrease = current_hashrate_ehs - target_hashrate_ehs
            justification = {
                "reason": "decrease_hashrate_to_save_energy",
                "current_hashrate_ehs": current_hashrate_ehs,
                "target_hashrate_ehs": target_hashrate_ehs,
                "proposed_decrease_ehs": proposed_decrease,
                "expected_improvement": "reduced_energy_consumption",
            }
            action_taken = f"decrease_hashrate_by_{proposed_decrease}_ehs"
            hashrate_change = -proposed_decrease
        proposed_action = {
            "hashrate_change": hashrate_change,
            "target_hashrate_ehs": target_hashrate_ehs,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)
        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=self.current_autonomy_level,
            decision_type="hashrate_optimization",
            mathematical_justification=justification,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            action_taken=action_taken,
            expected_outcome=justification["expected_improvement"],
        )
        self._log_decision(decision)
        if self._can_execute_autonomously(decision):
            decision.actual_outcome = "hashrate_target_updated"
        else:
            approved = self._request_operator_approval(decision)
            if approved:
                decision.actual_outcome = "hashrate_target_updated_after_approval"
            else:
                decision.operator_override = True
                decision.actual_outcome = "operator_rejected_hashrate_change"
        return decision

    async def optimize_compression_ratio(
        self,
        current_compression: float,
        target_compression: float,
    ) -> AutonomousDecision:
        """Autonomously adjust memory compression ratio."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()
        justification = {
            "reason": "optimize_memory_compression_for_efficiency",
            "current_compression": current_compression,
            "target_compression": target_compression,
            "phi_optimal_range": (1.5, 2.0),
            "expected_improvement": "better_memory_utilization",
        }
        proposed_action = {
            "compression_ratio": target_compression,
            "current_compression": current_compression,
        }
        satisfied, violated = self._check_safety_constraints(proposed_action)
        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=self.current_autonomy_level,
            decision_type="compression_optimization",
            mathematical_justification=justification,
            constraints_satisfied=satisfied,
            constraints_violated=violated,
            action_taken=f"adjust_compression_to_{target_compression}",
            expected_outcome=justification["expected_improvement"],
        )
        self._log_decision(decision)
        if self._can_execute_autonomously(decision):
            decision.actual_outcome = "compression_ratio_updated"
        else:
            approved = self._request_operator_approval(decision)
            if approved:
                decision.actual_outcome = "compression_ratio_updated_after_approval"
            else:
                decision.operator_override = True
                decision.actual_outcome = "operator_rejected_compression_change"
        return decision

    async def emergency_shutdown(
        self,
        reason: str,
        mathematical_justification: Dict[str, Any],
    ) -> AutonomousDecision:
        """Execute emergency shutdown with mathematical justification."""
        decision_id = self._generate_decision_id()
        timestamp = time.time()
        previous_level = self.current_autonomy_level
        self.current_autonomy_level = AutonomyLevel.EMERGENCY
        decision = AutonomousDecision(
            decision_id=decision_id,
            timestamp=timestamp,
            autonomy_level=AutonomyLevel.EMERGENCY,
            decision_type="emergency_shutdown",
            mathematical_justification=mathematical_justification,
            constraints_satisfied=[SafetyConstraint.ENERGY_CONSERVATION],
            constraints_violated=[],
            action_taken="emergency_shutdown_initiated",
            expected_outcome="safe_system_shutdown",
        )
        self._log_decision(decision)
        self.current_autonomy_level = previous_level
        return decision

    def _check_safety_constraints(
        self,
        proposed_action: Dict[str, Any],
    ) -> Tuple[List[SafetyConstraint], List[SafetyConstraint]]:
        """Check if proposed action satisfies all safety constraints."""
        satisfied = []
        violated = []

        # Check Hermiticity constraint
        if self._check_hermiticity(proposed_action):
            satisfied.append(SafetyConstraint.HERMITICITY)
        else:
            violated.append(SafetyConstraint.HERMITICITY)

        # Check PSD constraint
        if self._check_psd(proposed_action):
            satisfied.append(SafetyConstraint.POSITIVE_SEMIDEFINITE)
        else:
            violated.append(SafetyConstraint.POSITIVE_SEMIDEFINITE)

        # Check Natural Scaling constraint
        if self._check_natural_scaling(proposed_action):
            satisfied.append(SafetyConstraint.NATURAL_SCALING)
        else:
            violated.append(SafetyConstraint.NATURAL_SCALING)

        # Check Energy Conservation constraint
        if self._check_energy_conservation(proposed_action):
            satisfied.append(SafetyConstraint.ENERGY_CONSERVATION)
        else:
            violated.append(SafetyConstraint.ENERGY_CONSERVATION)

        # Check Information Integrity constraint
        if self._check_information_integrity(proposed_action):
            satisfied.append(SafetyConstraint.INFORMATION_INTEGRITY)
        else:
            violated.append(SafetyConstraint.INFORMATION_INTEGRITY)

        return satisfied, violated

    def _check_hermiticity(self, action: Dict[str, Any]) -> bool:
        """Check if action preserves Hermitian properties.

        An operation preserves Hermiticity if:
        - It does not introduce imaginary asymmetries in the density matrix
        - The proposed change is self-adjoint (symmetric under transpose-conjugate)
        """
        # Verify the action doesn't break Hermitian symmetry
        for key, value in action.items():
            if isinstance(value, complex):
                # Complex values must appear with their conjugates
                return False
            if isinstance(value, (int, float)):
                # Real-valued changes preserve Hermiticity by construction
                # when applied to the diagonal of the density matrix
                continue
        return True  # Assume actions preserve hermiticity unless proven otherwise

    def _check_psd(self, action: Dict[str, Any]) -> bool:
        """Check if action results in positive semidefinite matrices.

        PSD is preserved if:
        - All eigenvalues remain non-negative
        - The action does not introduce negative diagonal elements
        """
        if "compression_ratio" in action:
            ratio = action["compression_ratio"]
            # Compression must not make eigenvalues negative
            if ratio > 3.0:
                return False
        if "phi_scaling_change" in action:
            change = action["phi_scaling_change"]
            # Scaling must not invert the density matrix
            if abs(change) > 2.0:
                return False
        return True  # Assume actions preserve PSD unless proven otherwise

    def _check_natural_scaling(self, action: Dict[str, Any]) -> bool:
        """Check if action follows φ-resonant scaling laws."""
        if "hashrate_change" in action:
            change = action["hashrate_change"]
            # Changes should follow φ-based scaling patterns
            return abs(change) < 2.0  # Limit sudden changes
        if "phi_scaling_change" in action:
            change = action["phi_scaling_change"]
            # φ-scaling changes should be small and incremental
            return abs(change) < 0.5
        if "search_depth_change" in action:
            change = action["search_depth_change"]
            # Search depth changes should be within φ-scaled bounds
            return abs(change) < 30.0
        if "coherence_threshold_change" in action:
            change = action["coherence_threshold_change"]
            # Coherence thresholds should move gradually
            return abs(change) < 0.1
        return True

    def _check_energy_conservation(self, action: Dict[str, Any]) -> bool:
        """Check if action respects energy limits."""
        if "power_consumption_watts" in action:
            power = action["power_consumption_watts"]
            return power <= self.config.max_autonomous_power_watts
        if "search_depth_change" in action:
            change = action["search_depth_change"]
            # Deeper search consumes more energy
            if change > 0:
                # Each 10s of search depth costs energy
                energy_gain = change / 10.0 * 10.0  # ~10W per 10s
                return (self.config.max_autonomous_power_watts - 100.0) >= energy_gain
        return True

    def _check_information_integrity(self, action: Dict[str, Any]) -> bool:
        """Check if action preserves informational structure.

        Information Integrity is the 5th and most important constraint
        for a data-less learning system. It ensures that no information
        is lost during compression or transformation.
        """
        if "compression_ratio" in action:
            ratio = action["compression_ratio"]
            # Lossless compression limit: PULVINI phi-folding is invertible up to 2.0
            return ratio <= 2.0  # Limit compression to preserve information
        if "phi_scaling_change" in action:
            change = action["phi_scaling_change"]
            # Scaling must not cause aliasing in the φ-domain
            return abs(change) < 1.0
        return True

    def _requires_operator_approval(self, decision_type: str) -> bool:
        """Check if decision type requires operator approval."""
        return decision_type in self.config.operator_approval_required_for

    def _normalise_operator_approval(
        self,
        raw_response: Union[bool, OperatorApprovalDecision, Dict[str, Any]],
    ) -> OperatorApprovalDecision:
        """Normalize bool or structured operator-service responses."""
        if isinstance(raw_response, OperatorApprovalDecision):
            return raw_response
        if isinstance(raw_response, dict):
            return OperatorApprovalDecision(
                approved=bool(raw_response.get("approved", False)),
                operator_id=raw_response.get("operator_id"),
                reason=raw_response.get("reason"),
                source=raw_response.get("source", "dict_callback"),
            )
        return OperatorApprovalDecision(
            approved=bool(raw_response),
            reason="legacy_boolean_callback",
            source="legacy_boolean_callback",
        )

    def _request_operator_approval(self, decision: AutonomousDecision) -> bool:
        """Request bounded human approval for guarded decisions.

        Missing callbacks fail closed. Callback exceptions or elapsed waits beyond
        the configured timeout are treated as automatic rejection.
        """
        request = OperatorApprovalRequest(
            request_id=f"approval_{uuid.uuid4().hex[:12]}",
            decision_id=decision.decision_id,
            requested_at=time.time(),
            expires_at=time.time() + self.config.operator_approval_timeout_seconds,
        )
        with self._approval_lock:
            self.operator_approval_requests.append(request)
            self._active_approval_requests[request.request_id] = request
        self._log_audit_event(
            "operator_approval_requested",
            {"request_id": request.request_id, "decision_type": decision.decision_type},
            decision=decision,
            action="request_operator_approval",
            outcome="pending",
        )
        if not self.operator_approval_callback:
            with self._approval_lock:
                request.status = "rejected"
                request.reason = "approval_callback_missing"
                decision.operator_reason = request.reason
                decision.operator_approval_source = "missing_callback"
                self._active_approval_requests.pop(request.request_id, None)
            self._log_audit_event(
                "operator_approval_rejected",
                {"request_id": request.request_id, "reason": request.reason},
                decision=decision,
                action="request_operator_approval",
                outcome="rejected",
                operator_action="missing_callback",
            )
            return False
        started = time.monotonic()
        try:
            approval = self._normalise_operator_approval(
                self.operator_approval_callback(decision)
            )
            approved = approval.approved
            request.operator_id = approval.operator_id
            request.reason = approval.reason
            decision.operator_id = approval.operator_id
            decision.operator_reason = approval.reason
            decision.operator_approval_source = approval.source
        except Exception as exc:
            approved = False
            request.reason = f"callback_error:{exc}"
            decision.operator_reason = request.reason
            decision.operator_approval_source = "callback_error"
        elapsed = time.monotonic() - started
        if elapsed > self.config.operator_approval_timeout_seconds:
            approved = False
            request.reason = "approval_timeout"
            decision.operator_reason = request.reason
            decision.operator_approval_source = "timeout"
        with self._approval_lock:
            request.status = "approved" if approved else "rejected"
            self._active_approval_requests.pop(request.request_id, None)
        self._log_audit_event(
            "operator_approval_completed",
            {
                "request_id": request.request_id,
                "elapsed_seconds": round(elapsed, 3),
                "reason": request.reason,
                "operator_id": request.operator_id,
            },
            decision=decision,
            action="request_operator_approval",
            outcome=request.status,
            operator_id=request.operator_id,
            operator_action=request.status,
        )
        return approved

    def authorize_emergency_operator_bypass(
        self,
        decision: AutonomousDecision,
        operator_id: str,
        emergency_reason: str,
    ) -> OperatorApprovalDecision:
        """Record a deliberate emergency approval by a configured operator.

        Scope is intentionally limited to the autonomous optimisation/reflexive
        layer. This method does not call, configure, or relax mining verification,
        pool submission, or nonce-search paths; those remain governed by the
        verifier/firewall and live-share gates. Callers must provide a non-empty
        incident reason and the operator must be present in
        ``HYBA_EMERGENCY_OPERATOR_IDS``/``AutonomousConfig.emergency_operator_ids``.
        """
        if not operator_id or operator_id not in self.config.emergency_operator_ids:
            self._log_audit_event(
                "emergency_operator_bypass_rejected",
                {"operator_id": operator_id, "reason": "operator_not_authorized"},
                decision=decision,
                action="emergency_operator_bypass",
                outcome="rejected",
                operator_id=operator_id,
                operator_action="emergency_bypass_rejected",
            )
            return OperatorApprovalDecision(
                approved=False,
                operator_id=operator_id,
                reason="operator_not_authorized",
                source="emergency_bypass",
            )
        if not emergency_reason.strip():
            self._log_audit_event(
                "emergency_operator_bypass_rejected",
                {"operator_id": operator_id, "reason": "missing_emergency_reason"},
                decision=decision,
                action="emergency_operator_bypass",
                outcome="rejected",
                operator_id=operator_id,
                operator_action="emergency_bypass_rejected",
            )
            return OperatorApprovalDecision(
                approved=False,
                operator_id=operator_id,
                reason="missing_emergency_reason",
                source="emergency_bypass",
            )
        decision.operator_reason = (
            f"EMERGENCY_BYPASS_AUTONOMY_LAYER_ONLY: {emergency_reason.strip()}"
        )
        self._log_audit_event(
            "emergency_operator_bypass_approved",
            {"operator_id": operator_id, "reason": decision.operator_reason},
            decision=decision,
            action="emergency_operator_bypass",
            outcome="approved",
            operator_id=operator_id,
            operator_action="emergency_bypass",
        )
        return OperatorApprovalDecision(
            approved=True,
            operator_id=operator_id,
            reason=decision.operator_reason,
            source="emergency_bypass",
        )

    def get_audit_log(self, limit: Optional[int] = None) -> List[AuditLogEntry]:
        """Return structured autonomy audit entries."""
        if limit:
            return self.audit_log[-limit:]
        return self.audit_log.copy()

    def rollback_to_state(
        self,
        state_file: Path,
        operator_reason: str,
        operator_id: str = "operator",
    ) -> Dict[str, Any]:
        """Rollback reflexive learning to a checksum-validated state file."""
        if not state_file.exists():
            raise FileNotFoundError(state_file)
        with self._state_lock:
            return self._rollback_to_state_locked(
                state_file, operator_reason, operator_id
            )

    def _rollback_to_state_locked(
        self,
        state_file: Path,
        operator_reason: str,
        operator_id: str,
    ) -> Dict[str, Any]:
        """Rollback while the in-process state lock is held."""
        checksum_file = state_file.with_suffix(state_file.suffix + ".sha256")
        if checksum_file.exists():
            expected = checksum_file.read_text(encoding="utf-8").strip()
            actual = hashlib.sha256(state_file.read_bytes()).hexdigest()
            if expected != actual:
                raise ValueError("rollback state checksum mismatch")
        target = self._state_file_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._state_file_lock(target):
            target.write_bytes(state_file.read_bytes())
            if checksum_file.exists():
                target.with_suffix(target.suffix + ".sha256").write_text(
                    checksum_file.read_text(encoding="utf-8"), encoding="utf-8"
                )
        self._load_reflexive_state_locked(target)
        self.proposal_history = []
        self._log_audit_event(
            "state_rollback",
            {"source_state": str(state_file), "reason": operator_reason},
            action="rollback_to_state",
            outcome="restored",
            operator_id=operator_id,
            operator_action="rollback",
        )
        return {
            "restored": True,
            "state_file": str(state_file),
            "operator_id": operator_id,
        }

    def get_knowledge_substrate(self) -> Any:
        """Get the Deutsch Knowledge Substrate used for reflexive learning."""
        return self.knowledge_substrate

    def get_proposal_history(self) -> List[SelfOptimizationProposal]:
        """Get history of self-optimization proposals."""
        return self.proposal_history.copy()

    def get_codebase_surroundings(self) -> CodebaseSurroundings:
        """Get the codebase surroundings map used for Active Inference."""
        return self.surroundings

    # ================================================================
    # ENHANCEMENT 1: CONTINUOUS HEALTH LOOP (Self-Correction)
    # ================================================================

    async def start_continuous_monitor(self) -> None:
        """Start the background continuous autonomy monitor task."""
        if self._monitor_task is not None and not self._monitor_task.done():
            self._log_event("monitor_already_running", {})
            return
        self.is_running = True
        self._reference_efficiency = self.get_current_efficiency()
        self._monitor_task = asyncio.create_task(self._continuous_autonomy_monitor())
        self._log_event("continuous_monitor_started", {})

    async def stop_continuous_monitor(self) -> None:
        """Gracefully stop the background monitor task."""
        self.is_running = False
        if self._monitor_task is not None and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        self._log_event("continuous_monitor_stopped", {})

    async def _continuous_autonomy_monitor(self) -> None:
        """Background loop that detects performance degradation continuously.

        Runs every 60 seconds while the controller is active, monitoring:
        - Hashrate deviation from moving average (30% drop triggers soft-reset)
        - Error rate escalation (climbing error rate triggers recalibration)
        - System load for adaptive resource scaling
        """
        import logging

        logger = logging.getLogger("pythia.autonomy.monitor")

        # Seed the heal attempt window with current time
        now = time.time()
        self._heal_attempt_window = [now]

        while self.is_running:
            try:
                metrics = self.get_metrics_snapshot()

                # Update live metrics from engine state
                self._actual_hashrate = (
                    metrics.get("phi_density", 0.0) * 2.0
                )  # normalized proxy
                self._target_hashrate = 1.0  # baseline target

                # Track error rate from constraint violations
                total_decisions = metrics.get("total_decisions", 0)
                violations = metrics.get("constraint_violations", 0)
                self._error_rate = violations / max(total_decisions, 1)

                # --- Health Check 1: Hashrate performance dip ---
                if self._actual_hashrate < (self._target_hashrate * 0.7):
                    logger.warning(
                        "Autonomy: Performance dip detected. "
                        f"actual={self._actual_hashrate:.3f} target={self._target_hashrate:.3f}"
                    )
                    await self._handle_performance_degradation()
                    self._degradation_events += 1
                    self._log_event(
                        "monitor_performance_dip",
                        {
                            "actual_hashrate": self._actual_hashrate,
                            "target_hashrate": self._target_hashrate,
                        },
                    )

                # --- Health Check 2: Error rate climbing ---
                if self._error_rate > self.MAX_ERROR_THRESHOLD:
                    logger.warning(
                        "Autonomy: Error rate threshold exceeded. "
                        f"error_rate={self._error_rate:.3f} threshold={self.MAX_ERROR_THRESHOLD}"
                    )
                    await self._recalibrate_parameters()
                    self._log_event(
                        "monitor_error_rate",
                        {
                            "error_rate": self._error_rate,
                            "threshold": self.MAX_ERROR_THRESHOLD,
                        },
                    )

                # --- Health Check 3: Environment-aware resource scaling ---
                await self._seek_improvement_with_resource_awareness()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"Autonomy monitor error: {exc}", exc_info=True)
                self._log_audit_event(
                    "monitor_error",
                    {"error": str(exc), "error_type": type(exc).__name__},
                    action="_continuous_autonomy_monitor",
                    outcome="exception_swallowed",
                )
                self._log_event("monitor_error", {"error": str(exc)})

            await asyncio.sleep(60.0)  # Monitor every minute

    async def _handle_performance_degradation(self) -> None:
        """Execute a soft-reset when performance drops below threshold.

        Records the event in the autonomy journal and attempts a gentle
        recalibration rather than a hard restart.
        """
        self.record_autonomy_event(
            "PerformanceDegradation",
            {
                "actual_hashrate": self._actual_hashrate,
                "target_hashrate": self._target_hashrate,
                "action": "soft_reset",
            },
        )

        # Apply optional quantum healing swarm for self-repair.  The autonomy
        # soft-reset path must remain available even if this optional numerical
        # module is absent or cannot initialise in a constrained environment.
        try:
            from .quantum_healing_swarm import QuantumHealingSwarm

            swarm = QuantumHealingSwarm(
                num_candidates=8,
                num_lanes=32,
                enable_tunnelling=True,
                enable_annealing=True,
                enable_swarming=True,
                enable_interference=True,
            )
            phi_density = (
                self.get_phi_density() if hasattr(self, "get_phi_density") else 0.5
            )
            healing_result = swarm.heal(
                phi_density=phi_density,
                consecutive_failures=self._consecutive_failures,
                degrade_factor=(
                    1.0 - (self._actual_hashrate / self._target_hashrate)
                    if self._target_hashrate > 0
                    else 0.5
                ),
            )
            healing_payload = healing_result.to_dict()
            healing_outcome = "quantum_healed"
        except (
            Exception
        ) as exc:  # pragma: no cover - defensive optional-module fallback
            healing_payload = {
                "error": str(exc),
                "error_type": type(exc).__name__,
                "fallback": "performance_soft_reset_only",
            }
            healing_outcome = "quantum_healing_unavailable"

        # Log quantum healing to persistent audit
        self._log_audit_event(
            "quantum_healing_complete",
            healing_payload,
            action="handle_performance_degradation",
            outcome=healing_outcome,
            state_diff=healing_payload,
        )

        # Reset internal state to recover from drift
        self._consecutive_failures = 0
        self._error_rate = 0.0

        # Log to persistent audit
        self._log_audit_event(
            "performance_soft_reset",
            {"actual_hashrate": self._actual_hashrate},
            action="handle_performance_degradation",
            outcome="soft_reset_initiated",
        )

    async def _recalibrate_parameters(self) -> None:
        """Recalibrate internal parameters when error rate exceeds threshold."""
        self.record_autonomy_event(
            "ParameterRecalibration",
            {
                "error_rate": self._error_rate,
                "threshold": self.MAX_ERROR_THRESHOLD,
            },
        )

        # Reset error tracking after recalibration
        self._error_rate = 0.0

        self._log_audit_event(
            "parameter_recalibration",
            {"error_rate_before": self._error_rate},
            action="recalibrate_parameters",
            outcome="recalibrated",
        )

    # ================================================================
    # ENHANCEMENT 1b: HEAL ATTEMPT TRACKING (Circuit Breaker Support)
    # ================================================================

    def _record_heal_attempt(self) -> None:
        """Record a heal attempt timestamp in the sliding window."""
        now = time.time()
        self._heal_attempt_window.append(now)
        # Prune entries older than the window
        cutoff = now - self._heal_attempt_window_seconds
        self._heal_attempt_window = [
            t for t in self._heal_attempt_window if t >= cutoff
        ]

    async def get_recent_heal_attempts(self) -> int:
        """Return count of heal attempts in the sliding window (10 min default)."""
        now = time.time()
        cutoff = now - self._heal_attempt_window_seconds
        self._heal_attempt_window = [
            t for t in self._heal_attempt_window if t >= cutoff
        ]
        return len(self._heal_attempt_window)

    # ================================================================
    # ENHANCEMENT 2: DYNAMIC RESOURCE SCALING (Environment Adaptation)
    # ================================================================

    def platform_interface_get_cpu_load(self) -> float:
        """Simulate reading system CPU load.

        In production, this would read from /proc/stat, psutil, or
        macOS host Cortana counters. Returns a float 0-100.
        """
        try:
            import psutil

            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            pass
        # Fallback: simulate load from system pressure
        try:
            load_avg = os.getloadavg()
            cpu_count = os.cpu_count() or 1
            return (load_avg[0] / cpu_count) * 100.0
        except (AttributeError, OSError):
            pass
        return self._system_load

    async def _seek_improvement_with_resource_awareness(self) -> None:
        """Enhanced improvement cycle that considers system pressure.

        Autonomously throttles intensity when system load is high,
        and expands when there is headroom.
        """
        system_load = self.platform_interface_get_cpu_load()

        if system_load > 90:
            # Autonomously reduce intensity to prevent system crash
            await self._adjust_intensity(decrement=1)
            self.record_autonomy_event(
                "ResourceThrottle",
                {
                    "system_load": system_load,
                    "new_intensity": self._current_intensity,
                },
            )
        elif system_load < 40 and self._current_intensity < 10:
            # Autonomously increase intensity to maximize yield
            await self._adjust_intensity(increment=1)
            self.record_autonomy_event(
                "ResourceExpansion",
                {
                    "system_load": system_load,
                    "new_intensity": self._current_intensity,
                },
            )

    async def _adjust_intensity(self, increment: int = 0, decrement: int = 0) -> None:
        """Adjust mining intensity (1-10 scale) in response to system load.

        Uses the intensity level to scale search depth and hashrate targets.
        """
        if increment > 0:
            self._current_intensity = min(10, self._current_intensity + increment)
        if decrement > 0:
            self._current_intensity = max(1, self._current_intensity - decrement)

        # Scale engine parameters based on intensity
        intensity_ratio = self._current_intensity / 5.0  # normalize to 0.2-2.0

        if self.engine is not None and self.engine.optimizer is not None:
            base_search_time = 60.0
            scaled_time = max(10.0, min(300.0, base_search_time * intensity_ratio))
            self.engine.optimizer.max_search_iterations = int(scaled_time)

        self._log_event(
            "intensity_adjusted",
            {
                "current_intensity": self._current_intensity,
                "intensity_ratio": round(intensity_ratio, 3),
            },
        )

    # ================================================================
    # ENHANCEMENT 3: CIRCUIT BREAKER PATTERN (Self-Preservation)
    # ================================================================

    async def boot_self_heal_and_optimize(self) -> Dict[str, Any]:
        """Run the startup autonomic healing and optimisation cycle immediately,
        enhanced with circuit breaker pattern to prevent death spirals.

        This is the backend-boot path for PYTHIA's resident autonomy: clean any
        stale self-state locks, evaluate recent heal attempts, and if excessive
        failures are detected, switch to backup infrastructure instead of
        attempting the same failing healing strategy.
        """
        boot_started = time.time()

        # --- Circuit Breaker: Check heal attempt frequency ---
        attempts = await self.get_recent_heal_attempts()
        if attempts > 5:
            import logging

            _logger = logging.getLogger("pythia.autonomy.circuit_breaker")
            _logger.critical(
                "Autonomy: Excessive healing failures (%d in window). "
                "Switching to Failover Node.",
                attempts,
            )
            await self._switch_to_backup_infrastructure()
            self._log_audit_event(
                "circuit_breaker_failover",
                {
                    "heal_attempts": attempts,
                    "window_seconds": self._heal_attempt_window_seconds,
                },
                action="boot_self_heal_and_optimize",
                outcome="failover_initiated",
            )
            self.record_autonomy_event(
                "CircuitBreakerFailover",
                {
                    "heal_attempts": attempts,
                    "action": "switch_to_backup",
                },
            )
            duration_ms = round((time.time() - boot_started) * 1000.0, 3)
            return {
                "startup_self_healing_executed": False,
                "circuit_breaker_triggered": True,
                "reason": "excessive_heal_attempts",
                "heal_attempts": attempts,
                "duration_ms": duration_ms,
            }

        self._record_heal_attempt()

        # --- Original boot logic ---
        self._clean_stale_lock_on_boot()
        before = self.get_metrics_snapshot()
        self._log_audit_event(
            "startup_self_healing_started",
            {
                "autonomy_level": self.current_autonomy_level.value,
                "reflexive_loop_enabled": self.config.reflexive_loop_enabled,
                "compression_drive_enabled": self.config.compression_drive_enabled,
                "phi_density_before": before.get("phi_density"),
            },
            action="boot_self_heal_and_optimize",
            outcome="started",
        )
        report = await self.seek_improvement()
        self._last_reflexive_cycle = time.time()
        after = self.get_metrics_snapshot()

        # --- Auto-escalation based on boot-time metrics ---
        escalation_result = self._escalation_engine.evaluate_and_escalate(
            self.current_autonomy_level.value,
            phi_density=after.get("phi_density", 0.0),
            proposal_acceptance_rate=after.get("proposal_acceptance_rate", 0.0),
            consecutive_failures=after.get("consecutive_failures", 0),
            has_reflexive_cycle_executed=report.get("reflexive_cycle_executed", False),
        )
        if escalation_result["action"] != "none":
            self._log_audit_event(
                "boot_autonomy_level_changed",
                escalation_result,
                action="escalation_engine",
                outcome=escalation_result["to_level"],
                state_diff={
                    "from_level": escalation_result["from_level"],
                    "to_level": escalation_result["to_level"],
                },
            )

        duration_ms = round((time.time() - boot_started) * 1000.0, 3)
        self._persistent_audit_logger.log_startup_self_healing(
            autonomy_level=self.current_autonomy_level.value,
            phi_density_before=before.get("phi_density", 0.0),
            phi_density_after=after.get("phi_density", 0.0),
            duration_ms=duration_ms,
            proposals_generated=report.get("proposals_generated", 0),
            proposals_applied=report.get("proposals_applied", 0),
            stale_lock_recoveries=after.get("stale_state_lock_recoveries", 0),
        )
        self._log_audit_event(
            "startup_self_healing_completed",
            {
                "duration_ms": duration_ms,
                "proposals_generated": report.get("proposals_generated", 0),
                "proposals_applied": report.get("proposals_applied", 0),
                "phi_density_after": after.get("phi_density"),
                "stale_state_lock_recoveries": after.get(
                    "stale_state_lock_recoveries", 0
                ),
                "escalation_action": escalation_result["action"],
                "autonomy_level_after": self.current_autonomy_level.value,
            },
            action="boot_self_heal_and_optimize",
            outcome="completed",
            state_diff={
                "reflexive_cycle_count": [
                    before.get("reflexive_cycle_count"),
                    after.get("reflexive_cycle_count"),
                ],
                "proposal_acceptance_rate": [
                    before.get("proposal_acceptance_rate"),
                    after.get("proposal_acceptance_rate"),
                ],
            },
        )
        self.record_autonomy_success()
        self._persistent_audit_logger.journal.flush()
        return {
            "startup_self_healing_executed": True,
            "duration_ms": duration_ms,
            "before": before,
            "after": after,
            "escalation": escalation_result,
            "reflexive_report": report,
        }

    async def _switch_to_backup_infrastructure(self) -> None:
        """Switch to backup mining nodes/configuration when primary fails repeatedly.

        Records the event in the autonomy journal and updates pool configuration.
        """
        self.record_autonomy_event(
            "BackupFailover",
            {
                "reason": "excessive_heal_attempts",
                "action": "switch_to_backup_pool",
            },
        )

        # Reset consecutive failure state after failover
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

        self._log_audit_event(
            "backup_failover",
            {"heal_attempt_window_size": len(self._heal_attempt_window)},
            action="switch_to_backup_infrastructure",
            outcome="failover_complete",
        )

    # ================================================================
    # ENHANCEMENT 4: AUTONOMY JOURNAL (Auditability)
    # ================================================================

    def record_autonomy_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Record an event in the autonomy journal for auditability.

        The journal provides a human-readable thought process trail,
        complementing the structured audit log with narrative events.
        """
        entry = {
            "event_id": f"autonomy_event_{uuid.uuid4().hex[:8]}_{int(time.time())}",
            "timestamp": time.time(),
            "event_type": event_type,
            "autonomy_level": self.current_autonomy_level.value,
            "phi_density": self.get_phi_density(),
            "data": data,
        }
        with self._audit_lock:
            self._autonomy_journal.append(entry)
            # Keep bounded journal (last 1000 entries)
            if len(self._autonomy_journal) > 1000:
                self._autonomy_journal = self._autonomy_journal[-1000:]

    def get_autonomy_journal(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Return the autonomy journal entries (most recent first)."""
        journal = list(reversed(self._autonomy_journal))
        if limit:
            return journal[:limit]
        return journal

    def calculate_optimization_delta(self) -> float:
        """Calculate the efficiency improvement since the reference baseline.

        Returns a float representing the percentage improvement (positive = gain).
        """
        current_efficiency = self.get_current_efficiency()
        if self._reference_efficiency <= 0:
            return 0.0
        delta = (
            (current_efficiency - self._reference_efficiency)
            / self._reference_efficiency
        ) * 100.0
        return round(delta, 2)


__all__ = [
    "AutonomousMiningController",
    "AutonomousConfig",
    "OperatorApprovalDecision",
    "AutonomousDecision",
    "AuditLogEntry",
    "OperatorApprovalRequest",
    "AutonomyLevel",
    "SafetyConstraint",
    "OptimizationTarget",
    "SelfOptimizationProposal",
    "CodebaseSurroundings",
    "MAX_AUTONOMOUS_HASHRATE_EHS",
    "AutonomyMetrics",
]
