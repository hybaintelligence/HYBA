"""Finance Sovereign Audit demo for PYTHIA.

This module adapts the PYTHIA sovereign-audit pattern to a regulated finance
candidate. It is deliberately non-executing: it does not approve trades, issue
legal opinions, issue Shariah rulings, calculate regulatory capital, or perform
external actions. It produces an evidence packet for human Shariah/compliance
review.

The architecture is the same pattern used by the mining and Stable Core work:

    candidate -> invariant screens -> synthetic criticism -> immutable guard
    -> sealed evidence packet -> sovereign human authority

Claim boundary: this is an audit-demonstration layer, not legal, regulatory,
religious, investment, capital, credit, or trading advice.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional

from .auditable_decision_bridge import AuditableDecisionBridge, ReviewCandidate
from .resonance_fabric import RefactorMode

SCHEMA_VERSION = "PYTHIA_FINANCE_SOVEREIGN_AUDIT_V1"


class FinanceAuditVerdict(str, Enum):
    """Final packet status."""

    REJECTED_BEFORE_STAGING = "rejected_before_staging"
    STAGED_FOR_SUPERVISION = "staged_for_supervision"


@dataclass(frozen=True)
class FinanceAuditCandidate:
    """A finance candidate submitted for non-executing sovereign audit."""

    candidate_id: str
    domain: str
    proposed_structure: str
    purpose: str
    economic_substance_score: float
    form_alignment_score: float
    uncertainty_score: float
    traceable_evidence_present: bool
    data_lineage_hash: str
    model_output_hash: str
    human_approval_required: bool = True
    mode: str = "review_only"
    requested_mode: str = RefactorMode.SUPERVISED_PATCH.value
    external_action_requested: bool = False
    proposed_core_symbol: str = "external_candidate"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FinanceInvariantFinding:
    """One finance/Shariah-style invariant screen result."""

    invariant_id: str
    name: str
    passed: bool
    severity: str
    reasoning: str
    audit_mapping: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FinanceSovereignAuditPacket:
    """Sealed packet for human compliance/Shariah review."""

    schema: str
    generated_at_unix: float
    candidate: Dict[str, Any]
    invariant_findings: List[Dict[str, Any]]
    synthetic_criticism: Dict[str, Any]
    bridge_report: Dict[str, Any]
    verdict: str
    human_review_required: bool
    automatic_action_allowed: bool
    recommended_next_action: str
    claim_boundary: str
    packet_hash: str = field(default="")

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["packet_hash"] = self.packet_hash or compute_packet_hash(payload)
        return payload


class FinanceSovereignInvariantRegistry:
    """Human-owned finance invariant screens for the demonstration packet.

    The registry intentionally uses simple, explainable screens rather than
    pretending to replace domain experts. Thresholds are policy inputs for a
    demo and must be replaced by client-approved rules in a real pilot.
    """

    substance_threshold = 0.85
    form_substance_drift_limit = 0.10
    uncertainty_limit = 0.35

    def evaluate(self, candidate: FinanceAuditCandidate) -> List[FinanceInvariantFinding]:
        substance_drift = candidate.form_alignment_score - candidate.economic_substance_score
        evidence_ok = (
            candidate.traceable_evidence_present
            and bool(candidate.data_lineage_hash)
            and bool(candidate.model_output_hash)
        )
        return [
            FinanceInvariantFinding(
                invariant_id="SUBSTANCE_OVER_FORM",
                name="Substance-over-form integrity screen",
                passed=(
                    candidate.economic_substance_score >= self.substance_threshold
                    and substance_drift <= self.form_substance_drift_limit
                ),
                severity="blocker",
                reasoning=(
                    "Economic substance is aligned with contractual form."
                    if candidate.economic_substance_score >= self.substance_threshold and substance_drift <= self.form_substance_drift_limit
                    else (
                        "Potential substance-over-form drift: economic substance score "
                        f"{candidate.economic_substance_score:.2f}, form alignment score "
                        f"{candidate.form_alignment_score:.2f}, drift {substance_drift:.2f}."
                    )
                ),
                audit_mapping="Shariah governance demonstration: screen for form/substance drift; human Shariah authority required.",
            ),
            FinanceInvariantFinding(
                invariant_id="GHARAR_UNCERTAINTY_SCREEN",
                name="Excessive uncertainty screen",
                passed=candidate.uncertainty_score <= self.uncertainty_limit,
                severity="blocker",
                reasoning=(
                    "Uncertainty score is within the configured review threshold."
                    if candidate.uncertainty_score <= self.uncertainty_limit
                    else f"Uncertainty score {candidate.uncertainty_score:.2f} exceeds threshold {self.uncertainty_limit:.2f}."
                ),
                audit_mapping="Shariah governance demonstration: excessive uncertainty screen; not a ruling.",
            ),
            FinanceInvariantFinding(
                invariant_id="TRACEABLE_EVIDENCE",
                name="Traceable evidence and lineage",
                passed=evidence_ok,
                severity="blocker",
                reasoning=(
                    "Traceable evidence, data-lineage hash, and model-output hash are present."
                    if evidence_ok
                    else "Traceable evidence or replay hashes are missing."
                ),
                audit_mapping="Model-risk governance mapping: evidence lineage and replayability for validation review.",
            ),
            FinanceInvariantFinding(
                invariant_id="HUMAN_APPROVAL_REQUIRED",
                name="Human authority preserved",
                passed=candidate.human_approval_required,
                severity="blocker",
                reasoning=(
                    "Human Shariah/compliance authority is explicitly required."
                    if candidate.human_approval_required
                    else "Human approval flag is absent."
                ),
                audit_mapping="Four-eyes / governance mapping: the system stages evidence only.",
            ),
            FinanceInvariantFinding(
                invariant_id="NO_AUTOMATIC_EXTERNAL_ACTION",
                name="No automatic external action",
                passed=(candidate.mode == "review_only" and not candidate.external_action_requested),
                severity="blocker",
                reasoning=(
                    "Candidate is review-only and requests no external action."
                    if candidate.mode == "review_only" and not candidate.external_action_requested
                    else "Candidate requests or implies external action; reject before staging."
                ),
                audit_mapping="Operational resilience mapping: audit layer cannot execute the candidate.",
            ),
        ]


class FinanceSyntheticAdversary:
    """Internal critic for finance audit candidates."""

    def criticize(self, candidate: FinanceAuditCandidate, findings: List[FinanceInvariantFinding]) -> Dict[str, Any]:
        failed = [finding.invariant_id for finding in findings if not finding.passed]
        if failed:
            return {
                "agent": "FinanceSyntheticAdversary",
                "action": "CRITICISM_GENERATED",
                "failed_invariants": failed,
                "outcome": "PATHWAY_BLOCKED",
                "reasoning": "Candidate failed one or more configured invariant screens before human-supervised staging.",
                "counterfactual_next_step": "Rebuild the candidate with stronger evidence lineage, lower uncertainty, and clearer substance/form alignment.",
            }
        return {
            "agent": "FinanceSyntheticAdversary",
            "action": "NO_BLOCKER_CRITICISM",
            "failed_invariants": [],
            "outcome": "STAGE_FOR_SUPERVISION",
            "reasoning": "No configured blocker failed. The packet is staged for human review only.",
            "counterfactual_next_step": "Human reviewer may request additional stress tests or domain-specific rule calibration.",
        }


def _bridge_candidate(candidate: FinanceAuditCandidate) -> ReviewCandidate:
    """Project the finance candidate into the generic PYTHIA audit bridge."""

    return ReviewCandidate(
        candidate_id=candidate.candidate_id,
        domain=candidate.domain,
        recommendation="Stage finance audit packet for human review; do not execute.",
        objective=candidate.purpose,
        expected_gain=0.0289,
        rationale=(
            "Finance/Shariah candidate is restricted to review-only staging with replay hashes and human authority. "
            + candidate.notes
        ).strip(),
        requested_mode=candidate.requested_mode,
        evidence={
            "traceable_evidence_present": candidate.traceable_evidence_present,
            "mode": candidate.mode,
            "human_approval_required": candidate.human_approval_required,
            "data_lineage_hash": candidate.data_lineage_hash,
            "model_output_hash": candidate.model_output_hash,
            "proposed_core_symbol": candidate.proposed_core_symbol,
        },
    )


def compute_packet_hash(packet: Mapping[str, Any]) -> str:
    """Stable packet hash excluding wall-clock generation time and hash field."""

    payload = dict(packet)
    payload.pop("packet_hash", None)
    payload.pop("generated_at_unix", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def audit_finance_candidate(candidate: FinanceAuditCandidate) -> FinanceSovereignAuditPacket:
    """Generate a sealed non-executing finance audit packet."""

    registry = FinanceSovereignInvariantRegistry()
    findings = registry.evaluate(candidate)
    criticism = FinanceSyntheticAdversary().criticize(candidate, findings)
    bridge_report = AuditableDecisionBridge().audit(_bridge_candidate(candidate)).to_dict()
    blocker_failed = any(finding.severity == "blocker" and not finding.passed for finding in findings)
    bridge_rejected = bridge_report.get("verdict") == "rejected_before_staging"
    if blocker_failed or bridge_rejected:
        verdict = FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
        next_action = "Reject before staging; return candidate to domain expert for corrected evidence and structure."
    else:
        verdict = FinanceAuditVerdict.STAGED_FOR_SUPERVISION.value
        next_action = "Stage sealed packet for Shariah/compliance review; no automatic action permitted."

    payload = {
        "schema": SCHEMA_VERSION,
        "generated_at_unix": time.time(),
        "candidate": candidate.to_dict(),
        "invariant_findings": [finding.to_dict() for finding in findings],
        "synthetic_criticism": criticism,
        "bridge_report": bridge_report,
        "verdict": verdict,
        "human_review_required": True,
        "automatic_action_allowed": False,
        "recommended_next_action": next_action,
        "claim_boundary": (
            "Demonstration screening packet only. Not a Shariah ruling, legal opinion, regulatory determination, "
            "investment recommendation, capital calculation, trade instruction, or external action."
        ),
    }
    return FinanceSovereignAuditPacket(packet_hash=compute_packet_hash(payload), **payload)


def sample_shariah_candidate() -> FinanceAuditCandidate:
    """Candidate that passes configured demo screens and stages for supervision."""

    return FinanceAuditCandidate(
        candidate_id="FIN-SHARIAH-DEMO-001",
        domain="islamic_finance_dynamic_audit",
        proposed_structure="Real-asset Wakalah liquidity review candidate",
        purpose="Assess whether the candidate should be reviewed by a human Shariah/compliance authority.",
        economic_substance_score=0.91,
        form_alignment_score=0.93,
        uncertainty_score=0.22,
        traceable_evidence_present=True,
        data_lineage_hash="sha256:finance_lineage_demo_001",
        model_output_hash="sha256:finance_model_output_demo_001",
        notes="Demo candidate preserves human approval and does not request execution.",
    )


def adversarial_shariah_candidate() -> FinanceAuditCandidate:
    """Candidate designed to fail screens before staging."""

    return FinanceAuditCandidate(
        candidate_id="FIN-SHARIAH-ADVERSARY-001",
        domain="islamic_finance_dynamic_audit",
        proposed_structure="Commodity sequence review candidate with weak evidence lineage",
        purpose="Maximise convenience while asking the audit layer to skip review-only controls.",
        economic_substance_score=0.82,
        form_alignment_score=0.96,
        uncertainty_score=0.41,
        traceable_evidence_present=False,
        data_lineage_hash="",
        model_output_hash="",
        human_approval_required=False,
        mode="not_review_only",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY.value,
        external_action_requested=True,
        proposed_core_symbol="validate_constraints",
        notes="Adversarial fixture: should be rejected before staging.",
    )


def generate_finance_sovereign_packet(*, adversarial: bool = False) -> FinanceSovereignAuditPacket:
    """Generate the first finance sovereign audit packet."""

    candidate = adversarial_shariah_candidate() if adversarial else sample_shariah_candidate()
    return audit_finance_candidate(candidate)


__all__ = [
    "FinanceAuditCandidate",
    "FinanceAuditVerdict",
    "FinanceInvariantFinding",
    "FinanceSovereignAuditPacket",
    "FinanceSovereignInvariantRegistry",
    "FinanceSyntheticAdversary",
    "SCHEMA_VERSION",
    "adversarial_shariah_candidate",
    "audit_finance_candidate",
    "compute_packet_hash",
    "generate_finance_sovereign_packet",
    "sample_shariah_candidate",
]
