"""Salamander frontier primitives for evidence-first autonomous adaptation.

The classes in this module intentionally avoid live pool/network side effects.
They model the frontier behaviours as deterministic, auditable transformations:

* evidence-based regeneration from immutable audit entries
* distributed agent coherence from a shared evidence trail
* adaptive phi tuning from reversible compression experiments
* self-scaling worker counts from measured marginal hashrate benefit
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from math import sqrt
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


@dataclass(frozen=True)
class PhiExperiment:
    phi_value: float
    compression_ratio: float
    reconstruction_error: float
    score: float


class AdaptivePhiTuning:
    """Experiment with phi variants and adopt only measured improvements."""

    def __init__(self, phi_current: float = PHI, improvement_threshold: float = 0.05) -> None:
        self.phi_current = float(phi_current)
        self.improvement_threshold = float(improvement_threshold)

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
            self.phi_current = best.phi_value
        return self.phi_current, improved, best


class SelfScalingWorkerPool:
    """Find worker count where marginal hashrate benefit falls below threshold."""

    def __init__(self, marginal_benefit_threshold: float = 0.02) -> None:
        self.marginal_benefit_threshold = float(marginal_benefit_threshold)

    def find_optimal_worker_count(self, hashrate_by_worker_count: dict[int, float]) -> int:
        optimal = 1
        previous = 0.0
        for count in sorted(hashrate_by_worker_count):
            rate = hashrate_by_worker_count[count]
            benefit = (rate - previous) / max(previous, 1.0)
            if benefit >= self.marginal_benefit_threshold:
                optimal = count
                previous = rate
            else:
                break
        return optimal


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
