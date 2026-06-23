from pythia_mining.blockchain_structure_intelligence import (
    MiningGuardrailInputs,
    MiningLaunchDecision,
    StructureEvidenceStatus,
    build_pythia_structure_intelligence_packet,
    evaluate_pythia_mining_guardrails,
    extract_empirical_structure_evidence,
)


def _empirical_report():
    return {
        "summary": {
            "total_blocks": 144,
            "phi_resonance_rate": 0.54,
            "mean_resonance_strength": 0.71,
            "birthday_echo_rate": 0.08,
        },
        "nonce_space_analysis": {
            "golden_angle_alignment": 0.31,
            "sunflower_score": 0.42,
            "sector_coverage_pct": 87.5,
            "uniformity_p_value": 0.64,
            "max_gap_size": 1024,
        },
    }


def test_empirical_structure_becomes_pythia_search_prior():
    evidence = extract_empirical_structure_evidence(_empirical_report())
    packet = build_pythia_structure_intelligence_packet(evidence)

    assert evidence.total_blocks == 144
    assert evidence.status in {
        StructureEvidenceStatus.OBSERVED,
        StructureEvidenceStatus.STRONG,
    }
    assert evidence.evidence_is_usable_as_prior is True
    assert packet.pythia_directives["use_as"] == "search_traversal_prior_only"
    assert (
        "retain_exact_sha256d_verification"
        in packet.pythia_directives["preferred_runtime_effect"]
    )
    assert (
        "do_not_bypass_sha256d_verifier"
        in packet.pythia_directives["forbidden_runtime_effect"]
    )
    assert len(packet.packet_hash) == 64


def test_guardrails_block_live_launch_without_operator_and_pool():
    evidence = extract_empirical_structure_evidence(_empirical_report())
    packet = build_pythia_structure_intelligence_packet(evidence)

    report = evaluate_pythia_mining_guardrails(
        packet,
        MiningGuardrailInputs(
            operator_approval=False,
            pool_credentials_present=False,
            exact_sha256d_verifier_enabled=True,
            evidence_packet_present=True,
            requested_live_mode=True,
        ),
    )

    assert report.decision == MiningLaunchDecision.BLOCK
    assert report.launch_permitted is False
    assert any("operator approval" in reason for reason in report.reasons)
    assert any("pool credentials" in reason for reason in report.reasons)


def test_guardrails_allow_only_guarded_live_readiness_when_all_preconditions_hold():
    evidence = extract_empirical_structure_evidence(_empirical_report())
    packet = build_pythia_structure_intelligence_packet(evidence)

    report = evaluate_pythia_mining_guardrails(
        packet,
        MiningGuardrailInputs(
            operator_approval=True,
            pool_credentials_present=True,
            exact_sha256d_verifier_enabled=True,
            evidence_packet_present=True,
            accepted_share_proof_present=False,
            funding_action_requested=False,
            requested_live_mode=True,
            max_runtime_minutes=15,
            max_power_watts=800,
            claim_text="Empirical structure prior with exact SHA-256d verification.",
        ),
    )

    assert report.decision == MiningLaunchDecision.GUARDED_LIVE_READY
    assert report.launch_permitted is True
    assert report.funding_actions_permitted is False
    assert report.guardrails["exact_sha256d_final_oracle"] is True
    assert report.guardrails["pool_side_accepted_share_required_for_funding"] is True


def test_guardrails_block_funding_without_accepted_share_proof():
    evidence = extract_empirical_structure_evidence(_empirical_report())
    packet = build_pythia_structure_intelligence_packet(evidence)

    report = evaluate_pythia_mining_guardrails(
        packet,
        MiningGuardrailInputs(
            operator_approval=True,
            pool_credentials_present=True,
            exact_sha256d_verifier_enabled=True,
            evidence_packet_present=True,
            accepted_share_proof_present=False,
            funding_action_requested=True,
            requested_live_mode=True,
            max_runtime_minutes=15,
        ),
    )

    assert report.decision == MiningLaunchDecision.BLOCK
    assert report.funding_actions_permitted is False
    assert any("accepted-share proof" in reason for reason in report.reasons)


def test_guardrails_reject_guaranteed_revenue_language():
    evidence = extract_empirical_structure_evidence(_empirical_report())
    packet = build_pythia_structure_intelligence_packet(evidence)

    report = evaluate_pythia_mining_guardrails(
        packet,
        MiningGuardrailInputs(
            operator_approval=True,
            pool_credentials_present=True,
            exact_sha256d_verifier_enabled=True,
            evidence_packet_present=True,
            requested_live_mode=True,
            claim_text="Guaranteed risk-free block discovery.",
        ),
    )

    assert report.decision == MiningLaunchDecision.BLOCK
    assert any("forbidden guaranteed-revenue" in reason for reason in report.reasons)


def test_insufficient_evidence_stays_in_dry_run():
    evidence = extract_empirical_structure_evidence({"summary": {"total_blocks": 4}})
    packet = build_pythia_structure_intelligence_packet(evidence)

    report = evaluate_pythia_mining_guardrails(
        packet,
        MiningGuardrailInputs(
            operator_approval=True,
            pool_credentials_present=True,
            exact_sha256d_verifier_enabled=True,
            evidence_packet_present=True,
            requested_live_mode=True,
        ),
    )

    assert evidence.status == StructureEvidenceStatus.INSUFFICIENT
    assert report.decision == MiningLaunchDecision.BLOCK
    assert any("insufficient" in reason for reason in report.reasons)
