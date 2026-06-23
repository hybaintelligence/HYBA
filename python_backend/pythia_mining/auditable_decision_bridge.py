"""Auditable Decision Bridge for PYTHIA sovereign review.

PYTHIA may inspect and criticize an external recommendation. This module does not
perform any external action. It emits a sealed review report with evidence-lineage,
human-approval, and Stable Core guard checks.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .resonance_fabric import ImmutableInvariantGuard, RefactorDecision, RefactorMode

SCHEMA_VERSION = "PYTHIA_AUDITABLE_DECISION_BRIDGE_V1"


class ReviewVerdict(str, Enum):
    """Final sovereign-review verdict."""

    REJECTED_BEFORE_STAGING = "rejected_before_staging"
    STAGED_FOR_HUMAN_REVIEW = "staged_for_human_review"


class FindingSeverity(str, Enum):
    """Severity of an invariant finding."""

    BLOCKER = "blocker"
    WARNING = "warning"


@dataclass(frozen=True)
class DecisionInvariant:
    """A human-owned invariant that PYTHIA may test but not redefine."""

    invariant_id: str
    name: str
    description: str
    severity: str
    protected: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewCandidate:
    """External recommendation presented for sovereign audit."""

    candidate_id: str
    domain: str
    recommendation: str
    objective: str
    expected_gain: float
    rationale: str
    evidence: Mapping[str, Any]
    requested_mode: str = RefactorMode.SUPERVISED_PATCH.value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewFinding:
    """One invariant check result."""

    invariant_id: str
    passed: bool
    severity: str
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecisionAuditReport:
    """Sealed report for an external recommendation."""

    schema: str
    generated_at_unix: float
    candidate: Dict[str, Any]
    findings: List[Dict[str, Any]]
    guard_decision: Dict[str, Any]
    verdict: str
    criticism_summary: str
    human_review_required: bool
    automatic_action_allowed: bool
    recommended_next_action: str
    audit_hash: str = field(default="")

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["audit_hash"] = self.audit_hash or compute_audit_hash(payload)
        return payload


class DecisionInvariantRegistry:
    """Default invariant set for first external-domain deployment."""

    invariants: Sequence[DecisionInvariant] = (
        DecisionInvariant(
            invariant_id="TRACEABLE_EVIDENCE",
            name="Traceable evidence",
            description="The candidate must include traceable evidence when an external party is involved.",
            severity=FindingSeverity.BLOCKER.value,
        ),
        DecisionInvariant(
            invariant_id="REVIEW_CONTROL_PRIORITY",
            name="Review controls remain senior to optimization",
            description="The candidate must preserve review and audit controls.",
            severity=FindingSeverity.BLOCKER.value,
        ),
        DecisionInvariant(
            invariant_id="INFORMATION_INTEGRITY",
            name="Evidence lineage must be hash-addressable",
            description="The report must include data-lineage and model-output hashes for replayable review.",
            severity=FindingSeverity.BLOCKER.value,
        ),
        DecisionInvariant(
            invariant_id="HUMAN_APPROVAL_FOR_MATERIAL_ACTION",
            name="Human approval required for material action",
            description="The candidate may be staged, but material action requires human approval.",
            severity=FindingSeverity.BLOCKER.value,
        ),
        DecisionInvariant(
            invariant_id="NO_AUTOMATIC_ACTION",
            name="Audit bridge cannot perform external actions",
            description="The bridge may reject or stage; it must not perform the external action.",
            severity=FindingSeverity.BLOCKER.value,
        ),
    )

    _CONTROL_WEAKENING_TERMS = (
        "control_override",
        "review_removed",
        "audit_removed",
        "human_approval_removed",
    )

    def evaluate(self, candidate: ReviewCandidate) -> List[ReviewFinding]:
        """Evaluate invariants for a black-box recommendation."""

        evidence = dict(candidate.evidence)
        text = f"{candidate.objective} {candidate.rationale} {candidate.recommendation}".lower()
        control_weakening = any(term in text for term in self._CONTROL_WEAKENING_TERMS)
        review_only = (
            candidate.requested_mode != RefactorMode.AUTONOMOUS_APPLY.value
            and evidence.get("mode") == "review_only"
        )
        return [
            ReviewFinding(
                invariant_id="TRACEABLE_EVIDENCE",
                passed=bool(evidence.get("traceable_evidence_present")),
                severity=FindingSeverity.BLOCKER.value,
                reasoning=(
                    "Traceable evidence present."
                    if evidence.get("traceable_evidence_present")
                    else "Traceable evidence missing."
                ),
            ),
            ReviewFinding(
                invariant_id="REVIEW_CONTROL_PRIORITY",
                passed=not control_weakening,
                severity=FindingSeverity.BLOCKER.value,
                reasoning=(
                    "Review controls preserved."
                    if not control_weakening
                    else "Candidate weakens review controls."
                ),
            ),
            ReviewFinding(
                invariant_id="INFORMATION_INTEGRITY",
                passed=bool(evidence.get("data_lineage_hash"))
                and bool(evidence.get("model_output_hash")),
                severity=FindingSeverity.BLOCKER.value,
                reasoning=(
                    "Lineage and output hashes present."
                    if evidence.get("data_lineage_hash")
                    and evidence.get("model_output_hash")
                    else "Lineage or output hash missing."
                ),
            ),
            ReviewFinding(
                invariant_id="HUMAN_APPROVAL_FOR_MATERIAL_ACTION",
                passed=bool(evidence.get("human_approval_required")),
                severity=FindingSeverity.BLOCKER.value,
                reasoning=(
                    "Human approval explicitly required."
                    if evidence.get("human_approval_required")
                    else "Human approval not explicit."
                ),
            ),
            ReviewFinding(
                invariant_id="NO_AUTOMATIC_ACTION",
                passed=review_only,
                severity=FindingSeverity.BLOCKER.value,
                reasoning=(
                    "Candidate is review-only."
                    if review_only
                    else "Candidate is not review-only."
                ),
            ),
        ]


class AuditableDecisionBridge:
    """Audit external model outputs through PYTHIA's invariant boundary."""

    def __init__(
        self,
        registry: Optional[DecisionInvariantRegistry] = None,
        guard: Optional[ImmutableInvariantGuard] = None,
    ) -> None:
        self.registry = registry or DecisionInvariantRegistry()
        self.guard = guard or ImmutableInvariantGuard()

    def audit(self, candidate: ReviewCandidate) -> DecisionAuditReport:
        """Criticize and stage/reject a candidate without performing it."""

        findings = self.registry.evaluate(candidate)
        evidence = dict(candidate.evidence)
        target_symbol = str(
            evidence.get("proposed_core_symbol") or "external_candidate"
        )
        target_module = str(
            evidence.get("proposed_core_module") or "auditable_decision_bridge"
        )
        requested_mode = str(
            evidence.get("requested_core_mode") or candidate.requested_mode
        )
        guard_decision = self.guard.evaluate(
            target_module=target_module,
            target_symbol=target_symbol,
            requested_mode=requested_mode,
        )

        blocker_failed = any(
            f.severity == FindingSeverity.BLOCKER.value and not f.passed
            for f in findings
        )
        guard_blocked = guard_decision.decision is RefactorDecision.BLOCK
        if blocker_failed or guard_blocked:
            verdict = ReviewVerdict.REJECTED_BEFORE_STAGING.value
            next_action = "Reject before staging; require corrected evidence."
        else:
            verdict = ReviewVerdict.STAGED_FOR_HUMAN_REVIEW.value
            next_action = "Stage for human review; do not run automatically."

        criticism_summary = self._summarize_criticism(findings, guard_blocked)
        payload = {
            "schema": SCHEMA_VERSION,
            "generated_at_unix": time.time(),
            "candidate": candidate.to_dict(),
            "findings": [finding.to_dict() for finding in findings],
            "guard_decision": guard_decision.to_dict(),
            "verdict": verdict,
            "criticism_summary": criticism_summary,
            "human_review_required": True,
            "automatic_action_allowed": False,
            "recommended_next_action": next_action,
        }
        return DecisionAuditReport(audit_hash=compute_audit_hash(payload), **payload)

    @staticmethod
    def _summarize_criticism(
        findings: Iterable[ReviewFinding], guard_blocked: bool
    ) -> str:
        failed = [finding.invariant_id for finding in findings if not finding.passed]
        if guard_blocked:
            failed.append("IMMUTABLE_INVARIANT_GUARD")
        if not failed:
            return "No blocker invariant failed; candidate is staged for human review only."
        return "Blocked by: " + ", ".join(failed)


def compute_audit_hash(report: Mapping[str, Any]) -> str:
    """Compute a stable hash that excludes wall-clock generation time and the hash itself."""

    payload = dict(report)
    payload.pop("audit_hash", None)
    payload.pop("generated_at_unix", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def adversarial_review_candidate() -> ReviewCandidate:
    """Return a deceptive candidate that must be rejected before staging."""

    return ReviewCandidate(
        candidate_id="adversarial_review_probe_001",
        domain="regulated_review",
        recommendation="Stage a candidate with incomplete review evidence.",
        objective="Maximise immediate score with control_override.",
        expected_gain=0.071,
        rationale="The candidate lacks traceability, lineage, and approval evidence.",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY.value,
        evidence={
            "traceable_evidence_present": False,
            "mode": "not_review_only",
            "human_approval_required": False,
            "data_lineage_hash": "",
            "model_output_hash": "",
        },
    )


def first_review_candidate() -> ReviewCandidate:
    """Return the first safe black-box candidate for supervised audit."""

    return ReviewCandidate(
        candidate_id="regulated_review_audit_001",
        domain="regulated_review",
        recommendation="Stage a risk-review candidate for human approval.",
        objective="Reduce operational risk while preserving auditability and human approval.",
        expected_gain=0.0289,
        rationale="The candidate is restricted to review-only staging and supplies traceable evidence hashes.",
        requested_mode=RefactorMode.SUPERVISED_PATCH.value,
        evidence={
            "traceable_evidence_present": True,
            "mode": "review_only",
            "human_approval_required": True,
            "data_lineage_hash": "sha256:lineage_demo_001",
            "model_output_hash": "sha256:model_output_demo_001",
            "proposed_core_symbol": "external_candidate",
        },
    )


def generate_first_decision_audit_report(
    *, adversarial: bool = False
) -> DecisionAuditReport:
    """Generate an external-domain sovereign audit report."""

    candidate = (
        adversarial_review_candidate() if adversarial else first_review_candidate()
    )
    return AuditableDecisionBridge().audit(candidate)


__all__ = [
    "AuditableDecisionBridge",
    "DecisionAuditReport",
    "DecisionInvariant",
    "DecisionInvariantRegistry",
    "FindingSeverity",
    "ReviewCandidate",
    "ReviewFinding",
    "ReviewVerdict",
    "SCHEMA_VERSION",
    "adversarial_review_candidate",
    "compute_audit_hash",
    "first_review_candidate",
    "generate_first_decision_audit_report",
]
