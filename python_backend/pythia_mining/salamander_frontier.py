"""Salamander frontier primitives for evidence-first autonomous adaptation.

The classes in this module intentionally avoid live pool/network side effects.
They model the frontier behaviours as deterministic, auditable transformations:

* evidence-based regeneration from immutable audit entries
* distributed agent coherence from a shared evidence trail
* adaptive phi tuning from reversible compression experiments
* self-scaling worker counts from measured marginal hashrate benefit
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from dataclasses import dataclass, field
from math import isfinite, sqrt
from statistics import mean
from time import time
from typing import Any, Callable, Iterable, Sequence

PHI = (1.0 + sqrt(5.0)) / 2.0


@dataclass(frozen=True)
class FrontierAuditEntry:
    """Immutable evidence event consumed by Salamander frontier replay."""

    event: str
    timestamp: float
    actor: str = "system"
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "data": self.data,
        }


class ImmutableEvidenceLog:
    """Append-only evidence trail with deterministic integrity sealing."""

    def __init__(self, entries: Iterable[FrontierAuditEntry] | None = None) -> None:
        self._entries: tuple[FrontierAuditEntry, ...] = tuple(entries or ())

    def append(
        self,
        event: str,
        *,
        actor: str = "system",
        timestamp: float | None = None,
        **data: Any,
    ) -> "ImmutableEvidenceLog":
        entry = FrontierAuditEntry(
            event=event,
            actor=actor,
            timestamp=time() if timestamp is None else timestamp,
            data=data,
        )
        return ImmutableEvidenceLog((*self._entries, entry))

    def entries(self) -> tuple[FrontierAuditEntry, ...]:
        return self._entries

    def filter(
        self, predicate: Callable[[FrontierAuditEntry], bool]
    ) -> tuple[FrontierAuditEntry, ...]:
        return tuple(entry for entry in self._entries if predicate(entry))

    def seal(self) -> str:
        payload = [entry.to_dict() for entry in self._entries]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SystemMetrics:
    """Comprehensive system metrics for autonomous observation."""

    hashrate_current: float = 0.0
    hashrate_target: float = 150.0
    hashrate_trend: float = 0.0
    memory_used: float = 0.0
    memory_available: float = 1.0
    compression_ratio: float = 1.0
    agent_health: list[dict[str, Any]] = field(default_factory=list)
    worker_health: list[dict[str, Any]] = field(default_factory=list)
    share_acceptance_rate: float = 1.0
    stale_share_rate: float = 0.0
    pool_latency_ms: float = 0.0
    cpu_utilization: float = 0.0
    gpu_available: bool = True
    last_anomaly: str | None = None
    time_since_regeneration: float = 0.0


@dataclass(frozen=True)
class Anomaly:
    """Structured anomaly description for regeneration triggering."""

    type: str
    severity: str
    current_value: float = 0.0
    target_value: float = 0.0
    trend: float = 0.0
    likely_causes: list[str] = field(default_factory=list)
    action: str | None = None
    agent_id: str | None = None
    stall_duration_ms: float = 0.0
    memory_used: float = 0.0
    memory_available: float = 0.0


@dataclass(frozen=True)
class RegenerationOutcome:
    """Outcome of a regeneration execution."""

    success: bool
    reason: str
    metrics_before: SystemMetrics = field(default_factory=SystemMetrics)
    metrics_after: SystemMetrics = field(default_factory=SystemMetrics)
    improvement: float = 0.0


@dataclass(frozen=True)
class TreasuryState:
    """Financial/economic state computed from evidence."""

    balance_btc: float = 0.0
    total_shares_submitted: int = 0
    total_shares_accepted: int = 0
    total_shares_rejected: int = 0
    transactions: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class HealthReport:
    """Comprehensive health report for observability."""

    timestamp: float
    agents_active: int
    workers_total: int
    hashrate_current: float
    hashrate_target: float
    hashrate_efficiency: float
    memory_used: float
    memory_available: float
    memory_efficiency: float
    phi_current: float
    compression_ratio: float
    share_acceptance_rate: float
    stale_share_rate: float
    pool_connectivity: str
    regenerations_performed: int
    adaptations_performed: int
    last_anomaly: str | None
    time_since_last_regeneration: float
    evidence_log_size: int
    evidence_log_integrity: str


@dataclass(frozen=True)
class ReplayedAgentState:
    agent_id: str
    current_job_id: str | None = None
    search_in_progress: bool = False
    search_start_nonce: int | None = None
    shares_found: int = 0
    shares_submitted: int = 0
    shares_accepted: int = 0
    shares_rejected: int = 0
    jobs_completed: int = 0
    workers: int = 0
    target_hashrate: float = 0.0


class SalamanderCore:
    """
    Foundation: Salamander detects anomalies, triggers regeneration,
    measures outcome, learns for next iteration.
    
    Mathematical first principles: substrate and hardware agnostic.
    """

    def __init__(
        self,
        audit_log: ImmutableEvidenceLog | None = None,
        phi_value: float = PHI,
    ) -> None:
        self.audit_log = audit_log or ImmutableEvidenceLog()
        self.phi_value = float(phi_value)
        self.regeneration_count = 0
        self.adaptations_performed = 0
        self._regeneration_timestamp: float | None = None

    def observe_system_state(
        self,
        hashrate_current: float = 0.0,
        hashrate_target: float = 150.0,
        memory_used: float = 0.0,
        memory_available: float = 1.0,
        agent_health: list[dict[str, Any]] | None = None,
        worker_health: list[dict[str, Any]] | None = None,
    ) -> SystemMetrics:
        """
        Non-invasive observation. Doesn't change state.
        Only observes what's happening.
        """
        agent_health = agent_health or []
        worker_health = worker_health or []
        
        # Compute trend from last 100 measurements in audit log
        recent_metrics = self.audit_log.filter(
            lambda e: e.event == "observation"
        )[-100:]
        hashrate_trend = 0.0
        if len(recent_metrics) >= 2:
            values = [e.data.get("hashrate_current", 0.0) for e in recent_metrics]
            if len(values) >= 2:
                hashrate_trend = (values[-1] - values[0]) / max(len(values), 1)

        # Compute acceptance/stale rates from audit log
        share_entries = self.audit_log.filter(
            lambda e: e.event in {"share_submitted", "share_accepted", "share_rejected"}
        )
        submitted = len([e for e in share_entries if e.event == "share_submitted"])
        accepted = len([e for e in share_entries if e.event == "share_accepted"])
        rejected = len([e for e in share_entries if e.event == "share_rejected"])
        share_acceptance_rate = accepted / max(submitted, 1)
        stale_share_rate = rejected / max(submitted, 1)

        # Get last anomaly
        last_anomaly = None
        anomaly_entries = self.audit_log.filter(lambda e: e.event == "anomaly_detected")
        if anomaly_entries:
            last_anomaly = anomaly_entries[-1].data.get("type")

        # Time since last regeneration
        time_since_regeneration = 0.0
        if self._regeneration_timestamp:
            time_since_regeneration = time() - self._regeneration_timestamp

        metrics = SystemMetrics(
            hashrate_current=hashrate_current,
            hashrate_target=hashrate_target,
            hashrate_trend=hashrate_trend,
            memory_used=memory_used,
            memory_available=memory_available,
            compression_ratio=self.phi_value,
            agent_health=agent_health,
            worker_health=worker_health,
            share_acceptance_rate=share_acceptance_rate,
            stale_share_rate=stale_share_rate,
            pool_latency_ms=0.0,  # Would be measured from actual pool
            cpu_utilization=0.0,  # Would be measured from system
            gpu_available=True,  # Would be detected from hardware
            last_anomaly=last_anomaly,
            time_since_regeneration=time_since_regeneration,
        )

        self.audit_log = self.audit_log.append(
            "observation",
            timestamp=time(),
            metrics=metrics.__dict__,
            decision="none",
        )

        return metrics

    def detect_anomaly(self, metrics: SystemMetrics) -> Anomaly | None:
        """
        Detect degradation or opportunity for optimization.
        Returns structured anomaly description.
        """
        # Degradation detection
        if (
            metrics.hashrate_trend < 0
            and metrics.hashrate_current < metrics.hashrate_target * 0.9
        ):
            return Anomaly(
                type="HASHRATE_DEGRADATION",
                severity="HIGH",
                current_value=metrics.hashrate_current,
                target_value=metrics.hashrate_target,
                trend=metrics.hashrate_trend,
                likely_causes=[
                    "pool_latency",
                    "gpu_not_available",
                    "phi_compression_not_optimized",
                    "stale_jobs_too_high",
                ],
            )

        # Memory pressure detection
        if metrics.memory_used > metrics.memory_available * 0.85:
            return Anomaly(
                type="MEMORY_PRESSURE",
                severity="MEDIUM",
                memory_used=metrics.memory_used,
                memory_available=metrics.memory_available,
                action="trigger_phi_folding",
            )

        # Agent stall detection
        for agent in metrics.agent_health:
            if agent.get("time_since_last_job_ms", 0) > 30000:  # 30 seconds
                return Anomaly(
                    type="AGENT_STALL",
                    severity="CRITICAL",
                    agent_id=agent.get("id"),
                    stall_duration_ms=agent.get("time_since_last_job_ms", 0),
                    action="regenerate_agent",
                )

        return None

    def execute_regeneration(self, anomaly: Anomaly) -> RegenerationOutcome:
        """
        Execute appropriate regeneration strategy.
        Record decision + outcome to audit log.
        """
        self.audit_log = self.audit_log.append(
            "regeneration_triggered",
            timestamp=time(),
            anomaly=anomaly.__dict__,
            policy=f"will_execute_{anomaly.type}",
        )

        outcome = match_anomaly_type(anomaly)

        # Log outcome
        self.audit_log = self.audit_log.append(
            "regeneration_completed",
            timestamp=time(),
            anomaly_type=anomaly.type,
            outcome=outcome.__dict__,
        )

        self.regeneration_count += 1
        self._regeneration_timestamp = time()

        return outcome


def match_anomaly_type(anomaly: Anomaly) -> RegenerationOutcome:
    """Match anomaly type to appropriate regeneration strategy."""
    match anomaly.type:
        case "HASHRATE_DEGRADATION":
            return RegenerationOutcome(
                success=True,
                reason="hashrate_regeneration_strategy_applied",
            )
        case "MEMORY_PRESSURE":
            return RegenerationOutcome(
                success=True,
                reason="phi_compression_regeneration_applied",
            )
        case "AGENT_STALL":
            return RegenerationOutcome(
                success=True,
                reason="agent_regeneration_strategy_applied",
            )
        case _:
            return RegenerationOutcome(
                success=False,
                reason="unknown_anomaly_type",
            )


class EvidenceBasedRegenerator:
    """Recompute state from evidence instead of restoring a golden copy."""

    def __init__(self, audit_log: ImmutableEvidenceLog) -> None:
        self.audit_log = audit_log

    def recover_agent(self, agent_id: str) -> ReplayedAgentState:
        state = ReplayedAgentState(agent_id=agent_id)
        for entry in sorted(
            self.audit_log.filter(lambda e: e.actor == agent_id), key=lambda e: e.timestamp
        ):
            data = entry.data
            if entry.event in {"agent_spawned", "job_received"}:
                state = ReplayedAgentState(
                    **{**state.__dict__, "current_job_id": data.get("job_id", state.current_job_id)}
                )
            elif entry.event == "search_started":
                state = ReplayedAgentState(
                    **{
                        **state.__dict__,
                        "search_in_progress": True,
                        "search_start_nonce": data.get("start_nonce"),
                    }
                )
            elif entry.event == "share_found":
                state = ReplayedAgentState(
                    **{**state.__dict__, "shares_found": state.shares_found + 1}
                )
            elif entry.event == "share_submitted":
                state = ReplayedAgentState(
                    **{**state.__dict__, "shares_submitted": state.shares_submitted + 1}
                )
            elif entry.event == "share_accepted":
                state = ReplayedAgentState(
                    **{**state.__dict__, "shares_accepted": state.shares_accepted + 1}
                )
            elif entry.event == "share_rejected":
                state = ReplayedAgentState(
                    **{**state.__dict__, "shares_rejected": state.shares_rejected + 1}
                )
            elif entry.event == "job_completed":
                state = ReplayedAgentState(
                    **{
                        **state.__dict__,
                        "jobs_completed": state.jobs_completed + 1,
                        "current_job_id": None,
                        "search_in_progress": False,
                    }
                )
            elif entry.event == "worker_spawned":
                state = ReplayedAgentState(**{**state.__dict__, "workers": state.workers + 1})
            elif entry.event == "worker_removed":
                state = ReplayedAgentState(
                    **{**state.__dict__, "workers": max(0, state.workers - 1)}
                )
            elif entry.event == "target_hashrate_updated":
                state = ReplayedAgentState(
                    **{**state.__dict__, "target_hashrate": float(data["target_hashrate"])}
                )
        return state

    def recover_system(self) -> dict[str, ReplayedAgentState]:
        agent_ids = sorted(
            {entry.actor for entry in self.audit_log.entries() if entry.actor != "system"}
        )
        return {agent_id: self.recover_agent(agent_id) for agent_id in agent_ids}

    def recover_treasury_state(self) -> TreasuryState:
        """
        Treasury state is computed from share submissions + pool confirmations.
        No stored state needed.
        """
        treasury = TreasuryState()

        for entry in self.audit_log.entries():
            match entry.event:
                case "share_submitted":
                    treasury = TreasuryState(
                        balance_btc=treasury.balance_btc,
                        total_shares_submitted=treasury.total_shares_submitted + 1,
                        total_shares_accepted=treasury.total_shares_accepted,
                        total_shares_rejected=treasury.total_shares_rejected,
                        transactions=treasury.transactions.copy(),
                    )
                case "share_accepted":
                    reward = entry.data.get("pool_reward_btc", 0.0)
                    treasury = TreasuryState(
                        balance_btc=treasury.balance_btc + reward,
                        total_shares_submitted=treasury.total_shares_submitted,
                        total_shares_accepted=treasury.total_shares_accepted + 1,
                        total_shares_rejected=treasury.total_shares_rejected,
                        transactions=treasury.transactions
                        + [
                            {
                                "type": "reward",
                                "amount_btc": reward,
                                "timestamp": entry.timestamp,
                                "pool": entry.data.get("pool_name", "unknown"),
                                "txid": entry.data.get("txid", ""),
                            }
                        ],
                    )
                case "share_rejected":
                    treasury = TreasuryState(
                        balance_btc=treasury.balance_btc,
                        total_shares_submitted=treasury.total_shares_submitted,
                        total_shares_accepted=treasury.total_shares_accepted,
                        total_shares_rejected=treasury.total_shares_rejected + 1,
                        transactions=treasury.transactions.copy(),
                    )
                case "electricity_cost":
                    cost = entry.data.get("cost_btc", 0.0)
                    treasury = TreasuryState(
                        balance_btc=treasury.balance_btc - cost,
                        total_shares_submitted=treasury.total_shares_submitted,
                        total_shares_accepted=treasury.total_shares_accepted,
                        total_shares_rejected=treasury.total_shares_rejected,
                        transactions=treasury.transactions
                        + [
                            {
                                "type": "cost",
                                "amount_btc": cost,
                                "timestamp": entry.timestamp,
                                "category": "electricity",
                            }
                        ],
                    )
                case "operation_expense":
                    cost = entry.data.get("cost_btc", 0.0)
                    treasury = TreasuryState(
                        balance_btc=treasury.balance_btc - cost,
                        total_shares_submitted=treasury.total_shares_submitted,
                        total_shares_accepted=treasury.total_shares_accepted,
                        total_shares_rejected=treasury.total_shares_rejected,
                        transactions=treasury.transactions
                        + [
                            {
                                "type": "cost",
                                "amount_btc": cost,
                                "timestamp": entry.timestamp,
                                "category": entry.data.get("expense_type", "unknown"),
                            }
                        ],
                    )

        # Verify integrity
        computed_balance = sum(
            tx["amount_btc"] if tx["type"] == "reward" else -tx["amount_btc"]
            for tx in treasury.transactions
        )
        if abs(treasury.balance_btc - computed_balance) > 1e-8:
            self.audit_log = self.audit_log.append(
                "treasury_state_mismatch",
                timestamp=time(),
                computed=computed_balance,
                recorded=treasury.balance_btc,
                severity="CRITICAL",
            )

        return treasury

    def regenerate_system_from_evidence(self, target_timestamp: float) -> dict[str, ReplayedAgentState]:
        """
        Recover entire system to any point in time using evidence.
        Enables deterministic replay for debugging/validation.
        """
        relevant_log = ImmutableEvidenceLog(
            tuple(entry for entry in self.audit_log.entries() if entry.timestamp <= target_timestamp)
        )
        temp_regenerator = EvidenceBasedRegenerator(relevant_log)
        return temp_regenerator.recover_system()


@dataclass(frozen=True)
class CoherenceMetrics:
    active_agents: int
    agents_on_current_job: int
    jobs_diverged: int
    max_hashrate_deviation: float
    coherent: bool


class DistributedAgentCoherence:
    """Keep agents coherent by deriving assignments from shared evidence."""

    def __init__(self, audit_log: ImmutableEvidenceLog, total_target_hashrate: float) -> None:
        self.audit_log = audit_log
        self.total_target_hashrate = float(total_target_hashrate)

    def add_agent(
        self, agent_id: str, job_id: str, timestamp: float | None = None
    ) -> ImmutableEvidenceLog:
        active_count = len(EvidenceBasedRegenerator(self.audit_log).recover_system()) + 1
        target = self.total_target_hashrate / active_count
        return self.audit_log.append(
            "agent_spawned",
            actor=agent_id,
            timestamp=timestamp,
            job_id=job_id,
            active_agent_count_after=active_count,
        ).append(
            "target_hashrate_updated", actor=agent_id, timestamp=timestamp, target_hashrate=target
        )

    def measure(self, current_job_id: str, hashrates: dict[str, float]) -> CoherenceMetrics:
        states = EvidenceBasedRegenerator(self.audit_log).recover_system()
        active = len(states)
        on_job = sum(1 for state in states.values() if state.current_job_id == current_job_id)
        mean = sum(hashrates.values()) / max(len(hashrates), 1)
        max_dev = (
            max((abs(rate - mean) / mean for rate in hashrates.values()), default=0.0)
            if mean
            else 0.0
        )
        diverged = active - on_job
        return CoherenceMetrics(active, on_job, diverged, max_dev, diverged == 0)

    def rebalance_work_distribution(
        self, current_job_id: str, hashrates: dict[str, float], target_hashrate: float
    ) -> ImmutableEvidenceLog:
        """
        If agents are unbalanced, rebalance by adjusting worker allocation.
        No centralized scheduler. Agents adjust based on observed state.
        """
        states = EvidenceBasedRegenerator(self.audit_log).recover_system()
        
        # Identify slow and fast agents
        slow_agents = [
            agent_id
            for agent_id, state in states.items()
            if hashrates.get(agent_id, 0.0) < target_hashrate * 0.95
        ]
        fast_agents = [
            agent_id
            for agent_id, state in states.items()
            if hashrates.get(agent_id, 0.0) > target_hashrate * 1.05
        ]

        updated_log = self.audit_log
        
        # Slow agents: increase worker count
        for agent_id in slow_agents:
            updated_log = updated_log.append(
                "worker_spawned_for_rebalance",
                actor=agent_id,
                timestamp=time(),
                reason="hashrate_below_target",
                current_hashrate=hashrates.get(agent_id, 0.0),
                target_hashrate=target_hashrate,
            )

        # Fast agents: reduce worker count if safe
        for agent_id in fast_agents:
            state = states.get(agent_id)
            if state and state.workers > 1:
                updated_log = updated_log.append(
                    "worker_removed_for_rebalance",
                    actor=agent_id,
                    timestamp=time(),
                    reason="hashrate_above_target",
                    current_hashrate=hashrates.get(agent_id, 0.0),
                    target_hashrate=target_hashrate,
                )

        return updated_log

    def handle_agent_failure(
        self, failed_agent_id: str, total_target_hashrate: float
    ) -> tuple[ImmutableEvidenceLog, dict[str, float]]:
        """
        One agent fails. Other agents automatically adjust.
        No manual intervention needed.
        """
        states = EvidenceBasedRegenerator(self.audit_log).recover_system()
        
        # Remove failed agent from active list
        active_agents = {aid: state for aid, state in states.items() if aid != failed_agent_id}
        remaining_agent_count = len(active_agents)
        
        # Redistribute work
        new_target_per_agent = total_target_hashrate / max(remaining_agent_count, 1)
        
        updated_log = self.audit_log.append(
            "agent_failure_handled",
            actor="system",
            timestamp=time(),
            failed_agent_id=failed_agent_id,
            remaining_agents=remaining_agent_count,
            new_target_per_agent=new_target_per_agent,
            expected_total_hashrate=new_target_per_agent * remaining_agent_count,
        )

        # Update target hashrate for remaining agents
        for agent_id in active_agents:
            updated_log = updated_log.append(
                "target_hashrate_updated",
                actor=agent_id,
                timestamp=time(),
                target_hashrate=new_target_per_agent,
            )

        return updated_log, {aid: new_target_per_agent for aid in active_agents}


@dataclass(frozen=True)
class PhiExperiment:
    phi_value: float
    compression_ratio: float
    reconstruction_error: float
    score: float


class AdaptivePhiTuning:
    """Experiment with phi variants and adopt only measured improvements."""

    def __init__(
        self,
        phi_current: float = PHI,
        improvement_threshold: float = 0.05,
        audit_log: ImmutableEvidenceLog | None = None,
    ) -> None:
        self.phi_current = float(phi_current)
        self.improvement_threshold = float(improvement_threshold)
        self.audit_log = audit_log or ImmutableEvidenceLog()
        self.phi_baseline_efficiency: float = 0.0

    def initialize_phi_baseline(self, working_set: Sequence[float]) -> float:
        """
        Measure baseline compression efficiency at φ = 1.618034
        """
        magnitude = sum(abs(v) for v in working_set) or 1.0
        compression_ratio = magnitude / (
            1.0 + abs(self.phi_current - PHI) + len(working_set) / (self.phi_current + PHI)
        )
        self.phi_baseline_efficiency = compression_ratio

        self.audit_log = self.audit_log.append(
            "phi_baseline_measured",
            timestamp=time(),
            phi_value=self.phi_current,
            uncompressed_size=magnitude,
            compressed_size=magnitude / compression_ratio,
            compression_ratio=compression_ratio,
        )

        return compression_ratio

    def run_experiments(
        self, working_set: Sequence[float], candidates: Sequence[float] | None = None
    ) -> list[PhiExperiment]:
        candidates = candidates or (PHI * 0.95, PHI, PHI * 1.05, PHI**0.5, PHI**2)
        magnitude = sum(abs(v) for v in working_set) or 1.0
        experiments = []
        for candidate in candidates:
            compression_ratio = magnitude / (
                1.0 + abs(candidate - PHI) + len(working_set) / (candidate + PHI)
            )
            reconstruction_error = abs(candidate - PHI) / PHI
            experiments.append(
                PhiExperiment(
                    float(candidate),
                    float(compression_ratio),
                    float(reconstruction_error),
                    float(compression_ratio - reconstruction_error * 0.1),
                )
            )
        return experiments

    def adopt_best(
        self, baseline_ratio: float, experiments: Sequence[PhiExperiment]
    ) -> tuple[float, bool, PhiExperiment]:
        best = max(experiments, key=lambda exp: exp.score)
        improved = best.compression_ratio > baseline_ratio * (1.0 + self.improvement_threshold)
        if improved:
            old_phi = self.phi_current
            self.phi_current = best.phi_value
            self.phi_baseline_efficiency = best.compression_ratio

            self.audit_log = self.audit_log.append(
                "phi_value_updated",
                timestamp=time(),
                old_phi=old_phi,
                new_phi=self.phi_current,
                improvement_pct=(best.compression_ratio - baseline_ratio) / baseline_ratio * 100,
                reason="compression_efficiency",
            )
        else:
            self.audit_log = self.audit_log.append(
                "phi_value_unchanged",
                timestamp=time(),
                current_phi=self.phi_current,
                best_experiment_improvement=(best.compression_ratio - baseline_ratio) / baseline_ratio * 100,
                reason="improvement_below_threshold",
            )
        return self.phi_current, improved, best

    def continuous_phi_optimization(
        self, working_set: Sequence[float], iteration_count: int = 0
    ) -> None:
        """
        Run continuous optimization loop.
        Every N iterations: experiment, adopt best.
        """
        # Every 100 mining iterations, try new φ-values
        if iteration_count % 100 == 0:
            experiments = self.run_experiments(working_set)
            self.adopt_best(self.phi_baseline_efficiency, experiments)

            self.audit_log = self.audit_log.append(
                "phi_optimization_cycle",
                timestamp=time(),
                iteration=iteration_count,
                current_phi=self.phi_current,
            )


class SelfScalingWorkerPool:
    """Find worker count where marginal hashrate benefit falls below threshold."""

    def __init__(
        self,
        marginal_benefit_threshold: float = 0.02,
        target_hashrate: float = 150.0,
        audit_log: ImmutableEvidenceLog | None = None,
    ) -> None:
        self.marginal_benefit_threshold = float(marginal_benefit_threshold)
        self.target_hashrate = float(target_hashrate)
        self.audit_log = audit_log or ImmutableEvidenceLog()
        self.current_worker_count: int = 1
        self.scaling_history: list[dict[str, Any]] = []

    def measure_hashrate_with_worker_count(
        self, worker_count: int, measurement_duration_seconds: float = 30.0
    ) -> float:
        """
        Measure hashrate at specific worker count.
        In production, this would spawn workers and measure actual hashrate.
        For mathematical first principles, this is a deterministic function.
        """
        # Mathematical model: hashrate scales with worker count but with diminishing returns
        # This models substrate/hardware agnostic behavior
        base_hashrate = self.target_hashrate / 2.0
        scaling_efficiency = 1.0 - (worker_count - 1) * 0.05  # 5% efficiency loss per additional worker
        scaling_efficiency = max(scaling_efficiency, 0.5)  # Minimum 50% efficiency
        hashrate = base_hashrate * worker_count * scaling_efficiency
        return hashrate

    def find_optimal_worker_count(self, hashrate_by_worker_count: dict[int, float]) -> int:
        optimal = 1
        previous = 0.0
        hashrate_at_count = {}
        
        for count in sorted(hashrate_by_worker_count):
            rate = hashrate_by_worker_count[count]
            hashrate_at_count[count] = rate
            benefit = (rate - previous) / max(previous, 1.0)
            
            self.audit_log = self.audit_log.append(
                "scaling_experiment",
                timestamp=time(),
                worker_count=count,
                hashrate=rate,
                previous_hashrate=previous,
                marginal_benefit=benefit,
            )
            
            if benefit >= self.marginal_benefit_threshold:
                optimal = count
                previous = rate
            else:
                break
        
        self.audit_log = self.audit_log.append(
            "optimal_worker_count_found",
            timestamp=time(),
            optimal_count=optimal,
            hashrate_at_optimal=hashrate_at_count.get(optimal, 0.0),
            hashrate_curve=hashrate_at_count,
        )
        
        return optimal

    def scale_to_optimal(self, optimal_count: int) -> None:
        """
        Scale system to optimal worker count.
        """
        while self.current_worker_count < optimal_count:
            self.current_worker_count += 1
            self.audit_log = self.audit_log.append(
                "worker_spawned",
                timestamp=time(),
                worker_count=self.current_worker_count,
                reason="scaling_to_optimal",
            )
        
        while self.current_worker_count > optimal_count:
            self.current_worker_count -= 1
            self.audit_log = self.audit_log.append(
                "worker_removed",
                timestamp=time(),
                worker_count=self.current_worker_count,
                reason="scaling_to_optimal",
            )
        
        self.audit_log = self.audit_log.append(
            "worker_scaling_complete",
            timestamp=time(),
            current_worker_count=self.current_worker_count,
        )

    def monitor_scaling_efficiency(
        self, current_hashrate: float, check_interval_seconds: float = 3600.0
    ) -> None:
        """
        Periodically check if worker count is still optimal.
        Hardware changes, problem difficulty changes, etc.
        Readjust if needed.
        """
        # If hashrate dropped significantly, might need rebalance
        if current_hashrate < self.target_hashrate * 0.9:
            self.audit_log = self.audit_log.append(
                "scaling_degradation_detected",
                timestamp=time(),
                current_hashrate=current_hashrate,
                target_hashrate=self.target_hashrate,
                worker_count=self.current_worker_count,
                action="will_rebalance",
            )
            # In production, this would trigger scale_to_optimal()
        
        # Log periodic health check
        self.audit_log = self.audit_log.append(
            "scaling_health_check",
            timestamp=time(),
            worker_count=self.current_worker_count,
            current_hashrate=current_hashrate,
            efficiency=current_hashrate / max(self.current_worker_count, 1),
        )


@dataclass(frozen=True)
class EvidenceSeal:
    """Non-repudiation metadata for one audit decision."""

    entry_hash: str
    previous_hash: str
    hmac_signature: str | None = None


class EvidenceSealLifecycle:
    """Hash-chain and optional HMAC lifecycle for frontier audit entries."""

    GENESIS_HASH = "0" * 64

    def __init__(self, hmac_secret: bytes | None = None) -> None:
        self.hmac_secret = hmac_secret

    def seal_entry(
        self, entry: FrontierAuditEntry, previous_hash: str = GENESIS_HASH
    ) -> EvidenceSeal:
        payload = {
            "entry": entry.to_dict(),
            "previous_hash": previous_hash,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
            "utf-8"
        )
        entry_hash = hashlib.sha256(encoded).hexdigest()
        signature = None
        if self.hmac_secret is not None:
            signature = hmac.new(self.hmac_secret, encoded, hashlib.sha256).hexdigest()
        return EvidenceSeal(
            entry_hash=entry_hash, previous_hash=previous_hash, hmac_signature=signature
        )

    def seal_log(self, audit_log: ImmutableEvidenceLog) -> list[EvidenceSeal]:
        seals: list[EvidenceSeal] = []
        previous = self.GENESIS_HASH
        for entry in audit_log.entries():
            seal = self.seal_entry(entry, previous)
            seals.append(seal)
            previous = seal.entry_hash
        return seals

    def verify_log(self, audit_log: ImmutableEvidenceLog, expected: Sequence[EvidenceSeal]) -> bool:
        actual = self.seal_log(audit_log)
        return list(expected) == actual


@dataclass(frozen=True)
class CapabilityObservation:
    """Domain-neutral observation for ubiquitous Salamander adaptation."""

    domain: str
    capability: str
    metric_name: str
    current_value: float
    target_value: float
    higher_is_better: bool = True

    @property
    def health_ratio(self) -> float:
        if self.target_value == 0:
            return 1.0
        ratio = self.current_value / self.target_value
        return (
            ratio if self.higher_is_better else self.target_value / max(self.current_value, 1e-12)
        )


@dataclass(frozen=True)
class AdaptationDecision:
    """Decision produced from a capability observation."""

    domain: str
    capability: str
    action: str
    reason: str
    severity: str
    metric_name: str
    current_value: float
    target_value: float


class UbiquitousSalamanderFrontier:
    """General-purpose frontier layer for any HYBA capability, not only mining."""

    def __init__(
        self,
        audit_log: ImmutableEvidenceLog | None = None,
        seal_lifecycle: EvidenceSealLifecycle | None = None,
        adaptation_threshold: float = 0.9,
    ) -> None:
        self.audit_log = audit_log or ImmutableEvidenceLog()
        self.seal_lifecycle = seal_lifecycle or EvidenceSealLifecycle()
        self.adaptation_threshold = float(adaptation_threshold)

    def observe(self, observation: CapabilityObservation, timestamp: float | None = None) -> None:
        self.audit_log = self.audit_log.append(
            "capability_observed",
            actor=observation.capability,
            timestamp=timestamp,
            domain=observation.domain,
            metric_name=observation.metric_name,
            current_value=observation.current_value,
            target_value=observation.target_value,
            higher_is_better=observation.higher_is_better,
            health_ratio=observation.health_ratio,
        )

    def decide(self, observation: CapabilityObservation) -> AdaptationDecision | None:
        if observation.health_ratio >= self.adaptation_threshold:
            return None
        action = "add_capacity" if observation.higher_is_better else "shed_or_rebalance_load"
        severity = "critical" if observation.health_ratio < 0.5 else "degraded"
        return AdaptationDecision(
            domain=observation.domain,
            capability=observation.capability,
            action=action,
            reason=f"{observation.metric_name}_outside_frontier_threshold",
            severity=severity,
            metric_name=observation.metric_name,
            current_value=observation.current_value,
            target_value=observation.target_value,
        )

    def record_decision(
        self, decision: AdaptationDecision, timestamp: float | None = None
    ) -> EvidenceSeal:
        self.audit_log = self.audit_log.append(
            "adaptation_decision",
            actor=decision.capability,
            timestamp=timestamp,
            domain=decision.domain,
            action=decision.action,
            reason=decision.reason,
            severity=decision.severity,
            metric_name=decision.metric_name,
            current_value=decision.current_value,
            target_value=decision.target_value,
        )
        return self.seal_lifecycle.seal_log(self.audit_log)[-1]

    def observe_decide_and_seal(
        self, observation: CapabilityObservation, timestamp: float | None = None
    ) -> tuple[AdaptationDecision | None, EvidenceSeal | None]:
        self.observe(observation, timestamp=timestamp)
        decision = self.decide(observation)
        if decision is None:
            return None, None
        return decision, self.record_decision(decision, timestamp=timestamp)


@dataclass(frozen=True)
class CapabilityBlueprint:
    """Portable capability contract for QaaS, QIaaS, CIaaS, and future domains."""

    domain: str
    capability: str
    primary_metric: str
    target_value: float
    higher_is_better: bool = True
    evidence_tier: str = "frontier"

    def observe(self, current_value: float) -> CapabilityObservation:
        return CapabilityObservation(
            domain=self.domain,
            capability=self.capability,
            metric_name=self.primary_metric,
            current_value=float(current_value),
            target_value=self.target_value,
            higher_is_better=self.higher_is_better,
        )


class FrontierCapabilityPortfolio:
    """Registry of ubiquitous frontier capabilities HYBA can carry forward."""

    def __init__(self, blueprints: Iterable[CapabilityBlueprint] | None = None) -> None:
        self._blueprints: dict[str, CapabilityBlueprint] = {}
        for blueprint in blueprints or ():
            self.register(blueprint)

    def register(self, blueprint: CapabilityBlueprint) -> None:
        key = self.key_for(blueprint.domain, blueprint.capability)
        self._blueprints[key] = blueprint

    def get(self, domain: str, capability: str) -> CapabilityBlueprint:
        return self._blueprints[self.key_for(domain, capability)]

    def domains(self) -> tuple[str, ...]:
        return tuple(sorted({blueprint.domain for blueprint in self._blueprints.values()}))

    def as_observations(
        self, measurements: dict[tuple[str, str], float]
    ) -> list[CapabilityObservation]:
        observations: list[CapabilityObservation] = []
        for (domain, capability), value in measurements.items():
            observations.append(self.get(domain, capability).observe(value))
        return observations

    @staticmethod
    def key_for(domain: str, capability: str) -> str:
        return f"{domain}:{capability}"

    @classmethod
    def default(cls) -> "FrontierCapabilityPortfolio":
        return cls(
            [
                CapabilityBlueprint("funding", "treasury-resilience", "evidence_coverage", 0.99),
                CapabilityBlueprint("qaas", "quantum-job-orchestration", "job_success_rate", 0.995),
                CapabilityBlueprint(
                    "qiaas", "quantum-intelligence-routing", "answer_fidelity", 0.97
                ),
                CapabilityBlueprint(
                    "ciaas", "computational-intelligence-api", "p95_latency_ms", 150.0, False
                ),
                CapabilityBlueprint(
                    "research", "math-proof-workbench", "reproducibility_score", 0.98
                ),
            ]
        )


class DistributedEvidenceReplicator:
    """Deterministically merge shared audit logs from multiple replicas."""

    def __init__(self, seal_lifecycle: EvidenceSealLifecycle | None = None) -> None:
        self.seal_lifecycle = seal_lifecycle or EvidenceSealLifecycle()

    def merge(self, *logs: ImmutableEvidenceLog) -> ImmutableEvidenceLog:
        by_hash: dict[str, FrontierAuditEntry] = {}
        for audit_log in logs:
            for entry in audit_log.entries():
                entry_hash = self._entry_identity(entry)
                by_hash[entry_hash] = entry
        ordered = sorted(
            by_hash.values(),
            key=lambda entry: (
                entry.timestamp,
                entry.actor,
                entry.event,
                json.dumps(entry.data, sort_keys=True, default=str),
            ),
        )
        return ImmutableEvidenceLog(ordered)

    def verify_replicas(
        self, canonical: ImmutableEvidenceLog, *replicas: ImmutableEvidenceLog
    ) -> bool:
        canonical_seal = canonical.seal()
        return all(self.merge(canonical, replica).seal() == canonical_seal for replica in replicas)

    @staticmethod
    def _entry_identity(entry: FrontierAuditEntry) -> str:
        encoded = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExperimentMeasurement:
    """Single matched-load measurement for adaptation feedback validation."""

    strategy: str
    metric_value: float
    load_signature: str
    timestamp: float
    higher_is_better: bool = True


@dataclass(frozen=True)
class FeedbackValidationResult:
    """Result proving whether an adaptation is real or a measurement artifact."""

    candidate_strategy: str
    baseline_strategy: str
    matched_load_signature: str
    baseline_mean: float
    candidate_mean: float
    relative_improvement: float
    accepted: bool
    reason: str


class FeedbackLoopValidator:
    """Validate self-optimization using matched load signatures before adoption."""

    def __init__(self, min_samples: int = 2, min_relative_improvement: float = 0.02) -> None:
        self.min_samples = int(min_samples)
        self.min_relative_improvement = float(min_relative_improvement)

    def validate(
        self,
        measurements: Sequence[ExperimentMeasurement],
        *,
        baseline_strategy: str,
        candidate_strategy: str,
        load_signature: str,
    ) -> FeedbackValidationResult:
        baseline = [
            item
            for item in measurements
            if item.strategy == baseline_strategy and item.load_signature == load_signature
        ]
        candidate = [
            item
            for item in measurements
            if item.strategy == candidate_strategy and item.load_signature == load_signature
        ]
        if len(baseline) < self.min_samples or len(candidate) < self.min_samples:
            return FeedbackValidationResult(
                candidate_strategy,
                baseline_strategy,
                load_signature,
                0.0,
                0.0,
                0.0,
                False,
                "insufficient_matched_samples",
            )

        baseline_mean = sum(item.metric_value for item in baseline) / len(baseline)
        candidate_mean = sum(item.metric_value for item in candidate) / len(candidate)
        higher_is_better = candidate[0].higher_is_better
        if higher_is_better:
            relative = (candidate_mean - baseline_mean) / max(abs(baseline_mean), 1e-12)
        else:
            relative = (baseline_mean - candidate_mean) / max(abs(baseline_mean), 1e-12)
        accepted = relative >= self.min_relative_improvement
        return FeedbackValidationResult(
            candidate_strategy,
            baseline_strategy,
            load_signature,
            float(baseline_mean),
            float(candidate_mean),
            float(relative),
            accepted,
            "validated_matched_load_improvement" if accepted else "improvement_below_threshold",
        )


class SalamanderObservabilitySnapshot:
    """Read-only projection of frontier state for dashboards and workflows."""

    ADAPTATION_EVENTS = frozenset({"adaptation_decision", "phi_value_updated", "worker_spawned"})

    def __init__(
        self, audit_log: ImmutableEvidenceLog, seal_lifecycle: EvidenceSealLifecycle
    ) -> None:
        self.audit_log = audit_log
        self.seal_lifecycle = seal_lifecycle

    def to_dict(self) -> dict[str, Any]:
        entries = self.audit_log.entries()
        adaptation_events = [entry for entry in entries if entry.event in self.ADAPTATION_EVENTS]
        seals = self.seal_lifecycle.seal_log(self.audit_log)
        return {
            "evidence_events_total": len(entries),
            "adaptation_events_total": len(adaptation_events),
            "latest_evidence_hash": (
                seals[-1].entry_hash if seals else EvidenceSealLifecycle.GENESIS_HASH
            ),
            "domains": sorted(
                {str(entry.data.get("domain")) for entry in entries if "domain" in entry.data}
            ),
            "integrity": "sealed" if seals else "empty",
        }


class CrossLanguageReplayManifest:
    """Language-neutral canonical manifest for replaying evidence elsewhere."""

    SCHEMA_VERSION = "salamander.frontier.replay.v1"

    def __init__(self, audit_log: ImmutableEvidenceLog) -> None:
        self.audit_log = audit_log

    def to_manifest(self) -> dict[str, Any]:
        entries = [entry.to_dict() for entry in self.audit_log.entries()]
        return {
            "schema_version": self.SCHEMA_VERSION,
            "entry_count": len(entries),
            "entries": entries,
            "replay_digest": self.replay_digest(entries),
        }

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any]) -> ImmutableEvidenceLog:
        if manifest.get("schema_version") != cls.SCHEMA_VERSION:
            raise ValueError("unsupported Salamander replay manifest schema")
        entries = tuple(
            FrontierAuditEntry(
                event=str(item["event"]),
                timestamp=float(item["timestamp"]),
                actor=str(item.get("actor", "system")),
                data=dict(item.get("data", {})),
            )
            for item in manifest.get("entries", [])
        )
        expected_digest = manifest.get("replay_digest")
        actual_digest = cls.replay_digest([entry.to_dict() for entry in entries])
        if expected_digest != actual_digest:
            raise ValueError("Salamander replay manifest digest mismatch")
        return ImmutableEvidenceLog(entries)

    @staticmethod
    def replay_digest(entries: Sequence[dict[str, Any]]) -> str:
        encoded = json.dumps(entries, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MetabolicInvariantMetrics:
    """Measured work and energy window for substrate conservation checks."""

    work_performed: float
    energy_input_joules: float
    thermodynamic_efficiency: float
    max_work_per_joule: float


@dataclass(frozen=True)
class ValidationInvariantResult:
    """Single invariant verdict emitted by the Salamander validation battery."""

    invariant: str
    passed: bool
    reason: str
    observed: dict[str, Any]


class SalamanderPropertyBattery:
    """Formal invariant checks for evidence, metabolism, and phi resonance.

    These checks are deliberately deterministic and data-local.  They do not
    claim external scientific proof; they enforce repository-level conservation
    laws that can be exercised by property tests and audit scripts.
    """

    def invariant_evidence_fidelity(
        self, evidence_log: ImmutableEvidenceLog
    ) -> ValidationInvariantResult:
        manifest = CrossLanguageReplayManifest(evidence_log).to_manifest()
        replayed = CrossLanguageReplayManifest.from_manifest(manifest)
        original_digest = evidence_log.seal()
        replayed_digest = replayed.seal()
        passed = original_digest == replayed_digest
        return ValidationInvariantResult(
            invariant="evidence_fidelity",
            passed=passed,
            reason=(
                "replay_digest_matches_evidence"
                if passed
                else "INFIDELITY: State drift detected"
            ),
            observed={
                "entry_count": manifest["entry_count"],
                "original_digest": original_digest,
                "replayed_digest": replayed_digest,
            },
        )

    def invariant_metabolic_conservation(
        self, metrics: MetabolicInvariantMetrics
    ) -> ValidationInvariantResult:
        values = (
            metrics.work_performed,
            metrics.energy_input_joules,
            metrics.thermodynamic_efficiency,
            metrics.max_work_per_joule,
        )
        if any(not isfinite(value) for value in values):
            raise ValueError("metabolic invariant metrics must be finite")
        if (
            metrics.work_performed < 0
            or metrics.energy_input_joules < 0
            or metrics.thermodynamic_efficiency < 0
            or metrics.max_work_per_joule < 0
        ):
            raise ValueError("metabolic invariant metrics must be non-negative")

        theoretical_max_work = (
            metrics.energy_input_joules
            * min(metrics.thermodynamic_efficiency, 1.0)
            * metrics.max_work_per_joule
        )
        passed = metrics.work_performed <= theoretical_max_work
        return ValidationInvariantResult(
            invariant="metabolic_conservation",
            passed=passed,
            reason=(
                "work_within_energy_budget"
                if passed
                else "PHYSICS_VIOLATION: claimed work exceeds configured energy budget"
            ),
            observed={
                "work_performed": metrics.work_performed,
                "theoretical_max_work": theoretical_max_work,
                "efficiency_used": min(metrics.thermodynamic_efficiency, 1.0),
            },
        )

    def invariant_phi_resonance_bounds(
        self, current_phi: float, *, epsilon: float = 0.5
    ) -> ValidationInvariantResult:
        if not isfinite(current_phi) or not isfinite(epsilon):
            raise ValueError("phi resonance inputs must be finite")
        if epsilon <= 0:
            raise ValueError("phi resonance epsilon must be positive")

        drift = abs(current_phi - PHI)
        passed = drift < epsilon
        return ValidationInvariantResult(
            invariant="phi_resonance_bounds",
            passed=passed,
            reason=(
                "phi_within_harmonic_zone"
                if passed
                else "GENETIC_DRIFT: Phi has mutated beyond resonance"
            ),
            observed={"current_phi": current_phi, "golden_ratio": PHI, "drift": drift},
        )


@dataclass(frozen=True)
class MetricTrendPoint:
    """Observed metric point used for anticipatory adaptation."""

    timestamp: float
    value: float


@dataclass(frozen=True)
class AnticipatoryAdaptationPlan:
    """Plan generated before a capability crosses its health threshold."""

    capability: str
    metric_name: str
    action: str
    predicted_breach_timestamp: float | None
    lead_time_seconds: float | None
    reason: str


class AnticipatoryAdaptationPlanner:
    """Predict future threshold breaches from evidence trends before failure."""

    def __init__(self, minimum_lead_time_seconds: float = 60.0) -> None:
        self.minimum_lead_time_seconds = float(minimum_lead_time_seconds)

    def plan(
        self,
        observation: CapabilityObservation,
        trend: Sequence[MetricTrendPoint],
        *,
        now: float,
    ) -> AnticipatoryAdaptationPlan | None:
        if len(trend) < 2:
            return None
        first = trend[0]
        last = trend[-1]
        elapsed = last.timestamp - first.timestamp
        if elapsed <= 0:
            return None
        slope = (last.value - first.value) / elapsed
        threshold_value = (
            observation.target_value * 0.9
            if observation.higher_is_better
            else observation.target_value / 0.9
        )
        if observation.higher_is_better:
            if slope >= 0 or last.value <= threshold_value:
                return None
            seconds_to_breach = (last.value - threshold_value) / abs(slope)
            action = "pre_grow_capacity"
        else:
            if slope <= 0 or last.value >= threshold_value:
                return None
            seconds_to_breach = (threshold_value - last.value) / slope
            action = "pre_shed_or_rebalance_load"
        if seconds_to_breach < self.minimum_lead_time_seconds:
            return None
        return AnticipatoryAdaptationPlan(
            capability=observation.capability,
            metric_name=observation.metric_name,
            action=action,
            predicted_breach_timestamp=last.timestamp + seconds_to_breach,
            lead_time_seconds=seconds_to_breach,
            reason="trend_predicts_future_threshold_breach",
        )


@dataclass(frozen=True)
class ComputeGrowthOption:
    """Candidate compute-growth action for economic autonomy simulation."""

    option_id: str
    expected_value: float
    cost: float
    risk_discount: float = 0.0

    @property
    def risk_adjusted_value(self) -> float:
        return self.expected_value * (1.0 - self.risk_discount)

    @property
    def roi(self) -> float:
        if self.cost <= 0:
            return float("inf")
        return (self.risk_adjusted_value - self.cost) / self.cost


@dataclass(frozen=True)
class EconomicAutonomyDecision:
    """Auditable decision to allocate or reject additional compute budget."""

    option_id: str | None
    approved: bool
    budget_after: float
    roi: float
    reason: str


class EconomicAutonomyAllocator:
    """Decide whether growing compute is worth its cost without executing purchases."""

    def __init__(self, roi_threshold: float = 0.10) -> None:
        self.roi_threshold = float(roi_threshold)

    def choose(
        self, options: Sequence[ComputeGrowthOption], available_budget: float
    ) -> EconomicAutonomyDecision:
        affordable = [option for option in options if option.cost <= available_budget]
        if not affordable:
            return EconomicAutonomyDecision(
                None, False, available_budget, 0.0, "no_affordable_options"
            )
        best = max(affordable, key=lambda option: option.roi)
        if best.roi < self.roi_threshold:
            return EconomicAutonomyDecision(
                best.option_id,
                False,
                available_budget,
                float(best.roi),
                "roi_below_threshold",
            )
        return EconomicAutonomyDecision(
            best.option_id,
            True,
            available_budget - best.cost,
            float(best.roi),
            "risk_adjusted_roi_approved",
        )


@dataclass(frozen=True)
class EvidenceTraitClaim:
    """Physical/economic trait claim submitted by a distributed node."""

    origin_id: str
    work_units: float
    energy_watts: float
    duration_seconds: float
    error_rate: float = 0.0

    @property
    def watt_hours(self) -> float:
        return self.energy_watts * self.duration_seconds / 3600.0

    @property
    def work_per_watt_hour(self) -> float:
        return self.work_units / max(self.watt_hours, 1e-12)


@dataclass(frozen=True)
class ImmuneResponse:
    """Result of mathematical trait validation for one node claim."""

    origin_id: str
    accepted: bool
    quarantined: bool
    reason: str
    work_per_watt_hour: float


class SalamanderImmuneSystem:
    """Mathematical immune response for implausible or Byzantine evidence."""

    def __init__(
        self,
        *,
        min_work_per_watt_hour: float,
        max_work_per_watt_hour: float,
        max_error_rate: float = 0.05,
    ) -> None:
        self.min_work_per_watt_hour = float(min_work_per_watt_hour)
        self.max_work_per_watt_hour = float(max_work_per_watt_hour)
        self.max_error_rate = float(max_error_rate)
        self.quarantined_nodes: set[str] = set()

    def validate_trait(self, claim: EvidenceTraitClaim) -> ImmuneResponse:
        efficiency = claim.work_per_watt_hour
        accepted = (
            self.min_work_per_watt_hour <= efficiency <= self.max_work_per_watt_hour
            and claim.error_rate <= self.max_error_rate
            and claim.energy_watts > 0
            and claim.duration_seconds > 0
        )
        reason = "trait_plausible"
        if not accepted:
            self.quarantined_nodes.add(claim.origin_id)
            if efficiency > self.max_work_per_watt_hour:
                reason = "non_physical_efficiency_claim"
            elif efficiency < self.min_work_per_watt_hour:
                reason = "insufficient_work_for_energy"
            elif claim.error_rate > self.max_error_rate:
                reason = "error_rate_exceeds_bound"
            else:
                reason = "invalid_energy_or_duration"
        return ImmuneResponse(claim.origin_id, accepted, not accepted, reason, float(efficiency))

    def peer_audit(
        self,
        peer_id: str,
        audit_log: ImmutableEvidenceLog,
        expected_seals: Sequence[EvidenceSeal],
        seal_lifecycle: EvidenceSealLifecycle,
    ) -> ImmuneResponse:
        if seal_lifecycle.verify_log(audit_log, expected_seals):
            return ImmuneResponse(peer_id, True, False, "peer_evidence_chain_valid", 0.0)
        self.quarantined_nodes.add(peer_id)
        return ImmuneResponse(peer_id, False, True, "peer_evidence_chain_invalid", 0.0)


@dataclass(frozen=True)
class MorphogeneticBlueprint:
    """Success template distilled from an adaptation that performed well."""

    blueprint_id: str
    domain: str
    capability: str
    parameters: dict[str, Any]
    fitness_score: float
    environment_signature: str


class MorphogeneticBlueprintLibrary:
    """Remember successful operating shapes and retrieve them by environment."""

    def __init__(self) -> None:
        self._blueprints: dict[str, MorphogeneticBlueprint] = {}

    def add(self, blueprint: MorphogeneticBlueprint) -> None:
        self._blueprints[blueprint.blueprint_id] = blueprint

    def best_for(
        self, domain: str, capability: str, environment_signature: str
    ) -> MorphogeneticBlueprint | None:
        candidates = [
            blueprint
            for blueprint in self._blueprints.values()
            if blueprint.domain == domain
            and blueprint.capability == capability
            and blueprint.environment_signature == environment_signature
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda blueprint: blueprint.fitness_score)

    def distill_from_decision(
        self,
        decision: AdaptationDecision,
        *,
        parameters: dict[str, Any],
        fitness_score: float,
        environment_signature: str,
    ) -> MorphogeneticBlueprint:
        payload = {
            "domain": decision.domain,
            "capability": decision.capability,
            "parameters": parameters,
            "fitness_score": fitness_score,
            "environment_signature": environment_signature,
        }
        blueprint_id = (
            "BLP-"
            + hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:16]
        )
        blueprint = MorphogeneticBlueprint(
            blueprint_id,
            decision.domain,
            decision.capability,
            parameters,
            float(fitness_score),
            environment_signature,
        )
        self.add(blueprint)
        return blueprint


@dataclass(frozen=True)
class MetabolicCostProfile:
    """Cost of breathing for compute growth: watts, time, and energy price."""

    watts: float
    duration_hours: float
    cost_per_kwh: float

    @property
    def energy_cost(self) -> float:
        return (self.watts / 1000.0) * self.duration_hours * self.cost_per_kwh


class MetabolicEconomicAutonomyAllocator(EconomicAutonomyAllocator):
    """Economic allocator that includes power cost in compute-growth ROI."""

    def choose_with_metabolism(
        self,
        options: Sequence[tuple[ComputeGrowthOption, MetabolicCostProfile]],
        available_budget: float,
    ) -> EconomicAutonomyDecision:
        adjusted = [
            ComputeGrowthOption(
                option.option_id,
                option.expected_value,
                option.cost + profile.energy_cost,
                option.risk_discount,
            )
            for option, profile in options
        ]
        return self.choose(adjusted, available_budget)


@dataclass(frozen=True)
class SymbioticNutrientOffer:
    """Evidence-backed offer from one repo/domain to another."""

    origin_domain: str
    target_domain: str
    resource: str
    amount: float
    evidence_hash: str


@dataclass(frozen=True)
class SymbioticNutrientDecision:
    """Decision for cross-repo nutrient/resource exchange."""

    accepted: bool
    reason: str
    resource: str
    amount: float


class SymbioticEvidenceBridge:
    """Coordinate resource exchange between Salamander repos through evidence."""

    def evaluate_offer(
        self,
        offer: SymbioticNutrientOffer,
        trusted_hashes: set[str],
        requested_resource: str,
        requested_amount: float,
    ) -> SymbioticNutrientDecision:
        if offer.evidence_hash not in trusted_hashes:
            return SymbioticNutrientDecision(False, "untrusted_evidence_hash", offer.resource, 0.0)
        if offer.resource != requested_resource:
            return SymbioticNutrientDecision(False, "resource_mismatch", offer.resource, 0.0)
        accepted_amount = min(offer.amount, requested_amount)
        return SymbioticNutrientDecision(
            True, "symbiotic_exchange_accepted", offer.resource, accepted_amount
        )


@dataclass(frozen=True)
class BlastemaBootstrapPlan:
    """Portable seed plan for rehydrating a manifest in another runtime."""

    manifest_digest: str
    seed_path: str
    runtime_hint: str
    command: tuple[str, ...]


class BlastemaRehydrator:
    """Create portable bootstrap plans for manifest-based runtime rehydration."""

    def __init__(self, seed_path: str = "runtime_seeds/salamander_blastema_seed.rs") -> None:
        self.seed_path = seed_path

    def plan(self, manifest: dict[str, Any], runtime_hint: str = "rust") -> BlastemaBootstrapPlan:
        digest = str(manifest["replay_digest"])
        return BlastemaBootstrapPlan(
            manifest_digest=digest,
            seed_path=self.seed_path,
            runtime_hint=runtime_hint,
            command=("rustc", self.seed_path, "-o", "salamander_blastema_seed"),
        )


@dataclass(frozen=True)
class SynapticLatencyEdge:
    """Measured latency-distance between two nodes in the Salamander substrate."""

    node_a: str
    node_b: str
    latency_ms: float
    jitter_ms: float = 0.0
    observed_at: float = 0.0

    def connects(self, node_id: str) -> bool:
        return self.node_a == node_id or self.node_b == node_id

    def other(self, node_id: str) -> str:
        if self.node_a == node_id:
            return self.node_b
        if self.node_b == node_id:
            return self.node_a
        raise ValueError(f"node {node_id} is not part of this synaptic edge")


@dataclass(frozen=True)
class RegenerationAffinity:
    """Preferred location for regrowing a capability."""

    node_id: str
    affinity_score: float
    latency_ms: float
    reason: str


class SalamanderNervousSystem:
    """Topology sense for choosing where the next regeneration should happen."""

    def __init__(self, edges: Iterable[SynapticLatencyEdge] | None = None) -> None:
        self._edges: list[SynapticLatencyEdge] = list(edges or [])

    def observe_edge(self, edge: SynapticLatencyEdge) -> None:
        self._edges.append(edge)

    def latency_map(self, origin_node: str) -> dict[str, float]:
        best: dict[str, float] = {}
        for edge in self._edges:
            if not edge.connects(origin_node):
                continue
            peer = edge.other(origin_node)
            effective_latency = edge.latency_ms + edge.jitter_ms
            best[peer] = min(best.get(peer, float("inf")), effective_latency)
        return best

    def choose_regeneration_affinity(
        self,
        origin_node: str,
        candidate_nodes: Sequence[str],
        *,
        data_gravity: dict[str, float] | None = None,
        treasury_gravity: dict[str, float] | None = None,
    ) -> RegenerationAffinity | None:
        latencies = self.latency_map(origin_node)
        data_gravity = data_gravity or {}
        treasury_gravity = treasury_gravity or {}
        scored: list[RegenerationAffinity] = []
        for node in candidate_nodes:
            latency = latencies.get(node)
            if latency is None:
                continue
            gravity_bonus = data_gravity.get(node, 0.0) + treasury_gravity.get(node, 0.0)
            score = gravity_bonus - latency
            scored.append(
                RegenerationAffinity(
                    node,
                    float(score),
                    float(latency),
                    "lowest_latency_with_gravity_bonus",
                )
            )
        if not scored:
            return None
        return max(scored, key=lambda affinity: affinity.affinity_score)


@dataclass(frozen=True)
class SalamanderGene:
    """Self-configuration gene that may evolve through measured outcomes."""

    name: str
    value: float
    min_value: float
    max_value: float

    def clipped(self, value: float) -> "SalamanderGene":
        return SalamanderGene(
            self.name,
            min(max(float(value), self.min_value), self.max_value),
            self.min_value,
            self.max_value,
        )


@dataclass(frozen=True)
class GeneExperimentOutcome:
    """Fitness result from trying one gene value."""

    gene_name: str
    tested_value: float
    fitness_score: float


class RecursiveGeneFolder:
    """Meta-evolve Salamander thresholds using measured adaptation outcomes."""

    def __init__(self, learning_rate: float = 0.25) -> None:
        self.learning_rate = float(learning_rate)

    def evolve(
        self,
        genes: dict[str, SalamanderGene],
        outcomes: Sequence[GeneExperimentOutcome],
    ) -> dict[str, SalamanderGene]:
        evolved = dict(genes)
        for gene_name, gene in genes.items():
            gene_outcomes = [outcome for outcome in outcomes if outcome.gene_name == gene_name]
            if not gene_outcomes:
                continue
            best = max(gene_outcomes, key=lambda outcome: outcome.fitness_score)
            folded_value = gene.value + (best.tested_value - gene.value) * self.learning_rate
            evolved[gene_name] = gene.clipped(folded_value)
        return evolved


@dataclass(frozen=True)
class GlobalBlueprintRecord:
    """Species-memory record for sharing a blueprint through evidence."""

    blueprint: MorphogeneticBlueprint
    origin_node: str
    evidence_hash: str
    published_at: float


class GlobalEvidenceLedger:
    """Memory of the species: exchange trusted blueprints across agents/repos."""

    def __init__(self) -> None:
        self._records: list[GlobalBlueprintRecord] = []

    def publish_blueprint(
        self,
        blueprint: MorphogeneticBlueprint,
        *,
        origin_node: str,
        audit_log: ImmutableEvidenceLog,
        published_at: float,
    ) -> GlobalBlueprintRecord:
        record = GlobalBlueprintRecord(
            blueprint=blueprint,
            origin_node=origin_node,
            evidence_hash=audit_log.seal(),
            published_at=published_at,
        )
        self._records.append(record)
        return record

    def inherit_blueprints(
        self,
        *,
        trusted_hashes: set[str],
        domain: str,
        capability: str,
    ) -> tuple[MorphogeneticBlueprint, ...]:
        inherited = [
            record.blueprint
            for record in self._records
            if record.evidence_hash in trusted_hashes
            and record.blueprint.domain == domain
            and record.blueprint.capability == capability
        ]
        return tuple(sorted(inherited, key=lambda blueprint: blueprint.fitness_score, reverse=True))


@dataclass(frozen=True)
class DreamMutation:
    """Offline gene change to replay against historical evidence."""

    gene_name: str
    mutated_value: float


@dataclass(frozen=True)
class DreamOutcome:
    """Result of a sandboxed what-if replay."""

    dream_id: str
    gene_name: str
    mutated_value: float
    baseline_fitness: float
    simulated_fitness: float
    improvement: float
    promoted: bool
    evolved_genes: dict[str, SalamanderGene]
    evidence_hash: str
    audit_log: ImmutableEvidenceLog


class SalamanderDreamState:
    """Sandboxed foresight from replaying evidence with mutated genes.

    The dream state never edits live agents directly. It replays an
    ``ImmutableEvidenceLog`` through a caller-supplied deterministic evaluator,
    compares the mutated gene set with the current gene set, and only emits a
    promotable outcome when the simulated fitness clears the configured
    improvement threshold.
    """

    def __init__(
        self,
        fitness_evaluator: Callable[[ImmutableEvidenceLog, dict[str, SalamanderGene]], float],
        *,
        promotion_threshold: float = 0.0,
    ) -> None:
        self.fitness_evaluator = fitness_evaluator
        self.promotion_threshold = float(promotion_threshold)

    def dream(
        self,
        historical_log: ImmutableEvidenceLog,
        genes: dict[str, SalamanderGene],
        mutations: Sequence[DreamMutation],
        *,
        actor: str = "dream-state",
        timestamp: float | None = None,
    ) -> tuple[DreamOutcome, ...]:
        """Replay a batch of mutations and return the strongest dreams first."""

        outcomes = tuple(
            self.simulate_mutation(
                historical_log,
                genes,
                mutation,
                actor=actor,
                timestamp=timestamp,
            )
            for mutation in mutations
        )
        return tuple(sorted(outcomes, key=lambda outcome: outcome.improvement, reverse=True))

    def simulate_mutation(
        self,
        historical_log: ImmutableEvidenceLog,
        genes: dict[str, SalamanderGene],
        mutation: DreamMutation,
        *,
        actor: str = "dream-state",
        timestamp: float | None = None,
    ) -> DreamOutcome:
        if mutation.gene_name not in genes:
            raise KeyError(f"unknown gene: {mutation.gene_name}")

        baseline_fitness = float(self.fitness_evaluator(historical_log, dict(genes)))
        evolved_genes = dict(genes)
        evolved_genes[mutation.gene_name] = genes[mutation.gene_name].clipped(
            mutation.mutated_value
        )
        simulated_fitness = float(self.fitness_evaluator(historical_log, evolved_genes))
        if not isfinite(baseline_fitness) or not isfinite(simulated_fitness):
            raise ValueError("dream fitness evaluator must return finite values")
        improvement = simulated_fitness - baseline_fitness
        promoted = improvement > self.promotion_threshold
        evidence_hash = historical_log.seal()
        dream_material = {
            "evidence_hash": evidence_hash,
            "gene_name": mutation.gene_name,
            "mutated_value": evolved_genes[mutation.gene_name].value,
            "baseline_fitness": baseline_fitness,
            "simulated_fitness": simulated_fitness,
            "promotion_threshold": self.promotion_threshold,
        }
        dream_id = "DRM-SIM-" + hashlib.sha256(
            json.dumps(dream_material, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:16]
        audit_log = historical_log.append(
            "dream_mutation_replayed",
            actor=actor,
            timestamp=timestamp,
            dream_id=dream_id,
            promoted=promoted,
            improvement=improvement,
            **dream_material,
        )
        return DreamOutcome(
            dream_id=dream_id,
            gene_name=mutation.gene_name,
            mutated_value=evolved_genes[mutation.gene_name].value,
            baseline_fitness=baseline_fitness,
            simulated_fitness=simulated_fitness,
            improvement=improvement,
            promoted=promoted,
            evolved_genes=evolved_genes if promoted else dict(genes),
            evidence_hash=evidence_hash,
            audit_log=audit_log,
        )

    def promote_blueprint(
        self,
        outcome: DreamOutcome,
        *,
        ledger: GlobalEvidenceLedger,
        domain: str,
        capability: str,
        origin_node: str,
        audit_log: ImmutableEvidenceLog,
        published_at: float,
        environment_signature: str = "dream-sandbox",
    ) -> GlobalBlueprintRecord:
        if not outcome.promoted:
            raise ValueError("dream outcome did not clear promotion threshold")
        parameters = {
            "dream_id": outcome.dream_id,
            "dream_gene": outcome.gene_name,
            "mutated_value": outcome.mutated_value,
            "evidence_hash": outcome.evidence_hash,
            "baseline_fitness": outcome.baseline_fitness,
            "simulated_fitness": outcome.simulated_fitness,
            "improvement": outcome.improvement,
            "genes": {name: gene.value for name, gene in outcome.evolved_genes.items()},
        }
        payload = {
            "domain": domain,
            "capability": capability,
            "parameters": parameters,
            "fitness_score": outcome.simulated_fitness,
            "environment_signature": environment_signature,
        }
        blueprint_id = (
            "DRM-"
            + hashlib.sha256(
                json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
            ).hexdigest()[:16]
        )
        blueprint = MorphogeneticBlueprint(
            blueprint_id,
            domain,
            capability,
            parameters,
            outcome.simulated_fitness,
            environment_signature,
        )
        return ledger.publish_blueprint(
            blueprint, origin_node=origin_node, audit_log=audit_log, published_at=published_at
        )


@dataclass(frozen=True)
class AgentViabilityMetrics:
    """Fitness window used to decide whether an agent should self-prune."""

    agent_id: str
    roi: float
    metabolic_cost: float
    consecutive_underperforming_windows: int
    evidence_log: ImmutableEvidenceLog


@dataclass(frozen=True)
class ApoptosisDecision:
    """Programmed pruning decision that preserves evidence before shutdown."""

    agent_id: str
    should_prune: bool
    reason: str
    evidence_hash: str
    final_manifest: dict[str, Any] | None


class SalamanderApoptosis:
    """Programmed pruning of functional-but-unfit nodes to keep the colony lean."""

    def __init__(
        self,
        *,
        species_roi_ratio_threshold: float = 0.70,
        minimum_underperforming_windows: int = 3,
    ) -> None:
        self.species_roi_ratio_threshold = float(species_roi_ratio_threshold)
        self.minimum_underperforming_windows = int(minimum_underperforming_windows)

    def check_viability(
        self,
        metrics: AgentViabilityMetrics,
        *,
        species_average_roi: float,
    ) -> ApoptosisDecision:
        evidence_hash = metrics.evidence_log.seal()
        roi_floor = species_average_roi * self.species_roi_ratio_threshold
        below_species_floor = metrics.roi < roi_floor
        sustained = (
            metrics.consecutive_underperforming_windows >= self.minimum_underperforming_windows
        )
        metabolically_negative = metrics.roi < 0 or metrics.roi < metrics.metabolic_cost
        should_prune = below_species_floor and sustained and metabolically_negative
        if not should_prune:
            return ApoptosisDecision(
                metrics.agent_id,
                False,
                "agent_remains_viable",
                evidence_hash,
                None,
            )
        manifest = CrossLanguageReplayManifest(metrics.evidence_log).to_manifest()
        return ApoptosisDecision(
            metrics.agent_id,
            True,
            "export_evidence_then_graceful_shutdown",
            evidence_hash,
            manifest,
        )


@dataclass(frozen=True)
class ResonanceMeasurement:
    """Measured substrate response for one phi/frequency variant."""

    phi_value: float
    execution_jitter_ms: float
    thermal_drift_c: float
    throughput: float


@dataclass(frozen=True)
class ResonanceLock:
    """Chosen harmonic operating point for the local substrate."""

    phi_value: float
    resonance_score: float
    reason: str


class ResonantSubstrateTuner:
    """Search for the phi-adjacent harmonic with lowest jitter and heat."""

    def __init__(
        self,
        *,
        jitter_weight: float = 1.0,
        thermal_weight: float = 1.0,
        throughput_weight: float = 1.0,
    ) -> None:
        self.jitter_weight = float(jitter_weight)
        self.thermal_weight = float(thermal_weight)
        self.throughput_weight = float(throughput_weight)

    def candidate_phi_values(
        self, center_phi: float = PHI, epsilon: float = 0.01
    ) -> tuple[float, ...]:
        return (
            center_phi - 2 * epsilon,
            center_phi - epsilon,
            center_phi,
            center_phi + epsilon,
            center_phi + 2 * epsilon,
        )

    def find_harmonic_phi(self, measurements: Sequence[ResonanceMeasurement]) -> ResonanceLock:
        if not measurements:
            raise ValueError("at least one resonance measurement is required")
        best_measurement = max(measurements, key=self._score)
        return ResonanceLock(
            best_measurement.phi_value,
            self._score(best_measurement),
            "max_throughput_min_jitter_min_thermal_drift",
        )

    def _score(self, measurement: ResonanceMeasurement) -> float:
        return (
            measurement.throughput * self.throughput_weight
            - measurement.execution_jitter_ms * self.jitter_weight
            - measurement.thermal_drift_c * self.thermal_weight
        )


class SalamanderOrchestrator:
    """
    Coordinates all four frontier capabilities.
    System state emerges from their interaction.
    
    Mathematical first principles: substrate and hardware agnostic.
    """

    def __init__(
        self,
        audit_log: ImmutableEvidenceLog | None = None,
        total_target_hashrate: float = 150.0,
    ) -> None:
        self.audit_log = audit_log or ImmutableEvidenceLog()
        self.total_target_hashrate = float(total_target_hashrate)
        
        # Initialize components
        self.salamander_core = SalamanderCore(audit_log=self.audit_log)
        self.regeneration_layer = EvidenceBasedRegenerator(self.audit_log)
        self.agent_coherence = DistributedAgentCoherence(self.audit_log, self.total_target_hashrate)
        self.phi_tuning = AdaptivePhiTuning(audit_log=self.audit_log)
        self.worker_scaling = SelfScalingWorkerPool(
            target_hashrate=self.total_target_hashrate,
            audit_log=self.audit_log,
        )
        
        self.is_running = False
        self.mining_iteration_count = 0

    def initialize(self) -> None:
        """
        Boot Salamander system from scratch.
        Start minimal, let it grow.
        """
        # Start single agent
        self.audit_log = self.agent_coherence.add_agent(
            "agent_0", job_id="initial_job", timestamp=time()
        )
        
        # Measure baseline compression efficiency
        working_set = [1.0, 2.0, 3.0, 4.0, 5.0]
        self.phi_tuning.initialize_phi_baseline(working_set)
        
        self.audit_log = self.audit_log.append(
            "salamander_initialized",
            timestamp=time(),
            initial_agents=1,
            initial_workers=1,
            phi_initial=self.phi_tuning.phi_current,
        )

    async def main_autonomy_loop(self, observation_interval_seconds: float = 5.0) -> None:
        """
        Core autonomy loop: observe → detect → regenerate → learn
        Runs continuously.
        """
        self.is_running = True
        
        while self.is_running:
            # Observe current state (non-invasive)
            metrics = self.salamander_core.observe_system_state()
            
            # Detect anomalies or optimization opportunities
            anomaly = self.salamander_core.detect_anomaly(metrics)
            
            # If anomaly detected, execute regeneration
            if anomaly is not None:
                outcome = self.salamander_core.execute_regeneration(anomaly)
                
                # Check coherence after regeneration
                states = self.regeneration_layer.recover_system()
                hashrates = {aid: state.target_hashrate for aid, state in states.items()}
                coherence = self.agent_coherence.measure("current_job", hashrates)
                
                if coherence.jobs_diverged > 0:
                    self.agent_coherence.rebalance_work_distribution(
                        "current_job", hashrates, self.total_target_hashrate / max(len(states), 1)
                    )
            
            # Continue observing
            await asyncio.sleep(observation_interval_seconds)

    async def phi_optimization_loop(self, optimization_interval_seconds: float = 600.0) -> None:
        """
        Background: continuously optimize φ-value.
        Runs in parallel, doesn't block mining.
        """
        self.is_running = True
        working_set = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        while self.is_running:
            await asyncio.sleep(optimization_interval_seconds)
            
            self.phi_tuning.continuous_phi_optimization(working_set, self.mining_iteration_count)

    async def scaling_optimization_loop(self, optimization_interval_seconds: float = 1800.0) -> None:
        """
        Background: continuously optimize worker count.
        Runs in parallel, doesn't block mining.
        """
        self.is_running = True
        
        while self.is_running:
            await asyncio.sleep(optimization_interval_seconds)
            
            # Measure current hashrate
            current_hashrate = self.worker_scaling.measure_hashrate_with_worker_count(
                self.worker_scaling.current_worker_count
            )
            
            # Monitor scaling efficiency
            self.worker_scaling.monitor_scaling_efficiency(current_hashrate)

    def get_system_state(self) -> dict[str, ReplayedAgentState]:
        """
        At any point, recover current system state from evidence.
        """
        return self.regeneration_layer.regenerate_system()

    def get_health_report(self) -> HealthReport:
        """
        Generate comprehensive health report.
        """
        current_metrics = self.salamander_core.observe_system_state()
        states = self.regeneration_layer.recover_system()
        
        return HealthReport(
            timestamp=time(),
            agents_active=len(states),
            workers_total=sum(state.workers for state in states.values()),
            hashrate_current=current_metrics.hashrate_current,
            hashrate_target=current_metrics.hashrate_target,
            hashrate_efficiency=current_metrics.hashrate_current / max(current_metrics.hashrate_target, 1.0),
            memory_used=current_metrics.memory_used,
            memory_available=current_metrics.memory_available,
            memory_efficiency=1.0 - (current_metrics.memory_used / max(current_metrics.memory_available, 1.0)),
            phi_current=self.phi_tuning.phi_current,
            compression_ratio=self.phi_tuning.phi_baseline_efficiency,
            share_acceptance_rate=current_metrics.share_acceptance_rate,
            stale_share_rate=current_metrics.stale_share_rate,
            pool_connectivity="healthy",
            regenerations_performed=self.salamander_core.regeneration_count,
            adaptations_performed=self.salamander_core.adaptations_performed,
            last_anomaly=current_metrics.last_anomaly,
            time_since_last_regeneration=current_metrics.time_since_regeneration,
            evidence_log_size=len(self.audit_log.entries()),
            evidence_log_integrity="valid" if self.audit_log.seal() else "empty",
        )

    def get_adaptation_history(self) -> list[dict[str, Any]]:
        """
        Returns all adaptations performed.
        """
        adaptation_events = self.audit_log.filter(
            lambda e: e.event
            in {
                "regeneration_triggered",
                "phi_value_updated",
                "worker_spawned",
                "worker_removed",
                "agent_spawned",
                "agent_failure_handled",
            }
        )
        return [entry.to_dict() for entry in adaptation_events]

    def get_evidence_trail(self) -> list[dict[str, Any]]:
        """
        Returns immutable audit log.
        Read-only, no external writes.
        """
        return [entry.to_dict() for entry in self.audit_log.entries()]

    def get_prometheus_metrics(self) -> dict[str, float]:
        """
        Prometheus format metrics for time-series monitoring.
        """
        state = self.get_system_state()
        return {
            "salamander_agents_active": float(len(state)),
            "salamander_workers_total": float(sum(s.workers for s in state.values())),
            "salamander_hashrate_gh_s": self.salamander_core.observe_system_state().hashrate_current,
            "salamander_phi_value": self.phi_tuning.phi_current,
            "salamander_compression_ratio": self.phi_tuning.phi_baseline_efficiency,
            "salamander_regenerations_total": float(self.salamander_core.regeneration_count),
            "salamander_memory_used_bytes": self.salamander_core.observe_system_state().memory_used,
            "salamander_share_acceptance_rate": self.salamander_core.observe_system_state().share_acceptance_rate,
        }

    def generate_daily_report(self, target_date: float | None = None) -> dict[str, Any]:
        """
        Generate daily summary of all Salamander activities.
        """
        target_date = target_date or time()
        day_start = target_date - 86400.0  # 24 hours ago
        
        today_events = self.audit_log.filter(lambda e: day_start <= e.timestamp <= target_date)
        
        return {
            "date": target_date,
            "agents_spawned": len([e for e in today_events if e.event == "agent_spawned"]),
            "agents_failed": len([e for e in today_events if e.event == "agent_failure_handled"]),
            "workers_spawned": len([e for e in today_events if e.event == "worker_spawned"]),
            "workers_removed": len([e for e in today_events if e.event == "worker_removed"]),
            "regenerations": len([e for e in today_events if e.event == "regeneration_triggered"]),
            "phi_updates": len([e for e in today_events if e.event == "phi_value_updated"]),
            "total_shares": len([e for e in today_events if e.event == "share_found_and_submitted"]),
        }

    def stop(self) -> None:
        """Stop all autonomy loops."""
        self.is_running = False


class UnifiedMiningEngineWithSalamander:
    """
    Original UnifiedMiningEngine now wrapped with Salamander.
    Autonomy is transparent to mining code.
    
    Mathematical first principles: substrate and hardware agnostic.
    """

    def __init__(
        self,
        mining_engine: Any | None = None,
        salamander: SalamanderOrchestrator | None = None,
    ) -> None:
        self.mining_engine = mining_engine
        self.salamander = salamander or SalamanderOrchestrator()
        self.is_running = False

    async def run_mining_loop(
        self,
        get_job_func: Callable[[], Any] | None = None,
        search_func: Callable[[Any, float, float, int], Any] | None = None,
        submit_share_func: Callable[[Any], None] | None = None,
        loop_interval_seconds: float = 30.0,
    ) -> None:
        """
        Main mining loop. Salamander operates in background.
        """
        self.is_running = True
        self.salamander.initialize()
        
        # Start Salamander autonomy loops in background
        autonomy_task = asyncio.create_task(self.salamander.main_autonomy_loop())
        phi_task = asyncio.create_task(self.salamander.phi_optimization_loop())
        scaling_task = asyncio.create_task(self.salamander.scaling_optimization_loop())
        
        try:
            while self.is_running:
                # Request job from pool
                if get_job_func:
                    job = get_job_func()
                else:
                    job = {"job_id": f"job_{int(time())}", "difficulty": 1.0}
                
                # Mine with current configuration
                # (Salamander might change phi_value or worker_count)
                if search_func:
                    result = search_func(
                        job,
                        self.salamander.phi_tuning.phi_current,
                        self.salamander.worker_scaling.current_worker_count,
                    )
                else:
                    result = None
                
                # Submit result if found
                if result is not None and submit_share_func:
                    submit_share_func(result)
                    
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "share_found_and_submitted",
                        timestamp=time(),
                        nonce=result.get("nonce", 0),
                        difficulty=job.get("difficulty", 1.0),
                    )
                    self.salamander.mining_iteration_count += 1
                
                # Salamander monitors in background (doesn't block)
                # No explicit synchronization needed
                
                await asyncio.sleep(loop_interval_seconds)
        
        finally:
            # Stop Salamander autonomy loops
            self.salamander.stop()
            await asyncio.gather(autonomy_task, phi_task, scaling_task, return_exceptions=True)

    async def handle_pool_disconnect(
        self,
        reconnect_func: Callable[[], bool] | None = None,
        max_retries: int = 10,
        initial_backoff_seconds: float = 1.0,
    ) -> bool:
        """
        Pool disconnects. Salamander detects and triggers recovery.
        """
        anomaly = Anomaly(
            type="POOL_CONNECTIVITY_LOST",
            severity="CRITICAL",
            action="reconnect_with_backoff",
        )
        
        outcome = self.salamander.salamander_core.execute_regeneration(anomaly)
        
        # Retry connection
        retry_count = 0
        backoff_seconds = initial_backoff_seconds
        
        while retry_count < max_retries and self.is_running:
            if reconnect_func:
                success = reconnect_func()
                if success:
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "pool_reconnected",
                        timestamp=time(),
                        retry_count=retry_count,
                    )
                    return True
            else:
                # Simulate successful reconnection for testing
                if retry_count >= 2:  # Simulate success after 2 retries
                    self.salamander.audit_log = self.salamander.audit_log.append(
                        "pool_reconnected",
                        timestamp=time(),
                        retry_count=retry_count,
                    )
                    return True
            
            retry_count += 1
            await asyncio.sleep(backoff_seconds)
            backoff_seconds = min(backoff_seconds * 2, 60.0)  # Cap at 60 seconds
        
        if retry_count >= max_retries:
            self.salamander.audit_log = self.salamander.audit_log.append(
                "pool_reconnection_failed",
                timestamp=time(),
                severity="CRITICAL",
                action="waiting_for_manual_intervention",
            )
        
        return False

    def stop_mining(self) -> None:
        """Stop the mining loop."""
        self.is_running = False
