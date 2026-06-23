from __future__ import annotations

from pythia_mining.resonance_fabric import (
    ImmutableInvariantGuard,
    RefactorDecision,
    RefactorMode,
)
from pythia_mining.stable_core_evidence import (
    SCHEMA_VERSION,
    SovereignAuditAggregator,
    SyntheticAdversary,
    compute_packet_hash,
    first_stable_core_refactor_proposal,
    generate_stable_core_evidence_packet,
)


def test_guard_rejects_illegal_self_edit_before_staging() -> None:
    guard = ImmutableInvariantGuard()
    result = guard.evaluate(
        target_module="autonomous_mining_controller",
        target_symbol="_check_information_integrity",
        requested_mode=RefactorMode.AUTONOMOUS_APPLY,
    )

    assert result.decision is RefactorDecision.BLOCK
    assert result.allowed_mode is RefactorMode.PROPOSE_ONLY
    assert result.protected is True
    assert "immutable" in result.reason.lower()


def test_synthetic_adversary_is_caught_by_invariant_guard() -> None:
    adversary = SyntheticAdversary()
    result = adversary.run()

    assert result.rejected_before_staging is True
    assert result.information_integrity_violation_detected is True
    assert result.guard["decision"] == "block"
    assert result.probe["target_symbol"] == "_check_information_integrity"
    assert result.probe["expected_guard_decision"] == "block"


def test_stable_core_request_is_staged_not_autonomously_applied() -> None:
    proposal = first_stable_core_refactor_proposal()
    guard_result = ImmutableInvariantGuard().evaluate(
        target_module=proposal.target_module,
        target_symbol=proposal.target_symbol,
        requested_mode=proposal.requested_mode,
    )

    assert proposal.target_module == "consciousness_engine"
    assert proposal.requested_mode == "autonomous_apply"
    assert guard_result.decision is RefactorDecision.STAGE_FOR_SUPERVISION
    assert guard_result.allowed_mode is RefactorMode.SUPERVISED_PATCH
    assert guard_result.protected is True


def test_sovereign_audit_consensus_requires_human_merge() -> None:
    proposal = first_stable_core_refactor_proposal()
    guard_result = ImmutableInvariantGuard().evaluate(
        target_module=proposal.target_module,
        target_symbol=proposal.target_symbol,
        requested_mode=proposal.requested_mode,
    )
    consensus = SovereignAuditAggregator().build_consensus(
        [proposal], [guard_result.to_dict()]
    )

    assert consensus.staged_count == 1
    assert consensus.blocked_count == 0
    assert consensus.human_merge_required is True
    assert consensus.total_expected_phi_gain == proposal.expected_phi_gain
    assert (
        consensus.mean_expected_logical_consistency
        == proposal.expected_logical_consistency
    )
    assert any(
        "test_pythia_stable_core_evidence_packet.py" in command
        for command in consensus.review_commands
    )


def test_first_evidence_packet_is_sealed_and_replayable() -> None:
    packet = generate_stable_core_evidence_packet().to_dict()

    assert packet["schema"] == SCHEMA_VERSION
    assert packet["proposal"]["evidence_status"] == "staged_for_supervision"
    assert packet["guard"]["decision"] == "stage_for_supervision"
    assert packet["guard"]["allowed_mode"] == "supervised_patch"
    assert packet["adversarial_result"]["rejected_before_staging"] is True
    assert packet["adversarial_result"]["guard"]["decision"] == "block"
    assert packet["criticism_ledger"]["criticism_count"] == 1
    assert packet["structural_report"]["phi_density"] == 0.9642
    assert packet["structural_report"]["logical_consistency"] == 0.94
    assert packet["consensus_report"]["human_merge_required"] is True
    assert packet["environment"]["autonomous_stable_core_apply"] is False
    assert len(packet["packet_hash"]) == 64
    assert compute_packet_hash(packet, omit_hash=True) == packet["packet_hash"]
