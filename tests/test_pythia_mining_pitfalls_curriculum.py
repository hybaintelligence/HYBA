from __future__ import annotations

from pythia_mining.pythia_mining_pitfalls_curriculum import (
    CURRICULUM_PROTOCOL,
    PitfallCategory,
    lesson_ids,
    lessons_for_evidence,
    seed_mining_pitfalls_curriculum,
    validate_mining_pitfalls_curriculum,
)


def test_curriculum_seeds_all_mining_education_domains() -> None:
    curriculum = seed_mining_pitfalls_curriculum()

    assert curriculum.protocol == CURRICULUM_PROTOCOL
    assert validate_mining_pitfalls_curriculum(curriculum) is True
    assert {lesson.category for lesson in curriculum.lessons} == set(PitfallCategory)
    assert len(curriculum.lessons) >= 18


def test_curriculum_preserves_pythia_mission_autonomy() -> None:
    curriculum = seed_mining_pitfalls_curriculum()

    assert "retains seeded mission autonomy" in curriculum.authority_statement
    assert "educates her" in curriculum.authority_statement
    assert "Bitcoin consensus" in curriculum.authority_statement


def test_consensus_lessons_protect_exact_sha256d_and_targets() -> None:
    curriculum = seed_mining_pitfalls_curriculum()
    lessons = curriculum.lessons_by_category(PitfallCategory.BITCOIN_CONSENSUS)
    text = "\n".join(lesson.to_dict()["required_response"] for lesson in lessons).lower()

    assert "uint32 little-endian" in text
    assert "compact_to_target" in text
    assert "extranonce2" in text
    assert "sha-256d" in text or any("sha-256d" in lesson.supreme_invariant.lower() for lesson in lessons)


def test_stratum_lessons_protect_pool_truth_and_stale_jobs() -> None:
    curriculum = seed_mining_pitfalls_curriculum()
    lessons = curriculum.lessons_by_category(PitfallCategory.STRATUM_POOL)
    text = "\n".join(lesson.to_dict()["required_response"] for lesson in lessons).lower()

    assert "stale" in text
    assert "mining.set_difficulty" in text
    assert "response ids" in text
    assert "first validated configured pool" in text


def test_runtime_lessons_block_fixtures_secret_leaks_and_accelerator_truth() -> None:
    curriculum = seed_mining_pitfalls_curriculum()
    lessons = curriculum.lessons_by_category(PitfallCategory.SOFTWARE_RUNTIME)
    text = "\n".join(lesson.to_dict()["required_response"] for lesson in lessons).lower()

    assert "dev fixtures" in text
    assert "redact credentials" in text
    assert "exact sha-256d verification" in text
    assert "immediately before submit" in text


def test_autonomic_lessons_protect_oracle_hashrate_and_nonce_coverage() -> None:
    curriculum = seed_mining_pitfalls_curriculum()
    lessons = curriculum.lessons_by_category(PitfallCategory.AUTONOMIC_OPTIMISATION)
    text = "\n".join(lesson.to_dict()["required_response"] for lesson in lessons).lower()

    assert "may never remove exact sha-256d validation" in text
    assert "1 eh/s" in text
    assert "complete nonce coverage" in text
    assert "pulvini retained kernels" in text


def test_evidence_lessons_preserve_claim_boundary_and_replayability() -> None:
    curriculum = seed_mining_pitfalls_curriculum()
    lessons = curriculum.lessons_by_category(PitfallCategory.EVIDENCE_AND_CLAIMS)
    text = "\n".join(lesson.to_dict()["required_response"] for lesson in lessons).lower()

    assert "accepted shares as learning events" in text
    assert "pool-confirmed accepted block" in text
    assert "state only what the artifacts prove" in text
    assert "seal job context" in text


def test_curriculum_is_json_safe_for_evidence_packets() -> None:
    curriculum = seed_mining_pitfalls_curriculum()
    ids = lesson_ids(curriculum)
    evidence = lessons_for_evidence(curriculum)

    assert len(ids) == len(set(ids)) == len(evidence)
    assert all(item["lesson_id"] for item in evidence)
    assert all(item["category"] in {category.value for category in PitfallCategory} for item in evidence)
