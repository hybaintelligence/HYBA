from __future__ import annotations

from pythia_mining.counterfactual_reflection import (
    COUNTERFACTUAL_REFLECTION_PROTOCOL,
    DEFAULT_COUNTERFACTUAL_LEARNING_RATE,
    DEFAULT_PHI_PRIOR,
    MAX_PHI_PRIOR_DELTA,
    MIN_REFLECTION_INTERVAL_SECONDS,
    MIN_REFLECTION_OBSERVATIONS,
    PHI_PRIOR_MAX,
    PHI_PRIOR_MIN,
    SearchTrajectory,
    reflect_counterfactual_phi_prior,
)


def make_path(name: str, phi: float, block_margin: float, share_margin: float = 0.0) -> SearchTrajectory:
    return SearchTrajectory(
        trajectory_id=name,
        strategy_id="phi_path",
        phi_score=phi,
        phi_threshold=0.50,
        block_margin=block_margin,
        share_margin=share_margin,
        nonce_entropy=0.40,
        locally_valid=True,
    )


def test_reflection_updates_phi_prior_only_after_velocity_guard_is_satisfied() -> None:
    reference = make_path("reference", 0.52, -0.20, 0.70)
    alternative = make_path("alternative", 0.68, 0.30, -0.10)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.50, learning_rate=0.10)

    assert result.protocol == COUNTERFACTUAL_REFLECTION_PROTOCOL
    assert result.velocity_guard_satisfied is True
    assert result.divergence > 0.0
    assert 0.0 < result.phi_prior_delta <= MAX_PHI_PRIOR_DELTA
    assert result.updated_phi_prior > 0.50
    assert result.memory_write_target == "phi_resonance_prior"
    assert result.share_difficulty_prior_unchanged is True


def test_reflection_velocity_guard_blocks_too_frequent_updates() -> None:
    reference = make_path("reference", 0.52, -0.20)
    alternative = make_path("alternative", 0.80, 0.80)

    result = reflect_counterfactual_phi_prior(
        reference,
        alternative,
        current_phi_prior=0.50,
        observations_supporting_update=1,
        seconds_since_last_update=1.0,
        session_event_id="event-velocity",
    )

    assert result.session_event_id == "event-velocity"
    assert result.velocity_guard_satisfied is False
    assert result.phi_prior_delta == 0.0
    assert result.updated_phi_prior == 0.50
    assert result.reflection_reason == "reflection_velocity_guard_wait_for_more_evidence"


def test_reflection_reduces_phi_prior_when_block_margin_is_weaker() -> None:
    reference = make_path("reference", 0.70, 0.40)
    alternative = make_path("alternative", 0.80, -0.20)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.60, learning_rate=0.10)

    assert -MAX_PHI_PRIOR_DELTA <= result.phi_prior_delta < 0.0
    assert result.updated_phi_prior < 0.60
    assert result.reflection_reason == "alternative_phi_trajectory_weakens_block_margin_with_bounded_prior_update"


def test_reflection_does_not_update_share_difficulty_prior() -> None:
    reference = make_path("reference", 0.55, 0.10, -0.80)
    alternative = make_path("alternative", 0.90, 0.10, 0.90)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.50, learning_rate=0.10)

    assert result.memory_write_target == "phi_resonance_prior"
    assert result.share_difficulty_prior_unchanged is True
    assert "does not use share difficulty as block truth" in result.claim_boundary


def test_reflection_uses_declared_default_prior_learning_rate_and_frequency_guard() -> None:
    reference = make_path("reference", 0.52, -0.10)
    alternative = make_path("alternative", 0.72, 0.20)

    result = reflect_counterfactual_phi_prior(reference, alternative)

    assert DEFAULT_PHI_PRIOR == 0.50
    assert DEFAULT_COUNTERFACTUAL_LEARNING_RATE == 0.05
    assert MIN_REFLECTION_OBSERVATIONS == 32
    assert MIN_REFLECTION_INTERVAL_SECONDS == 60.0
    assert result.updated_phi_prior > DEFAULT_PHI_PRIOR
    assert abs(result.phi_prior_delta) <= MAX_PHI_PRIOR_DELTA


def test_reflection_clips_phi_prior_to_non_degenerate_bounds() -> None:
    strong_reference = make_path("reference", 0.60, -1.00)
    strong_alternative = make_path("alternative", 1.00, 1.00)
    upper = reflect_counterfactual_phi_prior(
        strong_reference,
        strong_alternative,
        current_phi_prior=0.99,
        learning_rate=1.00,
    )

    weak_reference = make_path("reference", 0.90, 1.00)
    weak_alternative = make_path("alternative", 0.90, -1.00)
    lower = reflect_counterfactual_phi_prior(
        weak_reference,
        weak_alternative,
        current_phi_prior=0.01,
        learning_rate=1.00,
    )

    assert upper.updated_phi_prior == PHI_PRIOR_MAX
    assert upper.phi_prior_delta == 0.0
    assert lower.updated_phi_prior == PHI_PRIOR_MIN
    assert lower.phi_prior_delta == 0.0
    assert PHI_PRIOR_MIN < DEFAULT_PHI_PRIOR < PHI_PRIOR_MAX


def test_reflection_limits_single_step_prior_delta() -> None:
    reference = make_path("reference", 0.60, -1.00)
    alternative = make_path("alternative", 1.00, 1.00)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.50, learning_rate=1.00)

    assert result.unclipped_phi_prior == 0.50 + MAX_PHI_PRIOR_DELTA
    assert result.phi_prior_delta == MAX_PHI_PRIOR_DELTA
    assert result.updated_phi_prior == 0.50 + MAX_PHI_PRIOR_DELTA
