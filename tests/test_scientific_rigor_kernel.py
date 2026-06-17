from __future__ import annotations

from pythia_mining.scientific_rigor_kernel import (
    DEFAULT_CAUSAL_INTEGRATION_FLOOR,
    RevocationDisposition,
    SCIENTIFIC_RIGOR_PROTOCOL,
    ScientificClaimStatus,
    assess_penrose_obligation,
    compute_causal_integration_telemetry,
)


def test_penrose_obligation_requires_external_truth_after_local_truth() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {"exact_local_truth": True, "external_truth": False},
        evidence_ids=("EV-LOCAL-001",),
    )

    assert obligation.protocol == SCIENTIFIC_RIGOR_PROTOCOL
    assert obligation.status == ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
    assert obligation.reentry_required is True
    assert obligation.next_required_status == ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
    assert obligation.cannot_self_certify is True
    assert "cannot self-certify" in obligation.claim_boundary


def test_penrose_obligation_marks_falsified_evidence() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {"exact_local_truth": True, "external_truth": False, "falsified": True},
    )

    assert obligation.status == ScientificClaimStatus.FALSIFIED.value
    assert obligation.reentry_required is False
    assert "prevents escalation" in obligation.falsification_route


def test_penrose_obligation_allows_externally_confirmed_claim_only_with_both_truths() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {"exact_local_truth": True, "external_truth": True},
    )

    assert obligation.status == ScientificClaimStatus.EXTERNALLY_CONFIRMED.value
    assert obligation.reentry_required is False


def test_penrose_obligation_reenters_after_stale_job_revocation() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {
            "exact_local_truth": True,
            "external_truth": True,
            "pool_confirmation_revoked": True,
            "revocation_reason": "stale job race after pool invalidation",
        },
        evidence_ids=("EV-POOL-ACK-001", "EV-POOL-REVOKE-001"),
    )

    assert obligation.status == ScientificClaimStatus.CONFIRMED_THEN_REVOKED.value
    assert obligation.reentry_required is True
    assert obligation.next_required_status == ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
    assert obligation.revocation_disposition == RevocationDisposition.REENTER_EXTERNAL_TRUTH.value
    assert "stale job" in obligation.revocation_reason
    assert "revocation" in obligation.falsification_route


def test_penrose_obligation_falsifies_invalid_hash_revocation() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {
            "exact_local_truth": True,
            "external_truth": True,
            "pool_confirmation_revoked": True,
            "revocation_reason": "invalid hash does not meet target",
        },
    )

    assert obligation.status == ScientificClaimStatus.FALSIFIED.value
    assert obligation.reentry_required is False
    assert obligation.revocation_disposition == RevocationDisposition.FALSIFIED_INVALID_LOCAL_OR_EXTERNAL_TRUTH.value


def test_penrose_obligation_re_evaluates_vardiff_revocation() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {
            "exact_local_truth": True,
            "external_truth": True,
            "pool_confirmation_revoked": True,
            "revocation_reason": "vardiff target changed and difficulty boundary crossed",
        },
    )

    assert obligation.status == ScientificClaimStatus.CONFIRMED_THEN_REVOKED.value
    assert obligation.reentry_required is True
    assert obligation.revocation_disposition == RevocationDisposition.REEVALUATE_AGAINST_UPDATED_TARGET.value
    assert obligation.next_required_status == ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value


def test_causal_integration_telemetry_covers_required_evidence_channels() -> None:
    telemetry = compute_causal_integration_telemetry(
        {
            "verifier_firewall": True,
            "job_binding": True,
            "external_truth": False,
            "learning_correction": 0.8,
            "evidence_seal": True,
            "pitfalls_curriculum": True,
        }
    )

    assert telemetry.protocol == SCIENTIFIC_RIGOR_PROTOCOL
    assert set(telemetry.channels) == {
        "verifier_firewall",
        "job_binding",
        "external_truth",
        "learning_correction",
        "evidence_seal",
        "pitfalls_curriculum",
    }
    assert telemetry.channel_scores["external_truth"] == 0.0
    assert telemetry.whole_score < 1.0
    assert telemetry.operational_phi_floor_score == 0.0
    assert telemetry.floor_threshold == DEFAULT_CAUSAL_INTEGRATION_FLOOR
    assert telemetry.escalation_allowed is False
    assert "floor_failed" in telemetry.escalation_reason
    assert "not exact IIT Phi" in telemetry.claim_boundary
    assert "not a consciousness claim" in telemetry.claim_boundary


def test_causal_integration_telemetry_penalises_missing_partition() -> None:
    complete = compute_causal_integration_telemetry(
        {
            "verifier_firewall": True,
            "job_binding": True,
            "external_truth": True,
            "learning_correction": True,
            "evidence_seal": True,
            "pitfalls_curriculum": True,
        }
    )
    incomplete = compute_causal_integration_telemetry(
        {
            "verifier_firewall": True,
            "job_binding": True,
            "external_truth": False,
            "learning_correction": True,
            "evidence_seal": True,
            "pitfalls_curriculum": True,
        }
    )

    assert complete.whole_score == 1.0
    assert complete.operational_phi_floor_score == 1.0
    assert complete.escalation_allowed is True
    assert incomplete.whole_score < complete.whole_score
    assert incomplete.phi_proxy <= complete.phi_proxy
    assert incomplete.escalation_allowed is False


def test_causal_integration_floor_threshold_blocks_weak_chain() -> None:
    telemetry = compute_causal_integration_telemetry(
        {
            "verifier_firewall": True,
            "job_binding": True,
            "external_truth": True,
            "learning_correction": 0.50,
            "evidence_seal": True,
            "pitfalls_curriculum": True,
        },
        floor_threshold=0.75,
    )

    assert telemetry.operational_phi_floor_score < telemetry.floor_threshold
    assert telemetry.escalation_allowed is False
    assert telemetry.escalation_reason == "causal_integration_floor_failed_escalation_blocked"


def test_causal_integration_maps_negative_and_error_inputs_to_zero() -> None:
    telemetry = compute_causal_integration_telemetry(
        {
            "verifier_firewall": True,
            "job_binding": True,
            "external_truth": True,
            "learning_correction": -0.25,
            "evidence_seal": "error",
            "pitfalls_curriculum": "unrecognised",
        }
    )

    assert telemetry.channel_scores["learning_correction"] == 0.0
    assert telemetry.channel_scores["evidence_seal"] == 0.0
    assert telemetry.channel_scores["pitfalls_curriculum"] == 0.0
    assert telemetry.operational_phi_floor_score == 0.0
    assert telemetry.escalation_allowed is False
    assert set(telemetry.sanitized_channels) >= {"learning_correction", "evidence_seal", "pitfalls_curriculum"}
    assert "mapped to [0,1]" in telemetry.score_domain_policy
