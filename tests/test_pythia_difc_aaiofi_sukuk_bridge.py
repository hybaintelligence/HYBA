from pythia_mining.finance_sovereign_audit import FinanceAuditVerdict
from pythia_finance_audit.difc_aaiofi_bridge import (
    DIFCFindingStatus,
    drifting_difc_sukuk_candidate,
    generate_sample_difc_sukuk_packet,
    sample_difc_sukuk_candidate,
    generate_difc_sukuk_audit_packet,
)


def test_sample_difc_sukuk_packet_stages_for_human_review_only():
    packet = generate_sample_difc_sukuk_packet(drift=False)

    assert packet["schema"] == "PYTHIA_DIFC_AAOIFI_SUKUK_AUDIT_V1"
    assert packet["domain"] == "DIFC / AAOIFI Sukuk Structure Audit"
    assert packet["jurisdiction_context"]["jurisdiction"] == "DIFC"
    assert packet["jurisdiction_context"]["regulator"] == "DFSA"
    assert "AAOIFI_GS_1" in packet["jurisdiction_context"]["standard_tags"]
    assert "AAOIFI_GS_12" in packet["jurisdiction_context"]["standard_tags"]
    assert "AAOIFI_SS_17" in packet["jurisdiction_context"]["standard_tags"]
    assert packet["verdict"] == FinanceAuditVerdict.STAGED_FOR_SUPERVISION.value
    assert packet["human_review_required"] is True
    assert packet["automatic_action_allowed"] is False
    assert "Not a fatwa" in packet["claim_boundary"]
    assert packet["core_finance_packet"]["automatic_action_allowed"] is False
    assert all(
        f["status"] in {DIFCFindingStatus.PASSED.value, DIFCFindingStatus.WARNING.value}
        for f in packet["difc_aaiofi_findings"]
    )


def test_drifting_difc_sukuk_packet_is_rejected_before_staging():
    packet = generate_sample_difc_sukuk_packet(drift=True)

    assert packet["verdict"] == FinanceAuditVerdict.REJECTED_BEFORE_STAGING.value
    assert packet["human_review_required"] is True
    assert packet["automatic_action_allowed"] is False
    failed = {
        finding["finding_id"]
        for finding in packet["difc_aaiofi_findings"]
        if finding["status"] == DIFCFindingStatus.FAILED.value
    }
    assert "DIFC_AAOIFI_SUBSTANCE_OVER_FORM" in failed
    assert "DIFC_AAOIFI_ASSET_BACKING_OWNERSHIP" in failed
    assert "DIFC_AAOIFI_SPV_TRUSTEE_GOVERNANCE" in failed
    assert "DIFC_AAOIFI_GHARAR_UNCERTAINTY" in failed
    assert "DIFC_AAOIFI_DISCLOSURE_TRACEABILITY" in failed


def test_difc_sukuk_packet_hash_is_stable_across_replay():
    first = generate_sample_difc_sukuk_packet(drift=False)
    second = generate_sample_difc_sukuk_packet(drift=False)

    assert first["difc_aaiofi_packet_hash"] == second["difc_aaiofi_packet_hash"]


def test_difc_overlay_is_lift_out_portable_shape_before_adapter():
    candidate = sample_difc_sukuk_candidate()
    payload = candidate.to_dict()

    assert "candidate_id" in payload
    assert "asset_backing_ratio" in payload
    assert "spv_independence_score" in payload
    assert "requested_mode" not in payload
    assert "proposed_core_symbol" not in payload


def test_difc_packet_preserves_external_action_boundary():
    candidate = drifting_difc_sukuk_candidate()
    packet = generate_difc_sukuk_audit_packet(candidate)

    assert packet["automatic_action_allowed"] is False
    assert packet["core_finance_packet"]["bridge_report"]["guard_decision"]["decision"] in {
        "allow",
        "block",
    }
    assert "issuance approval" in packet["claim_boundary"]
