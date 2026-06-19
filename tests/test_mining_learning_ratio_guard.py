from __future__ import annotations

from pythia_mining.mining_learning_signal import (
    MiningLearningEvent,
    compute_learning_signal_correction,
)


def test_learning_difficulty_gap_ratio_is_never_above_one_for_valid_targets() -> None:
    event = MiningLearningEvent(
        job_id="job-ratio",
        nonce=7,
        phi_score=0.9,
        local_valid=True,
        pool_accepted_share=True,
        pool_confirmed_block=False,
        share_target=10_000,
        block_target=100,
        block_hash_int=50,
        strategy_id="phi_scaled_compressed_solver_search",
    )

    correction = compute_learning_signal_correction(event)

    assert 0.0 <= correction.difficulty_gap_ratio <= 1.0
    assert correction.phi_block_update_weight <= correction.phi_share_update_weight
    assert correction.amplitude_amplification_allowed is False
