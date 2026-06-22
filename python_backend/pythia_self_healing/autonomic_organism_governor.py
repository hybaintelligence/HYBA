"""Organism-level autonomic intelligence for Salamander.

This module sits above the existing lane-level regeneration mathematics and the
codebase-level SelfHealingReactor. It implements the next frontier as executable
repo evidence:

- Cross-Lane Regeneration Intelligence (CLRI)
- Temporal Regeneration Memory (TRM)
- Predictive pre-damage healing signals
- Hierarchical rewiring plans: local -> regional -> global
- Benchmark-suite evolution proposals
- Pulvini/Salamander cross-substrate handshake metadata
- Regulator-grade evidence-chain sealing

All outputs are sovereign-gated proposals or evidence packets. Nothing in this
module applies source changes, deploys rewires, or bypasses human approval.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from statistics import fmean
from typing import Any, Iterable, Literal


RewiringTier = Literal["LOCAL_LIMB", "REGIONAL_ORGAN", "GLOBAL_ORGANISM"]
Severity = Literal["info", "watch", "elevated", "critical"]


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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

    @classmethod
    def from_event(cls, event: Any) -> "OrganismSignal":
        return cls(
            lane_id=int(getattr(event, "lane_id")),
            module_id=str(getattr(event, "module_id")),
            pre_injury_phi=float(getattr(event, "pre_injury_phi")),
            post_recovery_fidelity=float(getattr(event, "post_recovery_fidelity")),
            scarring_detected=bool(getattr(event, "scarring_detected")),
            recovery_duration_ms=float(getattr(event, "recovery_duration_ms")),
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

    def analyse(
        self,
        signals: Iterable[OrganismSignal],
        *,
        phi_floor: float,
        scar_free_fidelity_floor: float,
    ) -> dict[str, Any]:
        signal_list = list(signals)
        findings: list[CrossLaneFinding] = []
        scarring_lanes = [signal.lane_id for signal in signal_list if signal.scarring_detected]
        low_fidelity = [
            signal
            for signal in signal_list
            if signal.post_recovery_fidelity < scar_free_fidelity_floor
        ]
        phi_floor_lanes = [signal.lane_id for signal in signal_list if signal.pre_injury_phi <= phi_floor]
        non_success = [signal for signal in signal_list if signal.status != "success"]

        if len(scarring_lanes) >= 2:
            findings.append(
                CrossLaneFinding(
                    finding_type="correlated_scarring",
                    severity="critical" if len(scarring_lanes) >= 4 else "elevated",
                    lanes=sorted(scarring_lanes),
                    evidence={"count": len(scarring_lanes), "scar_free_fidelity_floor": scar_free_fidelity_floor},
                    recommendation="Stage multi-limb regeneration sequence and run cross-lane collapse validation.",
                )
            )

        if phi_floor_lanes:
            findings.append(
                CrossLaneFinding(
                    finding_type="phi_floor_breach",
                    severity="critical",
                    lanes=sorted(phi_floor_lanes),
                    evidence={"phi_floor": phi_floor},
                    recommendation="Lock organism-level regeneration until φ-floor coherence is restored.",
                )
            )

        status_groups: dict[str, list[int]] = {}
        for signal in non_success:
            status_groups.setdefault(signal.status, []).append(signal.lane_id)
        for status, lanes in sorted(status_groups.items()):
            if len(lanes) >= 2:
                findings.append(
                    CrossLaneFinding(
                        finding_type="shared_regeneration_status_anomaly",
                        severity="elevated",
                        lanes=sorted(lanes),
                        evidence={"status": status, "count": len(lanes)},
                        recommendation="Investigate shared upstream cause before staging independent limb fixes.",
                    )
                )

        fidelity_values = [signal.post_recovery_fidelity for signal in signal_list]
        mean_fidelity = fmean(fidelity_values) if fidelity_values else 1.0
        min_fidelity = min(fidelity_values) if fidelity_values else 1.0
        cross_lane_phi_density = self._cross_lane_phi_density(signal_list, phi_floor=phi_floor)
        multi_limb_sequence = self._multi_limb_sequence(signal_list, low_fidelity)

        return {
            "analysis_id": f"CLRI-{_sha256([asdict(signal) for signal in signal_list])[:16]}",
            "signal_count": len(signal_list),
            "mean_fidelity": mean_fidelity,
            "minimum_fidelity": min_fidelity,
            "cross_lane_phi_density": cross_lane_phi_density,
            "findings": [asdict(finding) for finding in findings],
            "multi_limb_regeneration_sequence": multi_limb_sequence,
            "collapse_validation_scope": "multi_lane" if len(scarring_lanes) >= 2 else "single_lane",
            "sovereign_human_gate": True,
            "auto_apply": False,
        }

    @staticmethod
    def _cross_lane_phi_density(signals: list[OrganismSignal], *, phi_floor: float) -> dict[str, Any]:
        if not signals:
            return {"mean_phi": 1.0, "minimum_phi": 1.0, "at_risk_lanes": []}
        phis = [signal.pre_injury_phi for signal in signals]
        return {
            "mean_phi": fmean(phis),
            "minimum_phi": min(phis),
            "at_risk_lanes": sorted(signal.lane_id for signal in signals if signal.pre_injury_phi <= phi_floor),
        }

    @staticmethod
    def _multi_limb_sequence(
        signals: list[OrganismSignal],
        low_fidelity: list[OrganismSignal],
    ) -> list[dict[str, Any]]:
        ordered = sorted(
            low_fidelity,
            key=lambda signal: (signal.post_recovery_fidelity, -signal.recovery_duration_ms, signal.lane_id),
        )
        return [
            {
                "sequence_index": index,
                "lane_id": signal.lane_id,
                "module_id": signal.module_id,
                "reason": "lowest_fidelity_first",
                "post_recovery_fidelity": signal.post_recovery_fidelity,
            }
            for index, signal in enumerate(ordered, start=1)
        ]


class TemporalRegenerationMemory:
    """Append-only temporal memory with cryptographic chain-of-custody."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def record(self, packet: dict[str, Any], *, event: OrganismSignal | None = None) -> dict[str, Any]:
        previous_hash = self.records[-1]["chain_hash"] if self.records else "GENESIS"
        envelope = packet.get("governance_envelope", {}) or {}
        entry = {
            "record_id": f"TRM-{len(self.records) + 1:08d}",
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
            "auto_apply": bool(packet.get("auto_apply", False)),
            "sovereign_human_gate": bool(packet.get("sovereign_human_gate", True)),
            "packet_hash": _sha256(packet),
        }
        entry["chain_hash"] = _sha256(entry)
        self.records.append(entry)
        return entry

    def summarise(self) -> dict[str, Any]:
        lane_counts: dict[int, int] = {}
        target_counts: dict[str, int] = {}
        for record in self.records:
            lane_id = record.get("lane_id")
            if isinstance(lane_id, int):
                lane_counts[lane_id] = lane_counts.get(lane_id, 0) + 1
            target = record.get("target")
            if target:
                target_counts[str(target)] = target_counts.get(str(target), 0) + 1
        recurring_lanes = sorted(lane for lane, count in lane_counts.items() if count >= 2)
        recurring_targets = sorted(target for target, count in target_counts.items() if count >= 2)
        return {
            "record_count": len(self.records),
            "chain_head": self.records[-1]["chain_hash"] if self.records else "GENESIS",
            "recurring_lanes": recurring_lanes,
            "recurring_targets": recurring_targets,
            "lane_counts": lane_counts,
            "target_counts": target_counts,
            "chain_valid": self.validate_chain(),
        }

    def validate_chain(self) -> bool:
        previous = "GENESIS"
        for record in self.records:
            if record["previous_hash"] != previous:
                return False
            chain_hash = record["chain_hash"]
            clone = dict(record)
            clone.pop("chain_hash")
            if _sha256(clone) != chain_hash:
                return False
            previous = chain_hash
        return True


class PredictiveRegenerationEngine:
    """Forecast pre-damage healing candidates from CLRI + TRM."""

    def forecast(
        self,
        signals: Iterable[OrganismSignal],
        *,
        temporal_summary: dict[str, Any],
        clri_report: dict[str, Any],
        scar_free_fidelity_floor: float,
    ) -> dict[str, Any]:
        signal_list = list(signals)
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

            if risk >= 0.25:
                forecast_items.append(
                    {
                        "lane_id": signal.lane_id,
                        "module_id": signal.module_id,
                        "risk_score": round(min(1.0, risk), 6),
                        "drivers": drivers,
                        "recommendation": "Pre-stage sovereign-gated repair proposal; do not auto-apply.",
                    }
                )

        forecast_items.sort(key=lambda item: (-item["risk_score"], item["lane_id"]))
        return {
            "forecast_id": f"PRH-{_sha256(forecast_items)[:16]}",
            "status": "PRE_DAMAGE_PROPOSALS_AVAILABLE" if forecast_items else "NO_PRE_DAMAGE_SIGNAL",
            "predictions": forecast_items,
            "sovereign_human_gate": True,
            "auto_apply": False,
        }


class HierarchicalRewiringOrchestrator:
    """Classify rewiring scope without deploying the rewire."""

    def stage_plan(
        self,
        *,
        clri_report: dict[str, Any],
        predictive_report: dict[str, Any],
        temporal_summary: dict[str, Any],
    ) -> dict[str, Any]:
        findings = clri_report.get("findings", [])
        finding_types = {finding["finding_type"] for finding in findings}
        prediction_count = len(predictive_report.get("predictions", []))
        recurring_lanes = temporal_summary.get("recurring_lanes", [])

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

        return {
            "plan_id": f"REWIRE-{_sha256([tier, reasons, findings, prediction_count])[:16]}",
            "tier": tier,
            "reasons": reasons,
            "action": "ESCALATE_TO_SOVEREIGN_HUMAN",
            "required_approval": "sovereign_human",
            "blast_radius": tier,
            "auto_apply": False,
            "stable_core_guard": "must_not_modify_stable_core_without_explicit_approval",
        }


class BenchmarkEvolutionEngine:
    """Generate benchmark-suite evolution proposals from new failure modes."""

    def propose(
        self,
        *,
        clri_report: dict[str, Any],
        predictive_report: dict[str, Any],
        rewiring_plan: dict[str, Any],
    ) -> dict[str, Any]:
        proposed_tests: list[dict[str, str]] = []
        finding_types = {finding["finding_type"] for finding in clri_report.get("findings", [])}
        if "correlated_scarring" in finding_types:
            proposed_tests.append(
                {
                    "test_name": "test_cross_lane_correlated_scarring_stages_regional_repair",
                    "purpose": "Prove CLRI catches organ-level scarring rather than only lane-local damage.",
                }
            )
        if predictive_report.get("predictions"):
            proposed_tests.append(
                {
                    "test_name": "test_predictive_regeneration_pre_stages_without_auto_apply",
                    "purpose": "Prove pre-damage healing remains sovereign-gated and non-deploying.",
                }
            )
        if rewiring_plan.get("tier") in {"REGIONAL_ORGAN", "GLOBAL_ORGANISM"}:
            proposed_tests.append(
                {
                    "test_name": "test_hierarchical_rewiring_classifies_blast_radius",
                    "purpose": "Prove local/regional/global rewiring is classified before approval.",
                }
            )
        if not proposed_tests:
            proposed_tests.append(
                {
                    "test_name": "test_salamander_organism_no_false_positive_benchmark_evolution",
                    "purpose": "Prove benchmark evolution stays quiet when no new failure mode exists.",
                }
            )
        return {
            "benchmark_evolution_id": f"BENCH-EVO-{_sha256(proposed_tests)[:16]}",
            "proposed_tests": proposed_tests,
            "action": "STAGE_BENCHMARK_PROPOSALS",
            "auto_apply": False,
        }


class PulviniAutonomicHandshake:
    """Describe cross-substrate Salamander <-> Pulvini autonomic intent."""

    def stage(self, *, clri_report: dict[str, Any], pulvini_state: dict[str, Any] | None = None) -> dict[str, Any]:
        state = pulvini_state or {}
        return {
            "handshake_id": f"PULVINI-SALAMANDER-{_sha256([clri_report, state])[:16]}",
            "salmander_role": "detect_structural_drift_and_validate_regeneration_invariants",
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
            "auto_apply": False,
        }


class RegulatorEvidenceEngine:
    """Seal organism-level evidence for audit and supervisory review."""

    def seal(self, report: dict[str, Any]) -> dict[str, Any]:
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


class SalamanderOrganismGovernor:
    """Coordinate multi-scale Salamander autonomic intelligence."""

    def __init__(self, temporal_memory: TemporalRegenerationMemory | None = None) -> None:
        self.clri = CrossLaneRegenerationIntelligence()
        self.memory = temporal_memory or TemporalRegenerationMemory()
        self.predictive = PredictiveRegenerationEngine()
        self.rewiring = HierarchicalRewiringOrchestrator()
        self.benchmarks = BenchmarkEvolutionEngine()
        self.pulvini = PulviniAutonomicHandshake()
        self.evidence = RegulatorEvidenceEngine()

    def analyse_manager(
        self,
        manager: Any,
        *,
        recent_packets: Iterable[dict[str, Any]] | None = None,
        pulvini_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        signals = [OrganismSignal.from_event(event) for event in getattr(manager, "fidelity_history", [])]
        phi_floor = float(getattr(manager, "PHI_FLOOR", 0.45)) if hasattr(manager, "PHI_FLOOR") else 0.45
        scar_floor = 0.999

        for packet in list(recent_packets or getattr(manager, "healing_proposals", [])):
            self.memory.record(packet)

        clri_report = self.clri.analyse(
            signals,
            phi_floor=phi_floor,
            scar_free_fidelity_floor=scar_floor,
        )
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
        }
        report["regulator_evidence"] = self.evidence.seal(report)
        return report
