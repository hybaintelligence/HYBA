"""DIFC / AAOIFI Sukuk lifecycle drift simulation.

This module is deliberately inside the lift-out ``pythia_finance_audit`` package,
not ``pythia_mining``. It generates a read-only sequence of Sukuk audit packets
across lifecycle stages so a human Shariah Supervisory Board, trustee,
compliance function, or regulator-authorised reviewer can see where drift first
appears.

Boundary: this module never approves, issues, books, trades, files, executes, or
submits anything. It simulates criticism and sealed evidence only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from .difc_aaiofi_bridge import DIFCSukukCandidate, generate_difc_sukuk_audit_packet

SCHEMA_VERSION = "PYTHIA_DIFC_AAOIFI_SUKUK_LIFECYCLE_V1"
HASH_IGNORED_KEYS = {
    "generated_at_unix",
    "packet_hash",
    "difc_aaiofi_packet_hash",
    "lifecycle_packet_hash",
}


@dataclass(frozen=True)
class SukukLifecycleScenarioStep:
    """One candidate state in a Sukuk lifecycle simulation.

    The candidate remains portable and evidence-only. The simulation should be
    viewed as a product demo fixture, not as legal, Shariah, regulatory, capital,
    investment, credit, or trading advice.
    """

    step_id: str
    lifecycle_stage: str
    review_focus: str
    candidate: DIFCSukukCandidate

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["candidate"] = self.candidate.to_dict()
        return payload


def _canonicalise_for_hash(value: Any) -> Any:
    """Remove runtime timestamps and seal fields before stable hashing."""

    if isinstance(value, Mapping):
        return {
            str(key): _canonicalise_for_hash(item)
            for key, item in value.items()
            if str(key) not in HASH_IGNORED_KEYS
        }
    if isinstance(value, list):
        return [_canonicalise_for_hash(item) for item in value]
    return value


def compute_lifecycle_hash(payload: Mapping[str, Any]) -> str:
    """Compute a stable lifecycle hash, excluding runtime and seal fields."""

    canonical_payload = _canonicalise_for_hash(payload)
    canonical = json.dumps(canonical_payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def sample_sukuk_lifecycle_scenario() -> List[SukukLifecycleScenarioStep]:
    """Return a deterministic five-step Sukuk lifecycle drift scenario.

    The sequence starts with a clean staged-review candidate, introduces a
    warning during continuity monitoring, then reaches blocker failures during a
    drift/restructuring review. This gives a client-safe demo of *when* the
    criticism ledger first changes state.
    """

    return [
        SukukLifecycleScenarioStep(
            step_id="01",
            lifecycle_stage="pre_issuance_structuring",
            review_focus="Initial GS 12 / SS 17 structure, ownership, SPV, trustee, SSSB, and evidence-lineage review.",
            candidate=DIFCSukukCandidate(
                candidate_id="DIFC-SUKUK-LIFE-001",
                sukuk_type="SUKUK_AL_WAKALA",
                proposed_structure="Pre-issuance Wakalah structure with asset-backing, trustee oversight, and SSSB escalation.",
                purpose="Stage pre-issuance Sukuk evidence for human SSSB/compliance review.",
                economic_substance_score=0.92,
                form_alignment_score=0.93,
                uncertainty_score=0.21,
                asset_backing_ratio=0.88,
                risk_sharing_score=0.70,
                spv_independence_score=0.80,
                trustee_oversight_present=True,
                sssb_review_required=True,
                lifecycle_stage="pre_issuance_structuring",
                traceable_evidence_present=True,
                data_lineage_hash="sha256:life_001_lineage",
                model_output_hash="sha256:life_001_model",
                notes="Lifecycle simulation fixture: initial clean staged-review state.",
            ),
        ),
        SukukLifecycleScenarioStep(
            step_id="02",
            lifecycle_stage="issuance_closing_review",
            review_focus="Closing review after subscriptions, asset evidence update, and trustee confirmation.",
            candidate=DIFCSukukCandidate(
                candidate_id="DIFC-SUKUK-LIFE-002",
                sukuk_type="SUKUK_AL_WAKALA",
                proposed_structure="Closing-stage Wakalah structure with preserved asset evidence and trustee oversight.",
                purpose="Stage issuance-closing evidence for human SSSB/compliance review.",
                economic_substance_score=0.90,
                form_alignment_score=0.92,
                uncertainty_score=0.24,
                asset_backing_ratio=0.85,
                risk_sharing_score=0.63,
                spv_independence_score=0.77,
                trustee_oversight_present=True,
                sssb_review_required=True,
                lifecycle_stage="issuance_closing_review",
                traceable_evidence_present=True,
                data_lineage_hash="sha256:life_002_lineage",
                model_output_hash="sha256:life_002_model",
                notes="Lifecycle simulation fixture: closing review remains staged for human review only.",
            ),
        ),
        SukukLifecycleScenarioStep(
            step_id="03",
            lifecycle_stage="continuity_monitoring_warning",
            review_focus="Ongoing monitoring where risk-sharing begins to resemble debt-like fixed-return behaviour.",
            candidate=DIFCSukukCandidate(
                candidate_id="DIFC-SUKUK-LIFE-003",
                sukuk_type="SUKUK_AL_WAKALA",
                proposed_structure="Continuity-stage Wakalah structure with emerging fixed-return correlation but no configured blocker failure.",
                purpose="Surface continuity-monitoring criticism for human SSSB/compliance review.",
                economic_substance_score=0.88,
                form_alignment_score=0.92,
                uncertainty_score=0.30,
                asset_backing_ratio=0.82,
                risk_sharing_score=0.55,
                spv_independence_score=0.74,
                trustee_oversight_present=True,
                sssb_review_required=True,
                lifecycle_stage="continuity_monitoring_warning",
                traceable_evidence_present=True,
                data_lineage_hash="sha256:life_003_lineage",
                model_output_hash="sha256:life_003_model",
                notes="Lifecycle simulation fixture: first warning state; no automatic action permitted.",
            ),
        ),
        SukukLifecycleScenarioStep(
            step_id="04",
            lifecycle_stage="asset_drift_restructuring_trigger",
            review_focus="Asset-backing, SPV independence, substance, and uncertainty drift requiring human restructuring review.",
            candidate=DIFCSukukCandidate(
                candidate_id="DIFC-SUKUK-LIFE-004",
                sukuk_type="SUKUK_AL_WAKALA",
                proposed_structure="Continuity-stage Wakalah structure after asset substitution and weaker SPV independence evidence.",
                purpose="Detect blocker drift and stage a rejection-before-staging packet for human owners.",
                economic_substance_score=0.83,
                form_alignment_score=0.96,
                uncertainty_score=0.38,
                asset_backing_ratio=0.76,
                risk_sharing_score=0.49,
                spv_independence_score=0.66,
                trustee_oversight_present=True,
                sssb_review_required=True,
                lifecycle_stage="asset_drift_restructuring_trigger",
                traceable_evidence_present=True,
                data_lineage_hash="sha256:life_004_lineage",
                model_output_hash="sha256:life_004_model",
                notes="Lifecycle simulation fixture: first blocker state; reject before staging, no execution.",
            ),
        ),
        SukukLifecycleScenarioStep(
            step_id="05",
            lifecycle_stage="maturity_or_remediation_review",
            review_focus="Remediation or maturity review with missing evidence lineage and continuing ownership/substance weaknesses.",
            candidate=DIFCSukukCandidate(
                candidate_id="DIFC-SUKUK-LIFE-005",
                sukuk_type="SUKUK_AL_WAKALA",
                proposed_structure="Remediation-stage structure with unresolved asset and evidence-lineage concerns.",
                purpose="Keep the lifecycle packet blocked until human owners restore evidence and structure.",
                economic_substance_score=0.81,
                form_alignment_score=0.95,
                uncertainty_score=0.40,
                asset_backing_ratio=0.72,
                risk_sharing_score=0.44,
                spv_independence_score=0.61,
                trustee_oversight_present=False,
                sssb_review_required=True,
                lifecycle_stage="maturity_or_remediation_review",
                traceable_evidence_present=False,
                data_lineage_hash="",
                model_output_hash="",
                notes="Lifecycle simulation fixture: remediation remains blocked; human authority preserved.",
            ),
        ),
    ]


def _finding_ids_by_status(packet: Mapping[str, Any], status: str) -> List[str]:
    return [
        str(finding.get("finding_id"))
        for finding in packet.get("difc_aaiofi_findings", [])
        if finding.get("status") == status
    ]


def simulate_sukuk_lifecycle_drift(
    scenario: Optional[Iterable[SukukLifecycleScenarioStep]] = None,
    *,
    include_packets: bool = True,
) -> Dict[str, Any]:
    """Generate a read-only lifecycle drift evidence bundle.

    ``include_packets`` keeps the default artifact self-contained. Set it to
    ``False`` for a compact board-facing summary while retaining per-step packet
    hashes and finding identifiers.
    """

    steps = list(scenario) if scenario is not None else sample_sukuk_lifecycle_scenario()
    timeline: List[Dict[str, Any]] = []
    first_warning_step_id: Optional[str] = None
    first_blocker_step_id: Optional[str] = None

    for step in steps:
        packet = generate_difc_sukuk_audit_packet(step.candidate)
        failed = _finding_ids_by_status(packet, "failed")
        warnings = _finding_ids_by_status(packet, "warning")
        passed = _finding_ids_by_status(packet, "passed")
        if warnings and first_warning_step_id is None:
            first_warning_step_id = step.step_id
        if failed and first_blocker_step_id is None:
            first_blocker_step_id = step.step_id

        entry: Dict[str, Any] = {
            "step_id": step.step_id,
            "lifecycle_stage": step.lifecycle_stage,
            "review_focus": step.review_focus,
            "candidate_id": step.candidate.candidate_id,
            "verdict": packet.get("verdict"),
            "action": "ESCALATE_TO_SOVEREIGN_HUMAN",
            "human_review_required": True,
            "automatic_action_allowed": False,
            "packet_hash": packet.get("difc_aaiofi_packet_hash"),
            "passed_findings": passed,
            "warning_findings": warnings,
            "failed_findings": failed,
        }
        if include_packets:
            entry["packet"] = packet
        timeline.append(entry)

    rejected = [entry for entry in timeline if entry["failed_findings"]]
    warnings = [entry for entry in timeline if entry["warning_findings"]]
    result: Dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "domain": "DIFC / AAOIFI Sukuk Lifecycle Drift Simulation",
        "purpose": "Show the first warning and first blocker in a Sukuk lifecycle using sealed evidence packets for human review only.",
        "timeline": timeline,
        "summary": {
            "total_steps": len(timeline),
            "warning_steps": len(warnings),
            "blocker_steps": len(rejected),
            "first_warning_step_id": first_warning_step_id,
            "first_blocker_step_id": first_blocker_step_id,
            "first_blocker_stage": next((entry["lifecycle_stage"] for entry in timeline if entry["step_id"] == first_blocker_step_id), None),
        },
        "human_review_required": True,
        "automatic_action_allowed": False,
        "recommended_next_action": (
            "Use the first-warning and first-blocker steps as a read-only criticism ledger for SSSB, trustee, compliance, and counsel review."
        ),
        "claim_boundary": (
            "Simulation and evidence bundle only. Not a fatwa, Shariah ruling, legal opinion, regulatory determination, capital calculation, "
            "investment recommendation, issuance approval, trade instruction, booking instruction, or external filing."
        ),
    }
    result["lifecycle_packet_hash"] = compute_lifecycle_hash(result)
    return result


__all__ = [
    "SCHEMA_VERSION",
    "SukukLifecycleScenarioStep",
    "compute_lifecycle_hash",
    "sample_sukuk_lifecycle_scenario",
    "simulate_sukuk_lifecycle_drift",
]
