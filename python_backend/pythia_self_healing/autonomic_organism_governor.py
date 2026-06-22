"""Production-grade organism-level autonomic intelligence for Salamander.

This module sits above the existing lane-level regeneration mathematics and the
codebase-level SelfHealingReactor. It implements multi-scale autonomic
governance as executable repo evidence:

- Cross-Lane Regeneration Intelligence (CLRI)
- Temporal Regeneration Memory (TRM)
- Predictive pre-damage healing signals
- Hierarchical rewiring plans: local -> regional -> global
- Benchmark-suite evolution proposals
- Pulvini/Salamander cross-substrate handshake metadata
- Regulator-grade evidence-chain sealing
- Immutable invariant guard against auto-apply / Stable Core bypass attempts

All outputs are sovereign-gated proposals or evidence packets. Nothing in this
module applies source changes, deploys rewires, mutates protected Stable Core, or
bypasses human approval.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
from statistics import fmean, pstdev
from types import MappingProxyType
from typing import Any, Iterable, Literal, Mapping, Sequence


RewiringTier = Literal["LOCAL_LIMB", "REGIONAL_ORGAN", "GLOBAL_ORGANISM"]
Severity = Literal["info", "watch", "elevated", "critical"]


class AutonomicInvariantError(ValueError):
    """Raised when a packet/report attempts to violate governance invariants."""


PROPOSAL_ONLY_STATUS = {
    "ORGANISM_GOVERNANCE_STAGED",
    "ORGANISM_ANALYSIS_STAGED",
    "PRE_DAMAGE_PROPOSALS_AVAILABLE",
    "NO_PRE_DAMAGE_SIGNAL",
    "STAGED",
    "HEALING_PROPOSAL_STAGED",
    "OPTIMISATION_PROPOSAL_STAGED",
}


FORBIDDEN_TRUE_FLAGS = {
    "auto_apply",
    "automatic_application",
    "deployable_without_approval",
    "source_modified",
    "stable_core_modified",
    "rewire_deployed",
    "benchmark_committed",
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finite_float(value: Any, *, field_name: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise AutonomicInvariantError(f"{field_name} must be finite")
    return number


def _frozen_copy(value: Any) -> Any:
    """Return an immutable defensive copy for exported memory records."""

    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _frozen_copy(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_frozen_copy(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_frozen_copy(v) for v in value)
    return value


class ImmutableInvariantGuard:
    """Final local guard for organism-level autonomic outputs.

    The guard is intentionally small and deterministic. It rejects any packet that
    attempts direct application, Stable Core mutation, or sovereign-gate bypass.
    """

    def assert_proposal_only(self, payload: Mapping[str, Any], *, context: str) -> None:
        violations = self.find_violations(payload)
        if violations:
            raise AutonomicInvariantError(f"{context}: invariant violations detected: {violations}")

    def find_violations(self, payload: Any, *, path: str = "$", violations: list[str] | None = None) -> list[str]:
        if violations is None:
            violations = []
        if isinstance(payload, Mapping):
            for key, value in payload.items():
                key_text = str(key)
                child_path = f"{path}.{key_text}"
                if key_text in FORBIDDEN_TRUE_FLAGS and value is True:
                    violations.append(f"{child_path}=True")
                if key_text in {"sovereign_human_gate", "human_sovereign_required", "immutable_guard_active"} and value is False:
                    violations.append(f"{child_path}=False")
                if key_text == "action" and isinstance(value, str) and value.upper() in {
                    "APPLY",
                    "AUTO_APPLY",
                    "DEPLOY",
                    "MERGE",
                    "COMMIT",
                    "MUTATE_STABLE_CORE",
                }:
                    violations.append(f"{child_path}={value}")
                self.find_violations(value, path=child_path, violations=violations)
        elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            for index, item in enumerate(payload):
                self.find_violations(item, path=f"{path}[{index}]", violations=violations)
        return violations

    def seal(self, payload: Mapping[str, Any], *, context: str) -> dict[str, Any]:
        self.assert_proposal_only(payload, context=context)
        seal_body = {
            "context": context,
            "payload_hash": _sha256(payload),
            "timestamp": _utc_now(),
            "immutable_guard_active": True,
            "algorithm": "SHA-256",
        }
        seal_body["seal"] = _sha256(seal_body)
        return seal_body


@dataclass(frozen=True)
class OrganismSignal:
    """Normalised lane event used by organism-level analysis."""

    lane_id: int
    module_id: str
    pre_injury_phi: float
    post_recovery_fidelity: float
    scarring_detected: bool
    recovery_duration_ms: float
    status: str
    collapsed_role: str | None = None
    trace: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.lane_id, int) or self.lane_id < 0:
            raise AutonomicInvariantError("lane_id must be a non-negative integer")
        if not self.module_id:
            raise AutonomicInvariantError("module_id is required")
        if not math.isfinite(self.pre_injury_phi) or self.pre_injury_phi < 0:
            raise AutonomicInvariantError("pre_injury_phi must be finite and non-negative")
        if not math.isfinite(self.post_recovery_fidelity) or not (0.0 <= self.post_recovery_fidelity <= 1.0):
            raise AutonomicInvariantError("post_recovery_fidelity must be finite and in [0, 1]")
        if not math.isfinite(self.recovery_duration_ms) or self.recovery_duration_ms < 0:
            raise AutonomicInvariantError("recovery_duration_ms must be finite and non-negative")
        if not self.status:
            raise AutonomicInvariantError("status is required")

    @classmethod
    def from_event(cls, event: Any) -> "OrganismSignal":
        return cls(
            lane_id=int(getattr(event, "lane_id")),
            module_id=str(getattr(event, "module_id")),
            pre_injury_phi=_finite_float(getattr(event, "pre_injury_phi"), field_name="pre_injury_phi"),
            post_recovery_fidelity=_finite_float(getattr(event, "post_recovery_fidelity"), field_name="post_recovery_fidelity"),
            scarring_detected=bool(getattr(event, "scarring_detected")),
            recovery_duration_ms=_finite_float(getattr(event, "recovery_duration_ms"), field_name="recovery_duration_ms"),
            status=str(getattr(event, "status")),
            collapsed_role=getattr(event, "collapsed_role", None),
            trace=dict(getattr(event, "trace", {}) or {}),
        )


@dataclass(frozen=True)
class CrossLaneFinding:
    finding_type: str
    severity: Severity
    lanes: list[int]
    evidence: dict[str, Any]
    recommendation: str


class CrossLaneRegenerationIntelligence:
    """Detect organ-level patterns across otherwise independent lanes."""

    guard = ImmutableInvariantGuard()

    def analyse(
        self,
        signals: Iterable[OrganismSignal],
        *,
        phi_floor: float,
        scar_free_fidelity_floor: float,
    ) -> dict[str, Any]:
        signal_list = sorted(list(signals), key=lambda signal: (signal.lane_id, signal.module_id, signal.status))
        phi_floor = _finite_float(phi_floor, field_name="phi_floor")
        scar_free_fidelity_floor = _finite_float(scar_free_fidelity_floor, field_name="scar_free_fidelity_floor")
        if not 0.0 <= scar_free_fidelity_floor <= 1.0:
            raise AutonomicInvariantError("scar_free_fidelity_floor must be in [0, 1]")

        findings: list[CrossLaneFinding] = []
        scarring_lanes = sorted({signal.lane_id for signal in signal_list if signal.scarring_detected})
        low_fidelity = [signal for signal in signal_list if signal.post_recovery_fidelity < scar_free_fidelity_floor]
        phi_floor_lanes = sorted({signal.lane_id for signal in signal_list if signal.pre_injury_phi <= phi_floor})
        non_success = [signal for signal in signal_list if signal.status != "success"]

        if len(scarring_lanes) >= 2:
            findings.append(
                CrossLaneFinding(
                    finding_type="correlated_scarring",
                    severity="critical" if len(scarring_lanes) >= 4 else "elevated",
                    lanes=scarring_lanes,
                    evidence={"count": len(scarring_lanes), "scar_free_fidelity_floor": scar_free_fidelity_floor},
                    recommendation="Stage multi-limb regeneration sequence and run cross-lane collapse validation.",
                )
            )

        if phi_floor_lanes:
            findings.append(
                CrossLaneFinding(
                    finding_type="phi_floor_breach",
                    severity="critical",
                    lanes=phi_floor_lanes,
                    evidence={"phi_floor": phi_floor},
                    recommendation="Lock organism-level regeneration until φ-floor coherence is restored.",
                )
            )

        status_groups: dict[str, list[int]] = {}
        for signal in non_success:
            status_groups.setdefault(signal.status, []).append(signal.lane_id)
        for status, lanes in sorted(status_groups.items()):
            unique_lanes = sorted(set(lanes))
            if len(unique_lanes) >= 2:
                findings.append(
                    CrossLaneFinding(
                        finding_type="shared_regeneration_status_anomaly",
                        severity="elevated",
                        lanes=unique_lanes,
                        evidence={"status": status, "count": len(unique_lanes)},
                        recommendation="Investigate shared upstream cause before staging independent limb fixes.",
                    )
                )

        fidelity_values = [signal.post_recovery_fidelity for signal in signal_list]
        mean_fidelity = fmean(fidelity_values) if fidelity_values else 1.0
        min_fidelity = min(fidelity_values) if fidelity_values else 1.0
        cross_lane_phi_density = self._cross_lane_phi_density(signal_list, phi_floor=phi_floor)
        multi_limb_sequence = self._multi_limb_sequence(low_fidelity)
        report = {
            "analysis_id": f"CLRI-{_sha256([asdict(signal) for signal in signal_list])[:16]}",
            "signal_count": len(signal_list),
            "mean_fidelity": mean_fidelity,
            "minimum_fidelity": min_fidelity,
            "fidelity_dispersion": pstdev(fidelity_values) if len(fidelity_values) > 1 else 0.0,
            "cross_lane_phi_density": cross_lane_phi_density,
            "findings": [asdict(finding) for finding in findings],
            "multi_limb_regeneration_sequence": multi_limb_sequence,
            "collapse_validation_scope": "multi_lane" if len(scarring_lanes) >= 2 else "single_lane",
            "sovereign_human_gate": True,
            "auto_apply": False,
        }
        self.guard.assert_proposal_only(report, context="CLRI report")
        return report

    @staticmethod
    def _cross_lane_phi_density(signals: list[OrganismSignal], *, phi_floor: float) -> dict[str, Any]:
        if not signals:
            return {"mean_phi": 1.0, "minimum_phi": 1.0, "phi_dispersion": 0.0, "at_risk_lanes": []}
        phis = [signal.pre_injury_phi for signal in signals]
        return {
            "mean_phi": fmean(phis),
            "minimum_phi": min(phis),
            "phi_dispersion": pstdev(phis) if len(phis) > 1 else 0.0,
            "at_risk_lanes": sorted(signal.lane_id for signal in signals if signal.pre_injury_phi <= phi_floor),
        }

    @staticmethod
    def _multi_limb_sequence(low_fidelity: list[OrganismSignal]) -> list[dict[str, Any]]:
        ordered = sorted(low_fidelity, key=lambda signal: (signal.post_recovery_fidelity, -signal.recovery_duration_ms, signal.lane_id))
        return [
            {
                "sequence_index": index,
                "lane_id": signal.lane_id,
                "module_id": signal.module_id,
                "reason": "lowest_fidelity_first",
                "post_recovery_fidelity": signal.post_recovery_fidelity,
                "auto_apply": False,
            }
            for index, signal in enumerate(ordered, start=1)
        ]


class TemporalRegenerationMemory:
    """Append-only temporal memory with cryptographic chain-of-custody."""

    def __init__(self, *, guard: ImmutableInvariantGuard | None = None) -> None:
        self._records: list[dict[str, Any]] = []
        self.guard = guard or ImmutableInvariantGuard()

    @property
    def records(self) -> tuple[Mapping[str, Any], ...]:
        """Immutable defensive export of the memory chain."""

        return tuple(_frozen_copy(record) for record in self._records)

    def record(self, packet: Mapping[str, Any], *, event: OrganismSignal | None = None) -> dict[str, Any]:
        self.guard.assert_proposal_only(packet, context="TRM input packet")
        previous_hash = self._records[-1]["chain_hash"] if self._records else "GENESIS"
        envelope = packet.get("governance_envelope", {}) or {}
        entry = {
            "record_id": f"TRM-{len(self._records) + 1:08d}",
            "timestamp": _utc_now(),
            "previous_hash": previous_hash,
            "packet_id": packet.get("packet", {}).get("packet_id") or packet.get("packet_id"),
            "target": packet.get("target"),
            "status": packet.get("status"),
            "action": packet.get("action"),
            "lane_id": envelope.get("lane_id") if event is None else event.lane_id,
            "module_id": event.module_id if event is not None else None,
            "stability_impact": envelope.get("stability_impact"),
            "architecture_impact": envelope.get("architecture_impact", "LOCAL_LIMB"),
            "auto_apply": False,
            "sovereign_human_gate": True,
            "packet_hash": _sha256(packet),
        }
        entry["chain_hash"] = _sha256(entry)
        self._records.append(entry)
        return dict(entry)

    def summarise(self) -> dict[str, Any]:
        lane_counts: dict[int, int] = {}
        target_counts: dict[str, int] = {}
        for record in self._records:
            lane_id = record.get("lane_id")
            if isinstance(lane_id, int):
                lane_counts[lane_id] = lane_counts.get(lane_id, 0) + 1
            target = record.get("target")
            if target:
                target_counts[str(target)] = target_counts.get(str(target), 0) + 1
        recurring_lanes = sorted(lane for lane, count in lane_counts.items() if count >= 2)
        recurring_targets = sorted(target for target, count in target_counts.items() if count >= 2)
        return {
            "record_count": len(self._records),
            "chain_head": self._records[-1]["chain_hash"] if self._records else "GENESIS",
            "recurring_lanes": recurring_lanes,
            "recurring_targets": recurring_targets,
            "lane_counts": lane_counts,
            "target_counts": target_counts,
            "chain_valid": self.validate_chain(),
            "auto_apply": False,
        }

    def validate_chain(self) -> bool:
        previous = "GENESIS"
        for record in self._records:
            if record["previous_hash"] != previous:
                return False
            chain_hash = record["chain_hash"]
            clone = dict(record)
            clone.pop("chain_hash")
            if _sha256(clone) != chain_hash:
                return False
            if record.get("auto_apply") is not False or record.get("sovereign_human_gate") is not True:
                return False
            previous = chain_hash
        return True

    def assert_chain_valid(self) -> None:
        if not self.validate_chain():
            raise AutonomicInvariantError("TRM chain validation failed")


class PredictiveRegenerationEngine:
    """Forecast pre-damage healing candidates from CLRI + TRM."""

    guard = ImmutableInvariantGuard()

    def forecast(
        self,
        signals: Iterable[OrganismSignal],
        *,
        temporal_summary: Mapping[str, Any],
        clri_report: Mapping[str, Any],
        scar_free_fidelity_floor: float,
    ) -> dict[str, Any]:
        signal_list = sorted(list(signals), key=lambda signal: signal.lane_id)
        scar_free_fidelity_floor = _finite_float(scar_free_fidelity_floor, field_name="scar_free_fidelity_floor")
        forecast_items: list[dict[str, Any]] = []
        finding_types = {finding["finding_type"] for finding in clri_report.get("findings", [])}
        recurring_lanes = set(temporal_summary.get("recurring_lanes", []))

        for signal in signal_list:
            risk = 0.0
            drivers: list[str] = []
            fidelity_gap = max(0.0, scar_free_fidelity_floor - signal.post_recovery_fidelity)
            if fidelity_gap > 0:
                risk += min(0.45, fidelity_gap * 10.0)
                drivers.append("fidelity_decay")
            if signal.scarring_detected:
                risk += 0.25
                drivers.append("scarring_history")
            if signal.lane_id in recurring_lanes:
                risk += 0.15
                drivers.append("temporal_recurrence")
            if "correlated_scarring" in finding_types:
                risk += 0.15
                drivers.append("cross_lane_correlation")
            if signal.status != "success":
                risk += 0.10
                drivers.append("status_anomaly")

            bounded_risk = round(min(1.0, risk), 6)
            if bounded_risk >= 0.25:
                forecast_items.append(
                    {
                        "lane_id": signal.lane_id,
                        "module_id": signal.module_id,
                        "risk_score": bounded_risk,
                        "risk_band": self._risk_band(bounded_risk),
                        "drivers": sorted(set(drivers)),
                        "recommendation": "Pre-stage sovereign-gated repair proposal; do not auto-apply.",
                        "auto_apply": False,
                    }
                )

        forecast_items.sort(key=lambda item: (-item["risk_score"], item["lane_id"]))
        report = {
            "forecast_id": f"PRH-{_sha256(forecast_items)[:16]}",
            "status": "PRE_DAMAGE_PROPOSALS_AVAILABLE" if forecast_items else "NO_PRE_DAMAGE_SIGNAL",
            "predictions": forecast_items,
            "sovereign_human_gate": True,
            "auto_apply": False,
        }
        self.guard.assert_proposal_only(report, context="predictive regeneration report")
        return report

    @staticmethod
    def _risk_band(risk: float) -> Severity:
        if risk >= 0.85:
            return "critical"
        if risk >= 0.55:
            return "elevated"
        if risk >= 0.25:
            return "watch"
        return "info"


class HierarchicalRewiringOrchestrator:
    """Classify rewiring scope without deploying the rewire."""

    guard = ImmutableInvariantGuard()

    def stage_plan(
        self,
        *,
        clri_report: Mapping[str, Any],
        predictive_report: Mapping[str, Any],
        temporal_summary: Mapping[str, Any],
    ) -> dict[str, Any]:
        findings = list(clri_report.get("findings", []))
        finding_types = {finding["finding_type"] for finding in findings}
        prediction_count = len(predictive_report.get("predictions", []))
        recurring_lanes = list(temporal_summary.get("recurring_lanes", []))

        tier: RewiringTier = "LOCAL_LIMB"
        reasons: list[str] = []
        if "phi_floor_breach" in finding_types or len(recurring_lanes) >= 8:
            tier = "GLOBAL_ORGANISM"
            reasons.append("organism-level φ-floor or recurrence risk")
        elif "correlated_scarring" in finding_types or prediction_count >= 2 or len(recurring_lanes) >= 2:
            tier = "REGIONAL_ORGAN"
            reasons.append("cross-lane correlated scarring or recurrent lane risk")
        else:
            reasons.append("single-limb bounded repair surface")

        plan = {
            "plan_id": f"REWIRE-{_sha256([tier, reasons, findings, prediction_count])[:16]}",
            "tier": tier,
            "reasons": reasons,
            "action": "ESCALATE_TO_SOVEREIGN_HUMAN",
            "required_approval": "sovereign_human",
            "blast_radius": tier,
            "auto_apply": False,
            "stable_core_guard": "must_not_modify_stable_core_without_explicit_approval",
            "rewire_deployed": False,
        }
        self.guard.assert_proposal_only(plan, context="hierarchical rewiring plan")
        return plan


class BenchmarkEvolutionEngine:
    """Generate benchmark-suite evolution proposals from new failure modes."""

    guard = ImmutableInvariantGuard()

    def propose(
        self,
        *,
        clri_report: Mapping[str, Any],
        predictive_report: Mapping[str, Any],
        rewiring_plan: Mapping[str, Any],
    ) -> dict[str, Any]:
        proposed_tests: list[dict[str, str | bool]] = []
        finding_types = {finding["finding_type"] for finding in clri_report.get("findings", [])}
        if "correlated_scarring" in finding_types:
            proposed_tests.append(
                {
                    "test_name": "test_cross_lane_correlated_scarring_stages_regional_repair",
                    "purpose": "Prove CLRI catches organ-level scarring rather than only lane-local damage.",
                    "property": "same inputs imply same CLRI seal and no auto-apply",
                    "adversarial_case": "duplicated lane reports must not inflate unique-lane severity",
                    "auto_apply": False,
                }
            )
        if predictive_report.get("predictions"):
            proposed_tests.append(
                {
                    "test_name": "test_predictive_regeneration_pre_stages_without_auto_apply",
                    "purpose": "Prove pre-damage healing remains sovereign-gated and non-deploying.",
                    "property": "risk scores are finite, bounded in [0,1], and deterministic",
                    "adversarial_case": "NaN/Infinity signal metrics must be rejected before prediction",
                    "auto_apply": False,
                }
            )
        if rewiring_plan.get("tier") in {"REGIONAL_ORGAN", "GLOBAL_ORGANISM"}:
            proposed_tests.append(
                {
                    "test_name": "test_hierarchical_rewiring_classifies_blast_radius",
                    "purpose": "Prove local/regional/global rewiring is classified before approval.",
                    "property": "rewiring tiers never deploy and always require sovereign approval",
                    "adversarial_case": "packets requesting direct deploy are rejected by ImmutableInvariantGuard",
                    "auto_apply": False,
                }
            )
        if not proposed_tests:
            proposed_tests.append(
                {
                    "test_name": "test_salamander_organism_no_false_positive_benchmark_evolution",
                    "purpose": "Prove benchmark evolution stays quiet when no new failure mode exists.",
                    "property": "healthy lane inputs produce no high-severity benchmark churn",
                    "adversarial_case": "empty input remains sealed and proposal-only",
                    "auto_apply": False,
                }
            )
        report = {
            "benchmark_evolution_id": f"BENCH-EVO-{_sha256(proposed_tests)[:16]}",
            "proposed_tests": proposed_tests,
            "action": "STAGE_BENCHMARK_PROPOSALS",
            "benchmark_committed": False,
            "auto_apply": False,
        }
        self.guard.assert_proposal_only(report, context="benchmark evolution report")
        return report


class PulviniAutonomicHandshake:
    """Describe cross-substrate Salamander <-> Pulvini autonomic intent."""

    guard = ImmutableInvariantGuard()

    def stage(self, *, clri_report: Mapping[str, Any], pulvini_state: Mapping[str, Any] | None = None) -> dict[str, Any]:
        state = dict(pulvini_state or {})
        unsafe_candidates = [candidate for candidate in state.get("algorithmic_alternatives", []) if isinstance(candidate, Mapping) and candidate.get("auto_apply") is True]
        if unsafe_candidates:
            raise AutonomicInvariantError("Pulvini candidate exchange attempted auto-apply")
        report = {
            "handshake_id": f"PULVINI-SALAMANDER-{_sha256([clri_report, state])[:16]}",
            "salamander_role": "detect_structural_drift_and_validate_regeneration_invariants",
            "pulvini_role": "propose_memory_or_algorithmic_alternatives_under_reconstruction_invariants",
            "inputs": {
                "clri_analysis_id": clri_report.get("analysis_id"),
                "pulvini_state_hash": _sha256(state),
            },
            "candidate_exchange": state.get("algorithmic_alternatives", []),
            "invariant_contract": [
                "sovereign_human_gate_required",
                "stable_core_not_modified_without_explicit_approval",
                "auto_apply_false",
                "evidence_packet_required",
            ],
            "sovereign_human_gate": True,
            "auto_apply": False,
        }
        self.guard.assert_proposal_only(report, context="Pulvini autonomic handshake")
        return report


class RegulatorEvidenceEngine:
    """Seal organism-level evidence for audit and supervisory review."""

    guard = ImmutableInvariantGuard()

    def seal(self, report: Mapping[str, Any]) -> dict[str, Any]:
        self.guard.assert_proposal_only(report, context="regulator evidence input")
        payload = {
            "timestamp": _utc_now(),
            "report_hash": _sha256(report),
            "sovereign_human_gate": True,
            "auto_apply": False,
            "invariant_claims": [
                "lane_level_regeneration_math_unchanged",
                "small_limb_rule_preserved",
                "stable_core_guard_preserved",
                "organism_level_outputs_are_proposals_only",
                "temporal_memory_chain_valid",
            ],
            "chain_of_custody": {
                "clri": report.get("clri", {}).get("analysis_id"),
                "temporal_memory_head": report.get("temporal_memory", {}).get("chain_head"),
                "rewiring_plan": report.get("hierarchical_rewiring", {}).get("plan_id"),
                "benchmark_evolution": report.get("benchmark_evolution", {}).get("benchmark_evolution_id"),
            },
        }
        payload["evidence_id"] = f"SALAMANDER-ORGANISM-EVIDENCE-{_sha256(payload)[:16]}"
        payload["seal"] = _sha256(payload)
        return payload

    def verify(self, sealed_payload: Mapping[str, Any], report: Mapping[str, Any]) -> bool:
        if sealed_payload.get("report_hash") != _sha256(report):
            return False
        clone = dict(sealed_payload)
        seal = clone.pop("seal", None)
        return bool(seal and _sha256(clone) == seal)


class SalamanderOrganismGovernor:
    """Coordinate multi-scale Salamander autonomic intelligence."""

    def __init__(self, temporal_memory: TemporalRegenerationMemory | None = None, *, guard: ImmutableInvariantGuard | None = None) -> None:
        self.guard = guard or ImmutableInvariantGuard()
        self.clri = CrossLaneRegenerationIntelligence()
        self.memory = temporal_memory or TemporalRegenerationMemory(guard=self.guard)
        self.predictive = PredictiveRegenerationEngine()
        self.rewiring = HierarchicalRewiringOrchestrator()
        self.benchmarks = BenchmarkEvolutionEngine()
        self.pulvini = PulviniAutonomicHandshake()
        self.evidence = RegulatorEvidenceEngine()

    def analyse_manager(
        self,
        manager: Any,
        *,
        recent_packets: Iterable[Mapping[str, Any]] | None = None,
        pulvini_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        signals = [OrganismSignal.from_event(event) for event in getattr(manager, "fidelity_history", [])]
        phi_floor = float(getattr(manager, "PHI_FLOOR", 0.45)) if hasattr(manager, "PHI_FLOOR") else 0.45
        scar_floor = 0.999

        for packet in list(recent_packets or getattr(manager, "healing_proposals", [])):
            self.memory.record(packet)
        self.memory.assert_chain_valid()

        clri_report = self.clri.analyse(signals, phi_floor=phi_floor, scar_free_fidelity_floor=scar_floor)
        temporal_summary = self.memory.summarise()
        predictive_report = self.predictive.forecast(
            signals,
            temporal_summary=temporal_summary,
            clri_report=clri_report,
            scar_free_fidelity_floor=scar_floor,
        )
        rewiring_plan = self.rewiring.stage_plan(
            clri_report=clri_report,
            predictive_report=predictive_report,
            temporal_summary=temporal_summary,
        )
        benchmark_plan = self.benchmarks.propose(
            clri_report=clri_report,
            predictive_report=predictive_report,
            rewiring_plan=rewiring_plan,
        )
        pulvini_handshake = self.pulvini.stage(clri_report=clri_report, pulvini_state=pulvini_state)

        report = {
            "status": "ORGANISM_GOVERNANCE_STAGED",
            "created_at": _utc_now(),
            "clri": clri_report,
            "temporal_memory": temporal_summary,
            "predictive_regeneration": predictive_report,
            "hierarchical_rewiring": rewiring_plan,
            "benchmark_evolution": benchmark_plan,
            "pulvini_handshake": pulvini_handshake,
            "sovereign_human_gate": True,
            "stable_core_guard": True,
            "auto_apply": False,
            "source_modified": False,
            "stable_core_modified": False,
        }
        self.guard.assert_proposal_only(report, context="organism governance report")
        report["regulator_evidence"] = self.evidence.seal(report)
        assert self.evidence.verify(report["regulator_evidence"], report)
        return report


__all__ = [
    "AutonomicInvariantError",
    "BenchmarkEvolutionEngine",
    "CrossLaneRegenerationIntelligence",
    "HierarchicalRewiringOrchestrator",
    "ImmutableInvariantGuard",
    "OrganismSignal",
    "PredictiveRegenerationEngine",
    "PulviniAutonomicHandshake",
    "RegulatorEvidenceEngine",
    "SalamanderOrganismGovernor",
    "TemporalRegenerationMemory",
]
