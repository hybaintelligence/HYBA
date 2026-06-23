from __future__ import annotations

from pythia_mining.counterfactual_reflection import (
    SearchTrajectory,
    _derive_reflection_episode_id,
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
    alternative = _trajectory(
        trajectory_id="traj-alt", block_margin=0.4, phi_score=0.85
    )

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5
    )

    assert result.phi_prior_delta > 0
    assert result.updated_phi_prior > 0.5
    assert (
        result.reflection_reason
        == "alternative_phi_trajectory_improves_block_margin_with_bounded_prior_update"
    )
    assert result.memory_write_target == "phi_resonance_prior"
    assert result.share_difficulty_prior_unchanged is True


def test_counterfactual_reflection_penalizes_when_alternative_has_worse_block_margin():
    reference = _trajectory(block_margin=0.4, phi_score=0.80)
    alternative = _trajectory(
        trajectory_id="traj-alt", block_margin=0.1, phi_score=0.80
    )

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5
    )

    assert result.phi_prior_delta < 0
    assert result.updated_phi_prior < 0.5
    assert (
        result.reflection_reason
        == "alternative_phi_trajectory_weakens_block_margin_with_bounded_prior_update"
    )


def test_counterfactual_reflection_does_not_update_share_difficulty_prior():
    reference = _trajectory(block_margin=0.1)
    alternative = _trajectory(trajectory_id="traj-alt", block_margin=0.4)

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5
    )

    assert result.share_difficulty_prior_unchanged is True
    assert "phi_resonance_prior" in result.memory_write_target
    assert "share_difficulty" not in result.memory_write_target


def test_counterfactual_reflection_preserves_claim_boundary():
    reference = _trajectory()
    alternative = _trajectory(trajectory_id="traj-alt")

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5
    )

    assert "does not certify external truth" in result.claim_boundary
    assert "does not use share difficulty as block truth" in result.claim_boundary
    assert "does not mutate the live runtime" in result.claim_boundary


def test_counterfactual_reflection_rejects_share_margin_update():
    reference = _trajectory(block_margin=0.1, share_margin=0.5)
    alternative = _trajectory(
        trajectory_id="traj-alt", block_margin=0.1, share_margin=0.9
    )

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5
    )

    assert (
        result.reflection_reason
        == "counterfactual_phi_prior_unchanged_or_clipped_at_bound"
    )
    assert result.updated_phi_prior == 0.5


def test_reflection_episode_id_is_present_and_deterministic():
    reference = _trajectory(trajectory_id="traj-ref")
    alternative = _trajectory(trajectory_id="traj-alt")

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5
    )

    assert result.reflection_episode_id is not None
    assert len(result.reflection_episode_id) == 32
    expected = _derive_reflection_episode_id("traj-ref", "traj-alt")
    assert result.reflection_episode_id == expected


def test_reflection_episode_id_differs_from_session_event_id():
    reference = _trajectory(trajectory_id="traj-ref")
    alternative = _trajectory(trajectory_id="traj-alt")

    result = reflect_counterfactual_phi_prior(
        reference, alternative, current_phi_prior=0.5, session_event_id="session-xyz"
    )

    assert result.session_event_id == "session-xyz"
    assert result.reflection_episode_id != result.session_event_id
    expected = _derive_reflection_episode_id("traj-ref", "traj-alt")
    assert result.reflection_episode_id == expected


def test_reflection_episode_id_can_be_overridden():
    reference = _trajectory(trajectory_id="traj-ref")
    alternative = _trajectory(trajectory_id="traj-alt")

    result = reflect_counterfactual_phi_prior(
        reference,
        alternative,
        current_phi_prior=0.5,
        reflection_episode_id="explicit-episode-001",
    )

    assert result.reflection_episode_id == "explicit-episode-001"


def test_reflection_episode_id_reproducible_from_pair():
    """Different callers with same trajectory ids produce same episode id."""
    reference_a = _trajectory(trajectory_id="t1")
    alternative_a = _trajectory(trajectory_id="t2")
    reference_b = _trajectory(trajectory_id="t1")
    alternative_b = _trajectory(trajectory_id="t2")

    result_a = reflect_counterfactual_phi_prior(
        reference_a, alternative_a, current_phi_prior=0.5
    )
    result_b = reflect_counterfactual_phi_prior(
        reference_b,
        alternative_b,
        current_phi_prior=0.5,
        session_event_id="different-session",
    )

    assert result_a.reflection_episode_id == result_b.reflection_episode_id
    assert result_a.session_event_id == ""
    assert result_b.session_event_id == "different-session"
    assert result_a.reflection_episode_id != result_b.session_event_id
