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
        session_event_id="event-1",
    )

    assert obligation.protocol == SCIENTIFIC_RIGOR_PROTOCOL
    assert obligation.session_event_id == "event-1"
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
    assert obligation.revocation_classifier_source == "text_fallback"
    assert "stale job" in obligation.revocation_reason


def test_penrose_obligation_uses_pool_code_before_text() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {
            "exact_local_truth": True,
            "external_truth": True,
            "pool_confirmation_revoked": True,
            "pool_response_code": "23",
            "revocation_reason": "message says try again later",
        },
    )

    assert obligation.status == ScientificClaimStatus.FALSIFIED.value
    assert obligation.reentry_required is False
    assert (
        obligation.revocation_disposition
        == RevocationDisposition.FALSIFIED_INVALID_LOCAL_OR_EXTERNAL_TRUTH.value
    )
    assert obligation.revocation_classifier_source == "pool_response_code"


def test_penrose_obligation_unclassified_pool_code_reenters_conservatively() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {
            "exact_local_truth": True,
            "external_truth": True,
            "pool_confirmation_revoked": True,
            "pool_response_code": "novel-extension-777",
            "revocation_reason": "unrecognised pool extension response",
        },
    )

    assert obligation.status == ScientificClaimStatus.CONFIRMED_THEN_REVOKED.value
    assert obligation.reentry_required is True
    assert obligation.revocation_disposition == RevocationDisposition.UNCLASSIFIED_REVOCATION.value
    assert obligation.next_required_status == ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value


def test_penrose_obligation_re_evaluates_vardiff_revocation() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {
            "exact_local_truth": True,
            "external_truth": True,
            "pool_confirmation_revoked": True,
            "pool_response_code": "vardiff_target_changed",
            "revocation_reason": "target changed and difficulty boundary crossed",
        },
    )

    assert obligation.status == ScientificClaimStatus.CONFIRMED_THEN_REVOKED.value
    assert obligation.reentry_required is True
    assert (
        obligation.revocation_disposition
        == RevocationDisposition.REEVALUATE_AGAINST_UPDATED_TARGET.value
    )
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
        },
        session_event_id="event-1",
    )

    assert telemetry.protocol == SCIENTIFIC_RIGOR_PROTOCOL
    assert telemetry.session_event_id == "event-1"
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
    assert set(telemetry.sanitized_channels) >= {
        "learning_correction",
        "evidence_seal",
        "pitfalls_curriculum",
    }
    assert "mapped to [0,1]" in telemetry.score_domain_policy


def test_reproducibility_attestation_is_order_stable_and_boundary_limited() -> None:
    from pythia_mining.scientific_rigor_kernel import build_reproducibility_attestation

    first = build_reproducibility_attestation(
        "runtime_integration_proxy_not_consciousness_claim",
        {"metrics": {"phi": 0.5, "channels": ["a", "b"]}, "version": 1},
        ["PYTHONPATH=python_backend pytest tests/test_scientific_rigor_kernel.py -q"],
        seeds={"numpy": 42, "python_hash_seed": 0},
        dependency_pins={"python": "3.12"},
        boundary="Local deterministic replay only; not phenomenal consciousness or external validation.",
    )
    second = build_reproducibility_attestation(
        "runtime_integration_proxy_not_consciousness_claim",
        {"version": 1, "metrics": {"channels": ["a", "b"], "phi": 0.5}},
        ["PYTHONPATH=python_backend pytest tests/test_scientific_rigor_kernel.py -q"],
        seeds={"python_hash_seed": 0, "numpy": 42},
        dependency_pins={"python": "3.12"},
        boundary="Local deterministic replay only; not phenomenal consciousness or external validation.",
    )

    assert first.reproducible is True
    assert first.input_digest == second.input_digest
    assert first.replay_digest == second.replay_digest
    assert "not phenomenal consciousness" in first.boundary
    assert "Digest mismatch" in first.falsification_route


def test_reproducibility_attestation_changes_when_seed_changes() -> None:
    from pythia_mining.scientific_rigor_kernel import build_reproducibility_attestation

    baseline = build_reproducibility_attestation(
        "phi_scaling_bounded",
        {"sample": [1, 2, 3]},
        ["pytest hyba_intelligence_tests/test_phi_scaling_engine.py -q"],
        seeds={"numpy": 42},
    )
    changed = build_reproducibility_attestation(
        "phi_scaling_bounded",
        {"sample": [1, 2, 3]},
        ["pytest hyba_intelligence_tests/test_phi_scaling_engine.py -q"],
        seeds={"numpy": 43},
    )

    assert baseline.input_digest == changed.input_digest
    assert baseline.replay_digest != changed.replay_digest
