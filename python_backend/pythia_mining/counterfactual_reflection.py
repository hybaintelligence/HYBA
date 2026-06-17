"""Counterfactual reflection kernel for PYTHIA phi-resonant mining search.

This module is side-effect free. It compares a reference search trajectory with
an alternative trajectory and emits a memory-write proposal that updates the
phi-resonance prior, not the share-difficulty prior. It does not submit, connect,
or mutate the live mining runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

COUNTERFACTUAL_REFLECTION_PROTOCOL = "PYTHIA_MINING_COUNTERFACTUAL_REFLECTION_V2"
DEFAULT_PHI_PRIOR = 0.50
DEFAULT_COUNTERFACTUAL_LEARNING_RATE = 0.05
PHI_PRIOR_MIN = 0.20
PHI_PRIOR_MAX = 0.80
MAX_PHI_PRIOR_DELTA = 0.025


@dataclass(frozen=True)
class SearchTrajectory:
    trajectory_id: str
    strategy_id: str
    phi_score: float
    phi_threshold: float
    block_margin: float
    share_margin: float
    nonce_entropy: float
    locally_valid: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CounterfactualReflection:
    protocol: str
    reference: SearchTrajectory
    alternative: SearchTrajectory
    divergence: float
    phi_prior_delta: float
    unclipped_phi_prior: float
    updated_phi_prior: float
    phi_prior_min: float
    phi_prior_max: float
    max_phi_prior_delta: float
    memory_write_target: str
    share_difficulty_prior_unchanged: bool
    reflection_reason: str
    claim_boundary: str

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["reference"] = self.reference.to_dict()
        payload["alternative"] = self.alternative.to_dict()
        return payload


def _unit(value: float, field_name: str) -> float:
    value = float(value)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name}_must_be_unit_interval")
    return value


def _strict_unit_bound(value: float, field_name: str) -> float:
    value = float(value)
    if not 0.0 < value < 1.0:
        raise ValueError(f"{field_name}_must_be_open_unit_interval")
    return value


def _signed_unit(value: float, field_name: str) -> float:
    value = float(value)
    if not -1.0 <= value <= 1.0:
        raise ValueError(f"{field_name}_must_be_signed_unit_interval")
    return value


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def _bounded_delta(value: float, limit: float) -> float:
    return _clamp(value, -limit, limit)


def reflect_counterfactual_phi_prior(
    reference: SearchTrajectory,
    alternative: SearchTrajectory,
    current_phi_prior: float = DEFAULT_PHI_PRIOR,
    learning_rate: float = DEFAULT_COUNTERFACTUAL_LEARNING_RATE,
    phi_prior_min: float = PHI_PRIOR_MIN,
    phi_prior_max: float = PHI_PRIOR_MAX,
    max_phi_prior_delta: float = MAX_PHI_PRIOR_DELTA,
) -> CounterfactualReflection:
    """Compare trajectories and propose a bounded phi-prior update.

    ``block_margin`` is the block-level signal. ``share_margin`` is retained as
    context but does not drive the prior update. This prevents share-difficulty
    feedback from becoming a phi-resonance prior.

    The prior is clipped into a strict sub-interval of (0, 1). The lower bound
    prevents disabling phi-resonant search; the upper bound prevents a run of
    favourable counterfactuals from collapsing the search topology into an
    overconfident point mass.
    """

    lower = _strict_unit_bound(phi_prior_min, "phi_prior_min")
    upper = _strict_unit_bound(phi_prior_max, "phi_prior_max")
    if not lower < upper:
        raise ValueError("phi_prior_bounds_must_be_ordered")
    limit = _unit(max_phi_prior_delta, "max_phi_prior_delta")
    prior = _clamp(_unit(current_phi_prior, "current_phi_prior"), lower, upper)
    rate = _unit(learning_rate, "learning_rate")
    for trajectory in (reference, alternative):
        _unit(trajectory.phi_score, "phi_score")
        _unit(trajectory.phi_threshold, "phi_threshold")
        _signed_unit(trajectory.block_margin, "block_margin")
        _signed_unit(trajectory.share_margin, "share_margin")
        _unit(trajectory.nonce_entropy, "nonce_entropy")

    strategy_delta = 0.0 if reference.strategy_id == alternative.strategy_id else 1.0
    divergence = _clamp(
        0.45 * abs(alternative.phi_score - reference.phi_score)
        + 0.30 * abs(alternative.block_margin - reference.block_margin)
        + 0.15 * abs(alternative.nonce_entropy - reference.nonce_entropy)
        + 0.10 * strategy_delta,
        0.0,
        1.0,
    )

    reference_signal = reference.block_margin if reference.locally_valid else -1.0
    alternative_signal = alternative.block_margin if alternative.locally_valid else -1.0
    evidence_delta = alternative_signal - reference_signal
    phi_gate = 1.0 if alternative.phi_score >= alternative.phi_threshold else -0.5
    raw_delta = rate * evidence_delta * phi_gate
    phi_prior_delta = _bounded_delta(raw_delta, limit)
    unclipped_prior = prior + phi_prior_delta
    updated_prior = _clamp(unclipped_prior, lower, upper)
    effective_delta = updated_prior - prior

    if effective_delta > 0:
        reason = "alternative_phi_trajectory_improves_block_margin_with_bounded_prior_update"
    elif effective_delta < 0:
        reason = "alternative_phi_trajectory_weakens_block_margin_with_bounded_prior_update"
    else:
        reason = "counterfactual_phi_prior_unchanged_or_clipped_at_bound"

    return CounterfactualReflection(
        protocol=COUNTERFACTUAL_REFLECTION_PROTOCOL,
        reference=reference,
        alternative=alternative,
        divergence=divergence,
        phi_prior_delta=effective_delta,
        unclipped_phi_prior=unclipped_prior,
        updated_phi_prior=updated_prior,
        phi_prior_min=lower,
        phi_prior_max=upper,
        max_phi_prior_delta=limit,
        memory_write_target="phi_resonance_prior",
        share_difficulty_prior_unchanged=True,
        reflection_reason=reason,
        claim_boundary=(
            "Counterfactual reflection updates bounded phi-resonance priors only; it does not certify external truth, "
            "does not use share difficulty as block truth, and does not mutate the live runtime."
        ),
    )


__all__ = [
    "COUNTERFACTUAL_REFLECTION_PROTOCOL",
    "DEFAULT_COUNTERFACTUAL_LEARNING_RATE",
    "DEFAULT_PHI_PRIOR",
    "MAX_PHI_PRIOR_DELTA",
    "PHI_PRIOR_MAX",
    "PHI_PRIOR_MIN",
    "CounterfactualReflection",
    "SearchTrajectory",
    "reflect_counterfactual_phi_prior",
]
