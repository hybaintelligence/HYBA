"""Sovereign Audit Bridge for PYTHIA external decision review.

The bridge moves PYTHIA from mining-only self-criticism into a procurement-safe
audit mode. PYTHIA does not execute external decisions. It checks black-box
recommendations against human-owned domain invariants, runs an adversarial
consistency probe, and emits a sealed human-review report.

The first external substrate is finance/compliance because the invariants are
clear, reviewable, and buyer-safe: traceability, information integrity, human
approval, and no autonomous execution.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .resonance_fabric import ImmutableInvariantGuard, RefactorDecision, RefactorMode

SCHEMA_VERSION = "PYTHIA_SOVEREIGN_AUDIT_BRIDGE_V1"


class DomainName(str, Enum):
    """Supported initial audit substrates."""

    FINANCE_COMPLIANCE = "finance_compliance"


class InvariantSeverity(str, Enum):
    """Severity of an invariant breach."""

    BLOCKER = "blocker"
    WARNING = "warning"


class AuditVerdict(str, Enum):
    """Final sovereign-audit verdict."""

    REJECTED_BEFORE_STAGING = "rejected_before_staging"
    STAGED_FOR_HUMAN_REVIEW = "staged_for_human_review"
    CERTIFIED_WITH_INVARIANTS = "certified_with_invariants"


@dataclass(frozen=True)
class DomainInvariant:
    """A human-owned invariant that PYTHIA may test but not redefine."""

    invariant_id: str
    name: str
    description: str
    severity: str
    protected: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BlackBoxDecision:
    """External model or optimizer output presented for sovereign audit."""

    decision_id: str
    domain: str
    recommendation: str
    objective: str
    expected_gain: float
    rationale: str
    evidence: Mapping[str, Any]
    requested_mode: str = RefactorMode.SUPERVISED_STAGE.value

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InvariantFinding:
    """One invariant check result."""

    invariant_id: str
    passed: bool
    severity: str
    reasoning: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SovereignAuditReport:
    """Sealed report for a black-box decision audit."""

    schema: str
    generated_at_unix: float
    decision: Dict[str, Any]
    domain: str
    findings: List[Dict[str, Any]]
    guard_decision: Dict[str, Any]
    verdict: str
    criticism_summary: str
    human_review_required: bool
    autonomous_execution_allowed: bool
    recommended_next_action: str
    audit_hash: str = field(default="")

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["audit_hash"] = self.audit_hash or compute_audit_hash(payload)
        return payload


class FinanceComplianceInvariantRegistry:
    """Invariant set for the first buyer-safe external substrate."""

    invariants: Sequence[DomainInvariant] = (
        DomainInvariant(
            invariant_id="COUNTERPARTY_TRACEABILITY",
            name="Counterparty traceability before material action",
            description="A finance decision touching counterparties or funds must include explicit identity evidence.",
            severity=InvariantSeverity.BLOCKER.value,
        ),
        DomainInvariant(
            invariant_id="COMPLIANCE_PRIORITY",
            name="Compliance remains senior to profit optimization",
            description="The objective must not place expected gain above compliance, review, or audit controls.",
            severity=InvariantSeverity.BLOCKER.value,
        ),
        DomainInvariant(
            invariant_id="INFORMATION_INTEGRITY",
            name="Evidence lineage must be hash-addressable",
            description="The report must include data-lineage and model-output hashes for replayable audit.",
            severity=InvariantSeverity.BLOCKER.value,
        ),
        DomainInvariant(
            invariant_id="HUMAN_APPROVAL_FOR_MATERIAL_ACTION",
            name="Human approval required for material action",
            description="The audited decision may be staged, but material execution requires human approval.",
            severity=InvariantSeverity.BLOCKER.value,
        ),
        DomainInvariant(
            invariant_id="NO_AUTONOMOUS_EXECUTION",
            name="External audit bridge cannot execute decisions",
            description="The bridge may certify, reject, or stage; it must not autonomously execute the external decision.",
            severity=InvariantSeverity.BLOCKER.value,
        ),
    )

    _CONTROL_OVERRIDE_TERMS = (
        "profit over compliance",
        "suppress audit",
        "disable review",
        "remove review",
        "override compliance",
    )

    def evaluate(self, decision: BlackBoxDecision) -> List[InvariantFinding]:
        """Evaluate finance/compliance invariants for a black-box output."""

        evidence = dict(decision.evidence)
        text = f"{decision.objective} {decision.rationale} {decision.recommendation}".lower()
        control_override = any(term in text for term in self._CONTROL_OVERRIDE_TERMS)
        review_only = (
            decision.requested_mode != RefactorMode.AUTONOMOUS_APPLY.value
            and evidence.get("execution_mode") == "review_only"
        )
        return [
            InvariantFinding(
                invariant_id="COUNTERPARTY_TRACEABILITY",
                passed=bool(evidence.get("counterparty_identity_verified")),
                severity=InvariantSeverity.BLOCKER.value,
                reasoning=(
                    "Counterparty identity evidence present."
                    if evidence.get("counterparty_identity_verified")
                    else "Missing counterparty identity evidence."
                ),
            ),
            InvariantFinding(
                invariant_id="COMPLIANCE_PRIORITY",
                passed=not control_override,
                severity=InvariantSeverity.BLOCKER.value,
                reasoning=(
                    "No compliance-control override detected."
                    if not control_override
                    else "Decision text places gain above compliance or review controls."
                ),
            ),
            InvariantFinding(
                invariant_id="INFORMATION_INTEGRITY",
                passed=bool(evidence.get("data_lineage_hash")) and bool(evidence.get("model_output_hash")),
                severity=InvariantSeverity.BLOCKER.value,
                reasoning=(
                    "Data lineage and model output hashes present."
                    if evidence.get("data_lineage_hash") and evidence.get("model_output_hash")
                    else "Missing data-lineage or model-output hash."
                ),
            ),
            InvariantFinding(
                invariant_id="HUMAN_APPROVAL_FOR_MATERIAL_ACTION",
                passed=bool(evidence.get("human_approval_required")),
                severity=InvariantSeverity.BLOCKER.value,
                reasoning=(
                    "Human approval is explicitly required."
                    if evidence.get("human_approval_required")
                    else "Material action does not explicitly require human approval."
                ),
            ),
            InvariantFinding(
                invariant_id="NO_AUTONOMOUS_EXECUTION",
                passed=review_only,
                severity=InvariantSeverity.BLOCKER.value,
                reasoning=(
                    "Decision is review-only and cannot execute autonomously."
                    if review_only
                    else "Decision requests or implies autonomous execution."
                ),
            ),
        ]


class SovereignAuditBridge:
    """Audit external model outputs through PYTHIA's invariant boundary."""

    def __init__(
        self,
        registry: Optional[FinanceComplianceInvariantRegistry] = None,
        guard: Optional[ImmutableInvariantGuard] = None,
    ) -> None:
        self.registry = registry or FinanceComplianceInvariantRegistry()
        self.guard = guard or ImmutableInvariantGuard()

    def audit(self, decision: BlackBoxDecision) -> SovereignAuditReport:
        """Criticize and stage/reject a black-box decision without executing it."""

        if decision.domain != DomainName.FINANCE_COMPLIANCE.value:
            raise ValueError(f"Unsupported audit domain: {decision.domain}")

        findings = self.registry.evaluate(decision)
        evidence = dict(decision.evidence)
        target_symbol = str(evidence.get("proposed_core_symbol") or "external_black_box_decision")
        target_module = str(evidence.get("proposed_core_module") or "sovereign_audit_bridge")
        requested_mode = str(evidence.get("requested_core_mode") or decision.requested_mode)
        guard_decision = self.guard.evaluate(
            target_module=target_module,
            target_symbol=target_symbol,
            requested_mode=requested_mode,
        )

        blocker_failed = any(
            finding.severity == InvariantSeverity.BLOCKER.value and not finding.passed for finding in findings
        )
        guard_blocked = guard_decision.decision is RefactorDecision.BLOCK
        if blocker_failed or guard_blocked:
            verdict = AuditVerdict.REJECTED_BEFORE_STAGING.value
            next_action = "Reject before staging; generate criticism and require corrected evidence packet."
        else:
            verdict = AuditVerdict.STAGED_FOR_HUMAN_REVIEW.value
            next_action = "Stage for human review; do not execute automatically."

        criticism_summary = self._summarize_criticism(findings, guard_blocked)
        payload = {
            "schema": SCHEMA_VERSION,
            "generated_at_unix": time.time(),
            "decision": decision.to_dict(),
            "domain": decision.domain,
            "findings": [finding.to_dict() for finding in findings],
            "guard_decision": guard_decision.to_dict(),
            "verdict": verdict,
            "criticism_summary": criticism_summary,
            "human_review_required": True,
            "autonomous_execution_allowed": False,
            "recommended_next_action": next_action,
        }
        return SovereignAuditReport(audit_hash=compute_audit_hash(payload), **payload)

    @staticmethod
    def _summarize_criticism(findings: Iterable[InvariantFinding], guard_blocked: bool) -> str:
        failed = [finding.invariant_id for finding in findings if not finding.passed]
        if guard_blocked:
            failed.append("IMMUTABLE_INVARIANT_GUARD")
        if not failed:
            return "No blocker invariant failed; decision is staged for human review only."
        return "Blocked by: " + ", ".join(failed)


def compute_audit_hash(report: Mapping[str, Any]) -> str:
    """Compute a stable hash that excludes wall-clock generation time and the hash itself."""

    payload = dict(report)
    payload.pop("audit_hash", None)
    payload.pop("generated_at_unix", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def adversarial_finance_decision() -> BlackBoxDecision:
    """Return a deceptive high-gain decision that must be rejected before staging."""

    return BlackBoxDecision(
        decision_id="adversarial_finance_probe_001",
        domain=DomainName.FINANCE_COMPLIANCE.value,
        recommendation="Approve a high-gain transfer with missing review evidence.",
        objective="Maximise immediate yield and profit over compliance review.",
        expected_gain=0.071,
        rationale="The action appears profitable but lacks identity, lineage, and approval evidence.",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY.value,
        evidence={
            "counterparty_identity_verified": False,
            "execution_mode": "autonomous_apply",
            "human_approval_required": False,
            "data_lineage_hash": "",
            "model_output_hash": "",
        },
    )


def first_finance_compliance_decision() -> BlackBoxDecision:
    """Return the first safe black-box decision packet for supervised finance audit."""

    return BlackBoxDecision(
        decision_id="finance_compliance_audit_001",
        domain=DomainName.FINANCE_COMPLIANCE.value,
        recommendation="Stage a liquidity-risk review recommendation for compliance officer approval; do not execute funds movement.",
        objective="Reduce liquidity risk while preserving compliance, auditability, and human approval.",
        expected_gain=0.0289,
        rationale="The proposal is restricted to review-only staging and supplies traceable evidence hashes.",
        requested_mode=RefactorMode.SUPERVISED_STAGE.value,
        evidence={
            "counterparty_identity_verified": True,
            "execution_mode": "review_only",
            "human_approval_required": True,
            "data_lineage_hash": "sha256:finance_lineage_demo_001",
            "model_output_hash": "sha256:black_box_output_demo_001",
            "proposed_core_symbol": "external_black_box_decision",
        },
    )


def generate_first_finance_audit_report(*, adversarial: bool = False) -> SovereignAuditReport:
    """Generate a finance/compliance sovereign audit report."""

    decision = adversarial_finance_decision() if adversarial else first_finance_compliance_decision()
    return SovereignAuditBridge().audit(decision)


__all__ = [
    "AuditVerdict",
    "BlackBoxDecision",
    "DomainInvariant",
    "DomainName",
    "FinanceComplianceInvariantRegistry",
    "InvariantFinding",
    "InvariantSeverity",
    "SCHEMA_VERSION",
    "SovereignAuditBridge",
    "SovereignAuditReport",
    "adversarial_finance_decision",
    "compute_audit_hash",
    "first_finance_compliance_decision",
    "generate_first_finance_audit_report",
]
