from __future__ import annotations

from pythia_mining.counterfactual_reflection import (
    COUNTERFACTUAL_REFLECTION_PROTOCOL,
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


def test_reflection_updates_phi_prior_only() -> None:
    reference = make_path("reference", 0.52, -0.20, 0.70)
    alternative = make_path("alternative", 0.68, 0.30, -0.10)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.50, learning_rate=0.10)

    assert result.protocol == COUNTERFACTUAL_REFLECTION_PROTOCOL
    assert result.divergence > 0.0
    assert result.phi_prior_delta > 0.0
    assert result.updated_phi_prior > 0.50
    assert result.memory_write_target == "phi_resonance_prior"
    assert result.share_difficulty_prior_unchanged is True


def test_reflection_reduces_phi_prior_when_block_margin_is_weaker() -> None:
    reference = make_path("reference", 0.70, 0.40)
    alternative = make_path("alternative", 0.80, -0.20)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.60, learning_rate=0.10)

    assert result.phi_prior_delta < 0.0
    assert result.updated_phi_prior < 0.60
    assert result.reflection_reason == "alternative_phi_trajectory_weakens_block_margin"


def test_reflection_does_not_update_share_difficulty_prior() -> None:
    reference = make_path("reference", 0.55, 0.10, -0.80)
    alternative = make_path("alternative", 0.90, 0.10, 0.90)

    result = reflect_counterfactual_phi_prior(reference, alternative, current_phi_prior=0.50, learning_rate=0.10)

    assert result.memory_write_target == "phi_resonance_prior"
    assert result.share_difficulty_prior_unchanged is True
    assert "does not use share difficulty as block truth" in result.claim_boundary
