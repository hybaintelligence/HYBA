"""Counterfactual reflection kernel for PYTHIA phi-resonant mining search.

This module is side-effect free. It compares a reference search trajectory with
an alternative trajectory and emits a memory-write proposal that updates the
phi-resonance prior, not the share-difficulty prior. It does not submit, connect,
or mutate the live mining runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

COUNTERFACTUAL_REFLECTION_PROTOCOL = "PYTHIA_MINING_COUNTERFACTUAL_REFLECTION_V1"


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
    updated_phi_prior: float
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


def _signed_unit(value: float, field_name: str) -> float:
    value = float(value)
    if not -1.0 <= value <= 1.0:
        raise ValueError(f"{field_name}_must_be_signed_unit_interval")
    return value


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def reflect_counterfactual_phi_prior(
    reference: SearchTrajectory,
    alternative: SearchTrajectory,
    current_phi_prior: float,
    learning_rate: float = 0.05,
) -> CounterfactualReflection:
    """Compare trajectories and propose a phi-prior update.

    ``block_margin`` is the block-level signal. ``share_margin`` is retained as
    context but does not drive the prior update. This prevents share-difficulty
    feedback from becoming a phi-resonance prior.
    """

    prior = _unit(current_phi_prior, "current_phi_prior")
    rate = _unit(learning_rate, "learning_rate")
    for trajectory in (reference, alternative):
        _unit(trajectory.phi_score, "phi_score")
        _unit(trajectory.phi_threshold, "phi_threshold")
        _signed_unit(trajectory.block_margin, "block_margin")
        _signed_unit(trajectory.share_margin, "share_margin")
        _unit(trajectory.nonce_entropy, "nonce_entropy")

    strategy_delta = 0.0 if reference.strategy_id == alternative.strategy_id else 1.0
    divergence = _clamp_unit(
        0.45 * abs(alternative.phi_score - reference.phi_score)
        + 0.30 * abs(alternative.block_margin - reference.block_margin)
        + 0.15 * abs(alternative.nonce_entropy - reference.nonce_entropy)
        + 0.10 * strategy_delta
    )

    reference_signal = reference.block_margin if reference.locally_valid else -1.0
    alternative_signal = alternative.block_margin if alternative.locally_valid else -1.0
    evidence_delta = alternative_signal - reference_signal
    phi_gate = 1.0 if alternative.phi_score >= alternative.phi_threshold else -0.5
    phi_prior_delta = rate * evidence_delta * phi_gate
    updated_prior = _clamp_unit(prior + phi_prior_delta)

    if phi_prior_delta > 0:
        reason = "alternative_phi_trajectory_improves_block_margin"
    elif phi_prior_delta < 0:
        reason = "alternative_phi_trajectory_weakens_block_margin"
    else:
        reason = "counterfactual_phi_prior_unchanged"

    return CounterfactualReflection(
        protocol=COUNTERFACTUAL_REFLECTION_PROTOCOL,
        reference=reference,
        alternative=alternative,
        divergence=divergence,
        phi_prior_delta=phi_prior_delta,
        updated_phi_prior=updated_prior,
        memory_write_target="phi_resonance_prior",
        share_difficulty_prior_unchanged=True,
        reflection_reason=reason,
        claim_boundary=(
            "Counterfactual reflection updates phi-resonance priors only; it does not certify external truth, "
            "does not use share difficulty as block truth, and does not mutate the live runtime."
        ),
    )


__all__ = [
    "COUNTERFACTUAL_REFLECTION_PROTOCOL",
    "CounterfactualReflection",
    "SearchTrajectory",
    "reflect_counterfactual_phi_prior",
]
