"""Mining learning-signal correction for PYTHIA.

Accepted shares are useful learning events, but they are not accepted blocks. This
module formalises that gap so PYTHIA's search topology can learn from pool ACKs
without confusing share difficulty with block difficulty.

The model is intentionally conservative: share ACKs increase operational
confidence and pool/job alignment memory, while block-level learning remains
weighted by the probability mass that survives the stricter block target.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

LEARNING_SIGNAL_PROTOCOL = "PYTHIA_MINING_LEARNING_SIGNAL_V1"
PHI_THRESHOLD = 0.5
MIN_PROBABILITY = 1e-18


class LearningSignalError(ValueError):
    """Raised when a learning event is malformed or unsafe."""


@dataclass(frozen=True)
class MiningLearningEvent:
    """A single pool/local feedback event for PYTHIA learning."""

    job_id: str
    nonce: int
    phi_score: float
    local_valid: bool
    pool_accepted_share: bool
    pool_confirmed_block: bool
    share_target: int
    block_target: int
    block_hash_int: int
    strategy_id: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LearningSignalCorrection:
    """Corrected learning weights separating share ACKs from block truth."""

    protocol: str
    event: MiningLearningEvent
    share_likelihood: float
    block_likelihood: float
    difficulty_gap_ratio: float
    phi_share_update_weight: float
    phi_block_update_weight: float
    topology_update_allowed: bool
    amplitude_amplification_allowed: bool
    correction_reason: str

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["event"] = self.event.to_dict()
        return payload


def _clamp_probability(value: float) -> float:
    if math.isnan(value) or math.isinf(value):
        raise LearningSignalError("invalid_probability")
    return min(1.0, max(MIN_PROBABILITY, float(value)))


def _target_probability(target: int) -> float:
    if int(target) <= 0:
        raise LearningSignalError("target_must_be_positive")
    # Probability a uniformly sampled 256-bit hash is below target.
    return int(target) / float(2**256)


def compute_learning_signal_correction(event: MiningLearningEvent) -> LearningSignalCorrection:
    """Return a conservative update that prevents share difficulty drift.

    Formula intuition:
      share_likelihood = P(hash <= share_target)
      block_likelihood = P(hash <= block_target)
      difficulty_gap_ratio = block_likelihood / share_likelihood

    A pool share ACK may update operational/search-context confidence, but the
    phi amplitude update is discounted by the block/share gap unless a true
    pool-confirmed block is present.

    The correction is only valid when ``difficulty_gap_ratio <= 1``. If a pool
    or vardiff event presents a share target stricter than the block target or
    otherwise inverts this ratio, PYTHIA must halt learning for that event rather
    than overweighting share ACKs as block evidence.
    """

    if not (0.0 <= float(event.phi_score) <= 1.0):
        raise LearningSignalError("phi_score_must_be_unit_interval")
    if int(event.block_target) <= 0 or int(event.share_target) <= 0:
        raise LearningSignalError("targets_must_be_positive")
    if int(event.block_target) > int(event.share_target):
        raise LearningSignalError("block_target_must_not_be_easier_than_share_target")
    if event.pool_confirmed_block and not event.pool_accepted_share:
        raise LearningSignalError("confirmed_block_requires_pool_share_acceptance")

    share_likelihood = _target_probability(event.share_target)
    block_likelihood = _target_probability(event.block_target)
    raw_difficulty_gap_ratio = block_likelihood / share_likelihood
    if raw_difficulty_gap_ratio > 1.0:
        raise LearningSignalError("difficulty_gap_ratio_inversion")
    difficulty_gap_ratio = _clamp_probability(raw_difficulty_gap_ratio)

    phi_mass = 1.0 if event.phi_score >= PHI_THRESHOLD else 0.25
    share_update = phi_mass if event.pool_accepted_share and event.local_valid else 0.0
    block_update = (
        phi_mass
        if event.pool_confirmed_block
        else share_update * difficulty_gap_ratio
    )

    topology_allowed = bool(event.local_valid and (event.pool_accepted_share or not event.pool_confirmed_block))
    amplitude_allowed = bool(event.pool_confirmed_block)
    reason = (
        "pool_confirmed_block_full_block_weight"
        if event.pool_confirmed_block
        else "share_ack_discounted_by_block_share_difficulty_gap"
        if event.pool_accepted_share
        else "rejection_updates_negative_operational_memory_only"
    )

    return LearningSignalCorrection(
        protocol=LEARNING_SIGNAL_PROTOCOL,
        event=event,
        share_likelihood=share_likelihood,
        block_likelihood=block_likelihood,
        difficulty_gap_ratio=difficulty_gap_ratio,
        phi_share_update_weight=share_update,
        phi_block_update_weight=block_update,
        topology_update_allowed=topology_allowed,
        amplitude_amplification_allowed=amplitude_allowed,
        correction_reason=reason,
    )


def correction_summary(correction: LearningSignalCorrection) -> Dict[str, Any]:
    """Compact summary for evidence packets and PYTHIA memory."""

    return {
        "protocol": correction.protocol,
        "job_id": correction.event.job_id,
        "pool_accepted_share": correction.event.pool_accepted_share,
        "pool_confirmed_block": correction.event.pool_confirmed_block,
        "difficulty_gap_ratio": correction.difficulty_gap_ratio,
        "phi_share_update_weight": correction.phi_share_update_weight,
        "phi_block_update_weight": correction.phi_block_update_weight,
        "amplitude_amplification_allowed": correction.amplitude_amplification_allowed,
        "correction_reason": correction.correction_reason,
    }


def validate_learning_correction_policy(payload: Mapping[str, Any]) -> bool:
    """Machine-check a learning correction payload."""

    return (
        payload.get("protocol") == LEARNING_SIGNAL_PROTOCOL
        and 0.0 <= float(payload.get("difficulty_gap_ratio", -1.0)) <= 1.0
        and float(payload.get("phi_block_update_weight", 0.0)) <= float(payload.get("phi_share_update_weight", 1.0))
        and (
            bool(payload.get("pool_confirmed_block"))
            or payload.get("amplitude_amplification_allowed") is False
        )
    )


__all__ = [
    "LEARNING_SIGNAL_PROTOCOL",
    "MIN_PROBABILITY",
    "PHI_THRESHOLD",
    "LearningSignalCorrection",
    "LearningSignalError",
    "MiningLearningEvent",
    "compute_learning_signal_correction",
    "correction_summary",
    "validate_learning_correction_policy",
]
