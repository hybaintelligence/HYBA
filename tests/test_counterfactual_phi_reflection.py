from __future__ import annotations

from pythia_mining.counterfactual_reflection import (
    COUNTERFACTUAL_REFLECTION_PROTOCOL,
    SearchTrajectory,
    reflect_counterfactual_phi_prior,
)


def _trajectory(trajectory_id: str = "traj-1", **overrides):
    base = {
        "trajectory_id": trajectory_id,
        "strategy_id": "strategy-a",
        "phi_score": 0.8,
        "phi_threshold": 0.75,
        "block_margin": 0.2,
        "share_margin": 0.0,
        "nonce_entropy": 0.5,
        "locally_valid": True,
    }
    base.update(overrides)
    return SearchTrajectory(**base)


def test_counterfactual_reflection_increases_phi_prior_when_alternative_improves_block_margin():
    reference = _trajectory(block_margin=0.1)
    alternative = _trajectory(trajectory_id="traj-alt", block_margin=0.4, phi_score=0.85)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.5)

    assert result.phi_prior_delta > 0
    assert result.updated_phi_prior > 0.5
    assert result.reflection_reason == "alternative_phi_trajectory_improves_block_margin_with_bounded_prior_update"
    assert result.memory_write_target == "phi_resonance_prior"
    assert result.share_difficulty_prior_unchanged is True


def test_counterfactual_reflection_penalizes_when_alternative_has_worse_block_margin():
    reference = _trajectory(block_margin=0.4, phi_score=0.80)
    alternative = _trajectory(trajectory_id="traj-alt", block_margin=0.1, phi_score=0.80)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.5)

    assert result.phi_prior_delta < 0
    assert result.updated_phi_prior < 0.5
    assert result.reflection_reason == "alternative_phi_trajectory_weakens_block_margin_with_bounded_prior_update"


def test_counterfactual_reflection_does_not_update_share_difficulty_prior():
    reference = _trajectory(block_margin=0.1)
    alternative = _trajectory(trajectory_id="traj-alt", block_margin=0.4)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.5)

    assert result.share_difficulty_prior_unchanged is True
    assert "phi_resonance_prior" in result.memory_write_target
    assert "share_difficulty" not in result.memory_write_target


def test_counterfactual_reflection_preserves_claim_boundary():
    reference = _trajectory()
    alternative = _trajectory(trajectory_id="traj-alt")

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.5)

    assert "does not certify external truth" in result.claim_boundary
    assert "does not use share difficulty as block truth" in result.claim_boundary
    assert "does not mutate the live runtime" in result.claim_boundary


def test_counterfactual_reflection_rejects_share_margin_update():
    reference = _trajectory(block_margin=0.1, share_margin=0.5)
    alternative = _trajectory(trajectory_id="traj-alt", block_margin=0.1, share_margin=0.9)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.5)

    assert result.reflection_reason == "counterfactual_phi_prior_unchanged_or_clipped_at_bound"
    assert result.updated_phi_prior == 0.5