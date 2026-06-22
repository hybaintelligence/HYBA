"""VALIDATION TIER: BYZANTINE RESILIENCE."""

from pythia_mining.salamander_frontier import (
    EvidenceSealLifecycle,
    EvidenceTraitClaim,
    ImmutableEvidenceLog,
    SalamanderImmuneSystem,
    SymbioticNutrientOffer,
    SymbioticEvidenceBridge,
)


def test_siren_trait_claim_is_quarantined_for_non_physical_efficiency():
    immune = SalamanderImmuneSystem(
        min_work_per_watt_hour=1.0,
        max_work_per_watt_hour=10_000.0,
        max_error_rate=0.05,
    )
    siren = EvidenceTraitClaim(
        origin_id="siren-node",
        work_units=10_000_000_000.0,
        energy_watts=0.001,
        duration_seconds=1.0,
        error_rate=0.0,
    )

    response = immune.validate_trait(siren)

    assert response.accepted is False
    assert response.quarantined is True
    assert response.reason == "non_physical_efficiency_claim"
    assert "siren-node" in immune.quarantined_nodes


def test_evidence_tamper_breaks_peer_audit_chain():
    lifecycle = EvidenceSealLifecycle()
    original = ImmutableEvidenceLog().append(
        "capability_observed", actor="tokyo", timestamp=1.0, roi=1.0
    )
    expected_seals = lifecycle.seal_log(original)
    tampered = ImmutableEvidenceLog().append(
        "capability_observed", actor="tokyo", timestamp=1.0, roi=0.0
    )
    immune = SalamanderImmuneSystem(min_work_per_watt_hour=1.0, max_work_per_watt_hour=10.0)

    response = immune.peer_audit("tokyo", tampered, expected_seals, lifecycle)

    assert response.accepted is False
    assert response.quarantined is True
    assert response.reason == "peer_evidence_chain_invalid"


def test_vampire_symbiotic_request_without_trusted_evidence_is_rejected():
    offer = SymbioticNutrientOffer(
        origin_domain="unknown",
        target_domain="ciaas",
        resource="workers",
        amount=1000.0,
        evidence_hash="untrusted",
    )

    decision = SymbioticEvidenceBridge().evaluate_offer(
        offer,
        trusted_hashes=set(),
        requested_resource="workers",
        requested_amount=1000.0,
    )

    assert decision.accepted is False
    assert decision.reason == "untrusted_evidence_hash"
    assert decision.amount == 0.0
