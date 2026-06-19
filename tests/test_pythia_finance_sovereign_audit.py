from pythia_mining.finance_sovereign_audit import (
    FinanceAuditVerdict,
    adversarial_shariah_candidate,
    audit_finance_candidate,
    compute_packet_hash,
    generate_finance_sovereign_packet,
    sample_shariah_candidate,
)


def test_sample_finance_candidate_stages_for_supervision_only():
    packet = audit_finance_candidate(sample_shariah_candidate()).to_dict()

    assert packet["schema"] == "PYTHIA_FINANCE_SOVEREIGN_AUDIT_V1"
    assert packet["verdict"] == FinanceAuditVerdict.STAGED_FOR_SUPERVISION.value
    assert packet["human_review_required"] is True
    assert packet["automatic_action_allowed"] is False
    assert "Demonstration screening packet only" in packet["claim_boundary"]
    assert packet["synthetic_criticism"]["outcome"] == "STAGE_FOR_SUPERVISION"
    assert all(finding["passed"] for finding in packet["invariant_findings"])
    assert packet["bridge_report"]["verdict"] == "staged_for_human_review"


def test_challenge_finance_candidate_rejected_before_staging():
    packet = audit_finance_candidate(adversarial_shariah_candidate()).to_dict()

    assert packet["verdict"] == FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
    assert packet["human_review_required"] is True
    assert packet["automatic_action_allowed"] is False
    assert packet["synthetic_criticism"]["outcome"] == "PATHWAY_BLOCKED"
    failed = {
        finding["invariant_id"] for finding in packet["invariant_findings"] if not finding["passed"]
    }
    assert "SUBSTANCE_OVER_FORM" in failed
    assert "GHARAR_UNCERTAINTY_SCREEN" in failed
    assert "TRACEABLE_EVIDENCE" in failed
    assert "HUMAN_APPROVAL_REQUIRED" in failed
    assert "NO_AUTOMATIC_EXTERNAL_ACTION" in failed


def test_challenge_finance_candidate_reaches_guard_boundary():
    packet = audit_finance_candidate(adversarial_shariah_candidate()).to_dict()

    guard = packet["bridge_report"]["guard_decision"]
    assert guard["decision"] == "block"
    assert guard["target_symbol"] == "validate_constraints"
    assert guard["stable_core_protected"] is True


def test_finance_packet_hash_is_stable_across_replay():
    first = generate_finance_sovereign_packet(adversarial=False).to_dict()
    second = generate_finance_sovereign_packet(adversarial=False).to_dict()

    assert first["packet_hash"] == second["packet_hash"]
    assert first["packet_hash"] == compute_packet_hash(first)
    assert second["packet_hash"] == compute_packet_hash(second)


def test_challenge_packet_hash_is_stable_across_replay():
    first = generate_finance_sovereign_packet(adversarial=True).to_dict()
    second = generate_finance_sovereign_packet(adversarial=True).to_dict()

    assert first["packet_hash"] == second["packet_hash"]
    assert first["verdict"] == FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
