from __future__ import annotations

import pytest

from pythia_mining.mining_learning_signal import (
    LEARNING_SIGNAL_PROTOCOL,
    LearningSignalError,
    MiningLearningEvent,
    compute_learning_signal_correction,
    correction_summary,
    validate_learning_correction_policy,
)


def _event(**overrides: object) -> MiningLearningEvent:
    payload = {
        "job_id": "job-1",
        "nonce": 42,
        "phi_score": 0.91,
        "local_valid": True,
        "pool_accepted_share": True,
        "pool_confirmed_block": False,
        "share_target": 10_000,
        "block_target": 100,  # block_target must be <= share_target
        "block_hash_int": 50,
        "strategy_id": "phi_scaled_compressed_solver_search",
    }
    payload.update(overrides)
    return MiningLearningEvent(**payload)


def test_share_ack_learning_is_discounted_by_block_share_gap() -> None:
    correction = compute_learning_signal_correction(_event())

    assert correction.protocol == LEARNING_SIGNAL_PROTOCOL
    assert correction.pool_accepted_share if hasattr(correction, "pool_accepted_share") else correction.event.pool_accepted_share
    assert correction.event.pool_confirmed_block is False
    assert correction.difficulty_gap_ratio == pytest.approx(0.01)
    assert correction.phi_share_update_weight == pytest.approx(1.0)
    assert correction.phi_block_update_weight == pytest.approx(0.01)
    assert correction.amplitude_amplification_allowed is False
    assert correction.correction_reason == "share_ack_discounted_by_block_share_difficulty_gap"
    assert validate_learning_correction_policy(correction_summary(correction))


def test_pool_confirmed_block_gets_full_block_weight() -> None:
    correction = compute_learning_signal_correction(_event(pool_confirmed_block=True))

    assert correction.phi_block_update_weight == pytest.approx(1.0)
    assert correction.amplitude_amplification_allowed is True
    assert correction.correction_reason == "pool_confirmed_block_full_block_weight"
    assert validate_learning_correction_policy(correction_summary(correction))


def test_rejected_share_updates_negative_operational_memory_only() -> None:
    correction = compute_learning_signal_correction(
        _event(pool_accepted_share=False, pool_confirmed_block=False, local_valid=False)
    )

    assert correction.phi_share_update_weight == 0.0
    assert correction.phi_block_update_weight == 0.0
    assert correction.amplitude_amplification_allowed is False
    assert correction.correction_reason == "rejection_updates_negative_operational_memory_only"
    assert validate_learning_correction_policy(correction_summary(correction))


def test_learning_signal_rejects_block_target_easier_than_share_target() -> None:
    with pytest.raises(LearningSignalError, match="block_target_must_not_be_easier_than_share_target"):
        compute_learning_signal_correction(_event(block_target=20_000))


def test_learning_signal_rejects_confirmed_block_without_pool_share_acceptance() -> None:
    with pytest.raises(LearningSignalError, match="confirmed_block_requires_pool_share_acceptance"):
        compute_learning_signal_correction(_event(pool_accepted_share=False, pool_confirmed_block=True))
