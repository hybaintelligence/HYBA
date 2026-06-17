from __future__ import annotations

import pytest

from pythia_mining.mining_evidence_seal import (
    MINING_EVIDENCE_SEAL_PROTOCOL,
    TIMESTAMP_AUTHORITY,
    EvidenceSealError,
    bitcoin_job_timestamp_authority,
    build_sealed_mining_evidence_bundle,
    derive_session_event_id,
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


def _firewall_decision(session_event_id: str = "") -> dict:
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
    payload = assert_verification_firewall_precondition(precondition).to_dict()
    if session_event_id:
        payload["session_event_id"] = session_event_id
    return payload


def _learning_correction(session_event_id: str = "") -> dict:
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
    payload = correction_summary(compute_learning_signal_correction(event))
    if session_event_id:
        payload["session_event_id"] = session_event_id
    return payload


def _job_context() -> dict:
    return {
        "job_id": "job-1",
        "nbits": "1d00ffff",
        "pool_target": 1000,
        "bitcoin_block_height": 840_000,
        "prevhash": "11" * 32,
    }


def _candidate() -> dict:
    return {"candidate_id": "candidate-1", "nonce": 42, "phi_score": 0.91}


def _bundle(session_event_id: str = "") -> dict:
    curriculum = seed_mining_pitfalls_curriculum()
    event_id = session_event_id or derive_session_event_id(
        mission_id="PYTHIA-ONE-BLOCK-MISSION",
        event_type="accepted_share_learning_event",
        job_context=_job_context(),
        candidate=_candidate(),
    )
    bundle = build_sealed_mining_evidence_bundle(
        mission_id="PYTHIA-ONE-BLOCK-MISSION",
        event_type="accepted_share_learning_event",
        job_context=_job_context(),
        candidate=_candidate(),
        verifier_result={"valid": True, "block_hash": "0" * 64, "backend": "cpu_parallel_exact_sha256d", "session_event_id": event_id},
        firewall_decision=_firewall_decision(event_id),
        learning_correction=_learning_correction(event_id),
        pool_response={"accepted": True, "jsonrpc_id": 7, "error": None, "session_event_id": event_id},
        runtime_config={"pool_url": "stratum+tcp://pool.example:3333", "password": "private", "wallet": "bc1q..."},
        lesson_ids=list(lesson_ids(curriculum)),
        session_event_id=event_id,
    )
    return bundle.to_dict()


def test_sealed_mining_evidence_bundle_is_hash_committed_and_replayable() -> None:
    bundle = _bundle()

    assert bundle["protocol"] == MINING_EVIDENCE_SEAL_PROTOCOL
    assert validate_sealed_mining_evidence_bundle(bundle) is True
    assert bundle["session_event_id"]
    assert bundle["firewall_decision"]["submission_allowed"] is True
    assert bundle["learning_correction"]["correction_reason"] == "share_ack_discounted_by_block_share_difficulty_gap"
    assert bundle["timestamp_authority"]["authority"] == TIMESTAMP_AUTHORITY
    assert bundle["timestamp_authority"]["bitcoin_block_height"] == 840_000
    assert bundle["timestamp_authority"]["stratum_job_id"] == "job-1"
    assert bundle["timestamp_authority"]["anchor_hash"]
    assert bundle["bundle_hash"]


def test_session_event_id_is_deterministic_join_key() -> None:
    first = derive_session_event_id(
        mission_id="PYTHIA-ONE-BLOCK-MISSION",
        event_type="accepted_share_learning_event",
        job_context=_job_context(),
        candidate=_candidate(),
    )
    second = derive_session_event_id(
        mission_id="PYTHIA-ONE-BLOCK-MISSION",
        event_type="accepted_share_learning_event",
        job_context=_job_context(),
        candidate=_candidate(),
    )

    assert first == second
    assert _bundle(first)["session_event_id"] == first


def test_session_event_id_mismatch_is_rejected() -> None:
    bundle = _bundle("session-a")
    bundle["learning_correction"]["session_event_id"] = "session-b"

    with pytest.raises(EvidenceSealError, match="session_event_id_mismatch:learning_correction|bundle_hash_mismatch"):
        validate_sealed_mining_evidence_bundle(bundle)


def test_bitcoin_job_timestamp_authority_requires_height_job_and_prevhash() -> None:
    authority = bitcoin_job_timestamp_authority(_job_context(), unix_seconds=1_700_000_000.0)

    assert authority.authority == TIMESTAMP_AUTHORITY
    assert authority.bitcoin_block_height == 840_000
    assert authority.stratum_job_id == "job-1"
    assert authority.job_prevhash == "11" * 32

    with pytest.raises(EvidenceSealError, match="missing_bitcoin_block_height_anchor"):
        bitcoin_job_timestamp_authority({"job_id": "job-1", "prevhash": "11" * 32})


def test_sealed_mining_evidence_bundle_detects_tampering() -> None:
    bundle = _bundle()
    bundle["candidate"]["nonce"] = 43

    with pytest.raises(EvidenceSealError, match="bundle_hash_mismatch"):
        validate_sealed_mining_evidence_bundle(bundle)


def test_sealed_mining_evidence_bundle_detects_timestamp_anchor_tampering() -> None:
    bundle = _bundle()
    bundle["timestamp_authority"]["bitcoin_block_height"] = 840_001

    with pytest.raises(EvidenceSealError, match="timestamp_anchor_hash_mismatch|bundle_hash_mismatch"):
        validate_sealed_mining_evidence_bundle(bundle)


def test_runtime_config_hash_redacts_private_material() -> None:
    first = redact_and_hash_runtime_config({"pool_url": "x", "password": "one", "wallet": "abc"})
    second = redact_and_hash_runtime_config({"pool_url": "x", "password": "two", "wallet": "def"})
    third = redact_and_hash_runtime_config({"pool_url": "y", "password": "two", "wallet": "def"})

    assert first == second
    assert first != third


def test_seal_schema_summary_names_all_dependency_protocols() -> None:
    summary = seal_schema_summary()

    assert summary["protocol"] == MINING_EVIDENCE_SEAL_PROTOCOL
    assert summary["timestamp_authority"] == TIMESTAMP_AUTHORITY
    assert "PYTHIA_MINING_VERIFICATION_FIREWALL_V1" in summary["depends_on"]
    assert "PYTHIA_MINING_LEARNING_SIGNAL_V1" in summary["depends_on"]
    assert "PYTHIA_MINING_PITFALLS_CURRICULUM_V1" in summary["depends_on"]
    assert "session_event_id" in summary["required_bundle_parts"]
    assert "bitcoin_block_height" in summary["required_bundle_parts"]
    assert "accepted shares are learning events" in summary["success_boundary"]
