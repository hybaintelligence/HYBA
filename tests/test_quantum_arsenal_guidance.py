from pythia_mining.nonce_resonance_guidance import (
    BlockContext,
    EmpiricalStructureEvidence,
    QuantumArsenalDirectives,
    build_nonce_resonance_guidance,
)
from pythia_mining.pythia_mining_pitfalls_curriculum import (
    seed_mining_pitfalls_curriculum,
    validate_mining_pitfalls_curriculum,
)


def test_quantum_arsenal_declares_every_component_enabled() -> None:
    arsenal = QuantumArsenalDirectives()

    assert arsenal.all_enabled()
    assert set(arsenal.enabled_components()) >= {
        "pulvini_memory_compression",
        "empirical_nonce_resonance_prior",
        "bitcoin_pool_pitfalls_curriculum",
        "autonomic_healing_feedback",
        "share_acceptance_learning",
        "exact_hash_verification",
    }


def test_guidance_seeds_empirical_prior_and_pool_pitfalls_boundaries() -> None:
    evidence = EmpiricalStructureEvidence(
        sample_size=256,
        phi15_rate=0.72,
        golden_angle_alignment=0.81,
        birthday_echo_rate=0.15,
        sector_coverage=0.85,
        dodecahedral_domain_score=0.74,
        icosahedral_face_score=0.74,
        mass_gap_valley_score=0.68,
        uniformity_score=0.62,
    )
    guidance = build_nonce_resonance_guidance(
        evidence,
        BlockContext(block_height=840000, difficulty=1.0, target_hex="00" * 32),
    )
    curriculum = seed_mining_pitfalls_curriculum()

    assert guidance.empirical_evidence.enough_evidence()
    assert guidance.arsenal.all_enabled()
    assert validate_mining_pitfalls_curriculum(curriculum)
    assert any("Pool-side ACK" in boundary for boundary in guidance.claim_boundary)
    assert any("pitfalls curriculum" in boundary for boundary in guidance.claim_boundary)
