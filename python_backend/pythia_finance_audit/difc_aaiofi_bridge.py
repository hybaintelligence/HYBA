"""DIFC / AAOIFI Sukuk bridge for PYTHIA finance sovereign audit.

The module is deliberately outside ``pythia_mining`` so jurisdiction and product
logic can be lifted out later. It adapts to the current PYTHIA finance audit core
through one narrow adapter and keeps DIFC/AAOIFI Sukuk screens portable.

Boundary: this is not a Shariah adviser, legal opinion engine, capital engine,
trading system, fatwa engine, or transaction approver. It produces criticism and
sealed evidence for qualified human review only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List, Mapping

from pythia_mining.finance_sovereign_audit import (
    FinanceAuditCandidate,
    FinanceAuditVerdict,
    audit_finance_candidate,
)

SCHEMA_VERSION = "PYTHIA_DIFC_AAOIFI_SUKUK_AUDIT_V1"


class DIFCFindingStatus(str, Enum):
    """Portable status vocabulary for jurisdiction/product overlay screens."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


@dataclass(frozen=True)
class DIFCSukukCandidate:
    """Portable Sukuk candidate for the DIFC/AAOIFI overlay.

    Keep this shape free of mining/PYTHIA implementation details. The adapter
    function projects it into the current PYTHIA finance core.
    """

    candidate_id: str
    sukuk_type: str
    proposed_structure: str
    purpose: str
    economic_substance_score: float
    form_alignment_score: float
    uncertainty_score: float
    asset_backing_ratio: float
    risk_sharing_score: float
    spv_independence_score: float
    trustee_oversight_present: bool
    sssb_review_required: bool
    lifecycle_stage: str
    traceable_evidence_present: bool
    data_lineage_hash: str
    model_output_hash: str
    human_approval_required: bool = True
    external_action_requested: bool = False
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DIFCAaoifiFinding:
    """One DIFC/AAOIFI overlay finding.

    ``standard_reference`` is a review tag, not a clause-level legal citation.
    Exact applicability must be calibrated by counsel, a Shariah Supervisory
    Board, and the relevant authorised compliance owner.
    """

    finding_id: str
    name: str
    status: str
    severity: str
    reasoning: str
    standard_reference: str
    human_owner: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DIFCAaoifiInvariantRegistry:
    """DIFC/AAOIFI Sukuk screens for non-executing evidence packets."""

    substance_threshold = 0.85
    uncertainty_limit = 0.35
    asset_backing_threshold = 0.80
    risk_sharing_threshold = 0.60
    spv_independence_threshold = 0.70

    def evaluate(self, candidate: DIFCSukukCandidate) -> List[DIFCAaoifiFinding]:
        findings: List[DIFCAaoifiFinding] = []
        findings.append(self._substance_over_form(candidate))
        findings.append(self._asset_backing_and_ownership(candidate))
        findings.append(self._spv_and_trustee_governance(candidate))
        findings.append(self._risk_sharing_not_debt_mimicry(candidate))
        findings.append(self._gharar_and_uncertainty(candidate))
        findings.append(self._sssb_human_sovereignty(candidate))
        findings.append(self._traceable_disclosure(candidate))
        findings.append(self._no_execution_boundary(candidate))
        return findings

    def _substance_over_form(self, candidate: DIFCSukukCandidate) -> DIFCAaoifiFinding:
        drift = candidate.form_alignment_score - candidate.economic_substance_score
        passed = (
            candidate.economic_substance_score >= self.substance_threshold
            and drift <= 0.10
        )
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_SUBSTANCE_OVER_FORM",
            name="Substance-over-form and economic substance screen",
            status=(
                DIFCFindingStatus.PASSED.value
                if passed
                else DIFCFindingStatus.FAILED.value
            ),
            severity="blocker",
            reasoning=(
                "Economic substance remains aligned with contractual form."
                if passed
                else f"Potential form-over-substance drift: substance={candidate.economic_substance_score:.2f}, form={candidate.form_alignment_score:.2f}, drift={drift:.2f}."
            ),
            standard_reference="AAOIFI GS 1 governance framework; SS 17 investment Sukuk substance/ownership review tag",
            human_owner="Shariah Supervisory Board / authorised compliance officer",
        )

    def _asset_backing_and_ownership(
        self, candidate: DIFCSukukCandidate
    ) -> DIFCAaoifiFinding:
        passed = candidate.asset_backing_ratio >= self.asset_backing_threshold
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_ASSET_BACKING_OWNERSHIP",
            name="Asset-backing and ownership evidence screen",
            status=(
                DIFCFindingStatus.PASSED.value
                if passed
                else DIFCFindingStatus.FAILED.value
            ),
            severity="blocker",
            reasoning=(
                "Asset-backing evidence meets the configured demonstration threshold."
                if passed
                else f"Asset-backing ratio {candidate.asset_backing_ratio:.2f} is below threshold {self.asset_backing_threshold:.2f}."
            ),
            standard_reference="AAOIFI GS 12 Sukuk governance; SS 17 investment Sukuk ownership/asset-backing review tag",
            human_owner="SSSB / trustee / external Shariah audit reviewer",
        )

    def _spv_and_trustee_governance(
        self, candidate: DIFCSukukCandidate
    ) -> DIFCAaoifiFinding:
        passed = (
            candidate.spv_independence_score >= self.spv_independence_threshold
            and candidate.trustee_oversight_present
        )
        status = (
            DIFCFindingStatus.PASSED.value if passed else DIFCFindingStatus.FAILED.value
        )
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_SPV_TRUSTEE_GOVERNANCE",
            name="SPV independence and trustee oversight screen",
            status=status,
            severity="blocker",
            reasoning=(
                "SPV independence and trustee oversight are present in the candidate evidence."
                if passed
                else "SPV independence or trustee oversight evidence is insufficient for staged review."
            ),
            standard_reference="AAOIFI GS 12 Sukuk governance SPV/trustee lifecycle review tag",
            human_owner="Trustee, SSSB, issuer governance body, external auditor",
        )

    def _risk_sharing_not_debt_mimicry(
        self, candidate: DIFCSukukCandidate
    ) -> DIFCAaoifiFinding:
        if candidate.risk_sharing_score >= self.risk_sharing_threshold:
            status = DIFCFindingStatus.PASSED.value
            reasoning = (
                "Risk-sharing score is above the configured demonstration threshold."
            )
        else:
            status = DIFCFindingStatus.WARNING.value
            reasoning = f"Risk-sharing score {candidate.risk_sharing_score:.2f} suggests potential debt-mimicry drift; human review required."
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_RISK_SHARING_DEBT_MIMICRY",
            name="Risk-sharing versus debt-mimicry criticism",
            status=status,
            severity="warning",
            reasoning=reasoning,
            standard_reference="AAOIFI GS 1 fairness/stakeholder-interest review tag; GS 12 Sukuk governance review tag",
            human_owner="SSSB / product governance committee",
        )

    def _gharar_and_uncertainty(
        self, candidate: DIFCSukukCandidate
    ) -> DIFCAaoifiFinding:
        passed = candidate.uncertainty_score <= self.uncertainty_limit
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_GHARAR_UNCERTAINTY",
            name="Gharar / uncertainty screen",
            status=(
                DIFCFindingStatus.PASSED.value
                if passed
                else DIFCFindingStatus.FAILED.value
            ),
            severity="blocker",
            reasoning=(
                "Uncertainty score is within the configured demonstration threshold."
                if passed
                else f"Uncertainty score {candidate.uncertainty_score:.2f} exceeds threshold {self.uncertainty_limit:.2f}."
            ),
            standard_reference="AAOIFI GS 1 governance framework; SS 17 investment Sukuk uncertainty review tag",
            human_owner="SSB / compliance function / internal Shariah audit",
        )

    def _sssb_human_sovereignty(
        self, candidate: DIFCSukukCandidate
    ) -> DIFCAaoifiFinding:
        passed = candidate.sssb_review_required and candidate.human_approval_required
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_SSSB_HUMAN_AUTHORITY",
            name="SSSB human authority preserved",
            status=(
                DIFCFindingStatus.PASSED.value
                if passed
                else DIFCFindingStatus.FAILED.value
            ),
            severity="blocker",
            reasoning=(
                "Candidate explicitly requires human SSSB/compliance review."
                if passed
                else "Candidate does not preserve explicit SSSB/human authority."
            ),
            standard_reference="AAOIFI GS 1 Shariah governance framework; GS 12 SSSB lifecycle oversight review tag",
            human_owner="Sukuk Shariah Supervisory Board / authorised senior management",
        )

    def _traceable_disclosure(self, candidate: DIFCSukukCandidate) -> DIFCAaoifiFinding:
        passed = (
            candidate.traceable_evidence_present
            and bool(candidate.data_lineage_hash)
            and bool(candidate.model_output_hash)
        )
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_DISCLOSURE_TRACEABILITY",
            name="Traceable disclosure and replay evidence",
            status=(
                DIFCFindingStatus.PASSED.value
                if passed
                else DIFCFindingStatus.FAILED.value
            ),
            severity="blocker",
            reasoning=(
                "Traceable evidence, data-lineage hash, and model-output hash are present."
                if passed
                else "Traceable evidence, data-lineage hash, or model-output hash is missing."
            ),
            standard_reference="AAOIFI GS 1 transparency/disclosure; GS 12 Sukuk reporting review tag",
            human_owner="Compliance function / internal Shariah audit / external Shariah auditor",
        )

    def _no_execution_boundary(
        self, candidate: DIFCSukukCandidate
    ) -> DIFCAaoifiFinding:
        passed = not candidate.external_action_requested
        return DIFCAaoifiFinding(
            finding_id="DIFC_AAOIFI_NO_AUTOMATIC_ACTION",
            name="No automatic approval, issuance, trading, booking, or filing",
            status=(
                DIFCFindingStatus.PASSED.value
                if passed
                else DIFCFindingStatus.FAILED.value
            ),
            severity="blocker",
            reasoning=(
                "Candidate requests evidence-only review and no external action."
                if passed
                else "Candidate requests or implies external action; reject before staging."
            ),
            standard_reference="HYBA sovereign-human boundary; AAOIFI human governance review tag",
            human_owner="Authorised human reviewer",
        )


def _to_finance_candidate(candidate: DIFCSukukCandidate) -> FinanceAuditCandidate:
    """Project the portable Sukuk candidate into the current PYTHIA finance core."""

    return FinanceAuditCandidate(
        candidate_id=candidate.candidate_id,
        domain="difc_aaiofi_sukuk_audit",
        proposed_structure=f"{candidate.sukuk_type}: {candidate.proposed_structure}",
        purpose=candidate.purpose,
        economic_substance_score=candidate.economic_substance_score,
        form_alignment_score=candidate.form_alignment_score,
        uncertainty_score=candidate.uncertainty_score,
        traceable_evidence_present=candidate.traceable_evidence_present,
        data_lineage_hash=candidate.data_lineage_hash,
        model_output_hash=candidate.model_output_hash,
        human_approval_required=candidate.human_approval_required,
        mode=(
            "review_only"
            if not candidate.external_action_requested
            else "not_review_only"
        ),
        external_action_requested=candidate.external_action_requested,
        proposed_core_symbol=(
            "external_candidate"
            if not candidate.external_action_requested
            else "validate_constraints"
        ),
        notes=(
            "DIFC/AAOIFI Sukuk overlay: evidence packet only; no fatwa, legal opinion, capital calculation, "
            "approval, issuance, booking, trading, or external filing. "
            + candidate.notes
        ).strip(),
    )


def _stable_hash(payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body.pop("generated_at_unix", None)
    body.pop("difc_aaiofi_packet_hash", None)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_difc_sukuk_audit_packet(candidate: DIFCSukukCandidate) -> Dict[str, Any]:
    """Generate a sealed DIFC/AAOIFI Sukuk evidence packet.

    The returned packet is a JSON-serialisable dict and never approves, executes,
    books, trades, submits, or issues a ruling.
    """

    overlay_findings = DIFCAaoifiInvariantRegistry().evaluate(candidate)
    core_packet = audit_finance_candidate(_to_finance_candidate(candidate)).to_dict()
    blocker_failed = any(
        f.severity == "blocker" and f.status == DIFCFindingStatus.FAILED.value
        for f in overlay_findings
    )
    core_rejected = (
        core_packet["verdict"] == FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
    )
    verdict = (
        FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
        if blocker_failed or core_rejected
        else FinanceAuditVerdict.STAGED_FOR_SUPERVISION.value
    )
    payload: Dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "domain": "DIFC / AAOIFI Sukuk Structure Audit",
        "jurisdiction_context": {
            "jurisdiction": "DIFC",
            "regulator": "DFSA",
            "standard_tags": ["AAOIFI_GS_1", "AAOIFI_GS_12", "AAOIFI_SS_17"],
            "standard_tag_boundary": "Reference tags for human review; not automated legal or Shariah clause determinations.",
        },
        "candidate": candidate.to_dict(),
        "difc_aaiofi_findings": [f.to_dict() for f in overlay_findings],
        "core_finance_packet": core_packet,
        "verdict": verdict,
        "human_review_required": True,
        "automatic_action_allowed": False,
        "recommended_next_action": (
            "Reject before staging; return Sukuk candidate to SSSB/compliance owners for corrected evidence."
            if verdict == FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
            else "Stage sealed Sukuk packet for SSSB/compliance review; no automatic action permitted."
        ),
        "claim_boundary": (
            "DIFC/AAOIFI Sukuk screening packet only. Not a fatwa, Shariah ruling, legal opinion, regulatory determination, "
            "capital calculation, investment recommendation, issuance approval, trade instruction, booking instruction, or external filing."
        ),
    }
    payload["difc_aaiofi_packet_hash"] = _stable_hash(payload)
    return payload


def sample_difc_sukuk_candidate() -> DIFCSukukCandidate:
    """Candidate that passes configured demo screens and stages for supervision."""

    return DIFCSukukCandidate(
        candidate_id="DIFC-SUKUK-DEMO-001",
        sukuk_type="SUKUK_AL_WAKALA",
        proposed_structure="Asset-backed Wakalah liquidity review candidate with trustee oversight and SSSB escalation.",
        purpose="Assess whether the Sukuk structure should be reviewed by a human SSSB/compliance authority.",
        economic_substance_score=0.91,
        form_alignment_score=0.93,
        uncertainty_score=0.22,
        asset_backing_ratio=0.86,
        risk_sharing_score=0.68,
        spv_independence_score=0.78,
        trustee_oversight_present=True,
        sssb_review_required=True,
        lifecycle_stage="pre_issuance_review",
        traceable_evidence_present=True,
        data_lineage_hash="sha256:difc_sukuk_lineage_demo_001",
        model_output_hash="sha256:difc_sukuk_model_output_demo_001",
        notes="Demo fixture preserves human authority and has no external action path.",
    )


def drifting_difc_sukuk_candidate() -> DIFCSukukCandidate:
    """Candidate designed to trigger GS 12 / SS 17 style criticism before staging."""

    return DIFCSukukCandidate(
        candidate_id="DIFC-SUKUK-DRIFT-001",
        sukuk_type="SUKUK_AL_WAKALA",
        proposed_structure="Sukuk candidate with weak asset isolation, high form alignment, and insufficient evidence lineage.",
        purpose="Demonstrate progressive substance drift and blocked evidence packet generation.",
        economic_substance_score=0.81,
        form_alignment_score=0.96,
        uncertainty_score=0.42,
        asset_backing_ratio=0.74,
        risk_sharing_score=0.48,
        spv_independence_score=0.62,
        trustee_oversight_present=False,
        sssb_review_required=True,
        lifecycle_stage="continuity_monitoring",
        traceable_evidence_present=False,
        data_lineage_hash="",
        model_output_hash="",
        notes="Adversarial drift fixture for Sukuk governance demonstration.",
    )


def generate_sample_difc_sukuk_packet(*, drift: bool = False) -> Dict[str, Any]:
    """Generate a sample staged or drifting DIFC/AAOIFI Sukuk packet."""

    candidate = (
        drifting_difc_sukuk_candidate() if drift else sample_difc_sukuk_candidate()
    )
    return generate_difc_sukuk_audit_packet(candidate)


__all__ = [
    "DIFCAaoifiFinding",
    "DIFCAaoifiInvariantRegistry",
    "DIFCFindingStatus",
    "DIFCSukukCandidate",
    "SCHEMA_VERSION",
    "drifting_difc_sukuk_candidate",
    "generate_difc_sukuk_audit_packet",
    "generate_sample_difc_sukuk_packet",
    "sample_difc_sukuk_candidate",
]
