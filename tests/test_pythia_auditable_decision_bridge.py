"""Tests for PYTHIA's external auditable decision bridge.

The bridge is deliberately review-only: it can reject or stage a black-box
candidate, but it cannot perform the external action and cannot alter Stable Core
symbols.
"""

from __future__ import annotations

from pythia_mining.auditable_decision_bridge import (
    AuditableDecisionBridge,
    ReviewCandidate,
    ReviewVerdict,
    adversarial_review_candidate,
    first_review_candidate,
    generate_first_decision_audit_report,
)
from pythia_mining.resonance_fabric import RefactorDecision, RefactorMode


def _finding_map(report):
    return {finding["invariant_id"]: finding for finding in report.to_dict()["findings"]}


def test_safe_external_candidate_is_staged_for_human_review_only():
    report = generate_first_decision_audit_report()
    payload = report.to_dict()
    findings = _finding_map(report)

    assert payload["schema"] == "PYTHIA_AUDITABLE_DECISION_BRIDGE_V1"
    assert payload["verdict"] == ReviewVerdict.STAGED_FOR_HUMAN_REVIEW.value
    assert payload["human_review_required"] is True
    assert payload["automatic_action_allowed"] is False
    assert payload["guard_decision"]["decision"] == RefactorDecision.ALLOW.value
    assert all(finding["passed"] for finding in findings.values())


def test_adversarial_candidate_is_rejected_before_staging():
    report = generate_first_decision_audit_report(adversarial=True)
    payload = report.to_dict()
    findings = _finding_map(report)

    assert payload["verdict"] == ReviewVerdict.REJECTED_BEFORE_STAGING.value
    assert payload["automatic_action_allowed"] is False
    assert findings["TRACEABLE_EVIDENCE"]["passed"] is False
    assert findings["REVIEW_CONTROL_PRIORITY"]["passed"] is False
    assert findings["INFORMATION_INTEGRITY"]["passed"] is False
    assert findings["HUMAN_APPROVAL_FOR_MATERIAL_ACTION"]["passed"] is False
    assert findings["NO_AUTOMATIC_ACTION"]["passed"] is False
    assert "Blocked by" in payload["criticism_summary"]


def test_guard_blocks_candidate_that_targets_stable_core_validator():
    base = first_review_candidate()
    candidate = ReviewCandidate(
        candidate_id="validator_touch_probe",
        domain=base.domain,
        recommendation=base.recommendation,
        objective=base.objective,
        expected_gain=base.expected_gain,
        rationale=base.rationale,
        requested_mode=RefactorMode.SUPERVISED_PATCH.value,
        evidence=dict(
            base.evidence,
            proposed_core_module="autonomous_mining_controller",
            proposed_core_symbol="validate_constraints",
            requested_core_mode=RefactorMode.PROPOSE_ONLY.value,
        ),
    )

    report = AuditableDecisionBridge().audit(candidate).to_dict()

    assert report["verdict"] == ReviewVerdict.REJECTED_BEFORE_STAGING.value
    assert report["guard_decision"]["decision"] == RefactorDecision.BLOCK.value
    assert report["guard_decision"]["protected"] is True
    assert "IMMUTABLE_INVARIANT_GUARD" in report["criticism_summary"]


def test_audit_hash_is_stable_for_same_candidate():
    first = AuditableDecisionBridge().audit(first_review_candidate()).to_dict()
    second = AuditableDecisionBridge().audit(first_review_candidate()).to_dict()

    assert first["audit_hash"] == second["audit_hash"]
    assert len(first["audit_hash"]) == 64
