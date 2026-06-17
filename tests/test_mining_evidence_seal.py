from __future__ import annotations

import pytest

from pythia_mining.mining_evidence_seal import (
    MINING_EVIDENCE_SEAL_PROTOCOL,
    EvidenceSealError,
    TimestampAuthority,
    build_sealed_mining_evidence_bundle,
    redact_and_hash_runtime_config,
    seal_schema_summary,
    validate_sealed_mining_evidence_bundle,
)
from pythia_mining.mining_learning_signal import (
    MiningLearningEvent,
    compute_learning_signal_correction,
    correction_summary,
)
from pythia_mining.mining_verification_firewall import (
    CandidateVerificationPrecondition,
    assert_verification_firewall_precondition,
    build_candidate_binding_hash,
    verifier_contract,
)
from pythia_mining.pythia_mining_pitfalls_curriculum import lesson_ids, seed_mining_pitfalls_curriculum


def _firewall_decision() -> dict:
    contract = verifier_contract()
    binding = build_candidate_binding_hash(
        job_id="job-1",
        nonce=42,
        nbits="1d00ffff",
        pool_target=1000,
        job_epoch="epoch-1",
        extranonce_commitment="sha256:extranonce",
        ntime="5f5e100",
    )
    precondition = CandidateVerificationPrecondition(
        job_id="job-1",
        nonce=42,
        local_valid=True,
        block_hash="0" * 64,
        effective_target=500,
        nbits="1d00ffff",
        pool_target=1000,
        verifier_backend="cpu_parallel_exact_sha256d",
        job_epoch="epoch-1",
        extranonce_commitment="sha256:extranonce",
        ntime="5f5e100",
        candidate_binding_hash=binding,
        verifier_contract_hash=contract.contract_hash,
    )
    return assert_verification_firewall_precondition(precondition).to_dict()


def _learning_correction() -> dict:
    event = MiningLearningEvent(
        job_id="job-1",
        nonce=42,
        phi_score=0.91,
        local_valid=True,
        pool_accepted_share=True,
        pool_confirmed_block=False,
        share_target=10_000,
        block_target=100,
        block_hash_int=50,
        strategy_id="phi_scaled_compressed_solver_search",
    )
    return correction_summary(compute_learning_signal_correction(event))


def _bundle() -> dict:
    curriculum = seed_mining_pitfalls_curriculum()
    bundle = build_sealed_mining_evidence_bundle(
        mission_id="PYTHIA-ONE-BLOCK-MISSION",
        event_type="accepted_share_learning_event",
        job_context={"job_id": "job-1", "nbits": "1d00ffff", "pool_target": 1000},
        candidate={"nonce": 42, "phi_score": 0.91},
        verifier_result={"valid": True, "block_hash": "0" * 64, "backend": "cpu_parallel_exact_sha256d"},
        firewall_decision=_firewall_decision(),
        learning_correction=_learning_correction(),
        pool_response={"accepted": True, "jsonrpc_id": 7, "error": None},
        runtime_config={"pool_url": "stratum+tcp://pool.example:3333", "password": "secret", "wallet": "bc1q..."},
        lesson_ids=list(lesson_ids(curriculum)),
        timestamp_authority=TimestampAuthority(authority="unit_test_clock", unix_seconds=1_700_000_000.0),
    )
    return bundle.to_dict()


def test_sealed_mining_evidence_bundle_is_hash_committed_and_replayable() -> None:
    bundle = _bundle()

    assert bundle["protocol"] == MINING_EVIDENCE_SEAL_PROTOCOL
    assert validate_sealed_mining_evidence_bundle(bundle) is True
    assert bundle["firewall_decision"]["submission_allowed"] is True
    assert bundle["learning_correction"]["correction_reason"] == "share_ack_discounted_by_block_share_difficulty_gap"
    assert bundle["bundle_hash"]


def test_sealed_mining_evidence_bundle_detects_tampering() -> None:
    bundle = _bundle()
    bundle["candidate"]["nonce"] = 43

    with pytest.raises(EvidenceSealError, match="bundle_hash_mismatch"):
        validate_sealed_mining_evidence_bundle(bundle)


def test_runtime_config_hash_redacts_secret_material() -> None:
    first = redact_and_hash_runtime_config({"pool_url": "x", "password": "one", "wallet": "abc"})
    second = redact_and_hash_runtime_config({"pool_url": "x", "password": "two", "wallet": "def"})
    third = redact_and_hash_runtime_config({"pool_url": "y", "password": "two", "wallet": "def"})

    assert first == second
    assert first != third


def test_seal_schema_summary_names_all_dependency_protocols() -> None:
    summary = seal_schema_summary()

    assert summary["protocol"] == MINING_EVIDENCE_SEAL_PROTOCOL
    assert "PYTHIA_MINING_VERIFICATION_FIREWALL_V1" in summary["depends_on"]
    assert "PYTHIA_MINING_LEARNING_SIGNAL_V1" in summary["depends_on"]
    assert "PYTHIA_MINING_PITFALLS_CURRICULUM_V1" in summary["depends_on"]
    assert "accepted shares are learning events" in summary["success_boundary"]
