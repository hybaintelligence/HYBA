from __future__ import annotations

from pythia_mining.scientific_rigor_kernel import (
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
    assert obligation.cannot_self_certify is True
    assert "cannot self-certify" in obligation.claim_boundary


def test_penrose_obligation_marks_falsified_evidence() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {"exact_local_truth": True, "external_truth": False, "falsified": True},
    )

    assert obligation.status == ScientificClaimStatus.FALSIFIED.value
    assert "prevents escalation" in obligation.falsification_route


def test_penrose_obligation_allows_externally_confirmed_claim_only_with_both_truths() -> None:
    obligation = assess_penrose_obligation(
        "candidate is externally successful",
        {"exact_local_truth": True, "external_truth": True},
    )

    assert obligation.status == ScientificClaimStatus.EXTERNALLY_CONFIRMED.value


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
    assert incomplete.whole_score < complete.whole_score
    assert incomplete.phi_proxy <= complete.phi_proxy
