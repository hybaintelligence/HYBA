"""Scientific rigor kernel for PYTHIA mining evidence.

This module is intentionally small and side-effect free. It does not start work,
connect to anything, submit anything, or alter PYTHIA autonomy. It gives PYTHIA
machine-readable scientific obligations: proof humility and causal integration
telemetry.

Penrose boundary: autonomous reasoning cannot self-certify external truth.
IIT boundary: integration telemetry is not exact IIT Phi and not a consciousness
claim; it is an operational evidence-coherence measure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Mapping, Sequence, Tuple

SCIENTIFIC_RIGOR_PROTOCOL = "PYTHIA_MINING_SCIENTIFIC_RIGOR_KERNEL_V2"
DEFAULT_CAUSAL_INTEGRATION_FLOOR = 0.75


class ScientificClaimStatus(str, Enum):
    PROVISIONAL = "provisional"
    REQUIRES_EXTERNAL_TRUTH = "requires_external_truth"
    FALSIFIED = "falsified"
    EXTERNALLY_CONFIRMED = "externally_confirmed"
    CONFIRMED_THEN_REVOKED = "confirmed_then_revoked"


@dataclass(frozen=True)
class PenroseProofObligation:
    protocol: str
    claim: str
    status: str
    required_truth_condition: str
    evidence_ids: Tuple[str, ...]
    falsification_route: str
    cannot_self_certify: bool
    claim_boundary: str
    reentry_required: bool = False
    revocation_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CausalIntegrationTelemetry:
    protocol: str
    channels: Tuple[str, ...]
    channel_scores: Dict[str, float]
    whole_score: float
    weakest_partition: str
    weakest_partition_score: float
    phi_proxy: float
    operational_phi_floor_score: float
    floor_threshold: float
    escalation_allowed: bool
    escalation_reason: str
    claim_boundary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _score(value: Any) -> float:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return max(0.0, min(1.0, float(value)))
    return 1.0 if value else 0.0


def assess_penrose_obligation(
    claim: str,
    evidence: Mapping[str, Any],
    evidence_ids: Sequence[str] = (),
) -> PenroseProofObligation:
    """Classify a claim according to external-truth obligations.

    External confirmation is not monotonic in live mining. Pool-side stale-job
    races, reorg-like invalidation, vardiff correction, or explicit pool reversal
    may revoke a previously confirmed claim. Revocation therefore has a distinct
    state and forces re-entry into the external-truth obligation path.
    """

    exact_local_truth = bool(evidence.get("exact_local_truth", False))
    external_truth = bool(evidence.get("external_truth", False))
    falsified = bool(evidence.get("falsified", False))
    revoked = bool(
        evidence.get("external_truth_revoked", False)
        or evidence.get("pool_confirmation_revoked", False)
        or evidence.get("confirmed_then_revoked", False)
    )
    revocation_reason = str(
        evidence.get("revocation_reason")
        or evidence.get("pool_revocation_reason")
        or "external confirmation was revoked; return to proof obligation"
    )

    if falsified:
        status = ScientificClaimStatus.FALSIFIED.value
        reentry_required = False
    elif revoked:
        status = ScientificClaimStatus.CONFIRMED_THEN_REVOKED.value
        reentry_required = True
    elif exact_local_truth and external_truth:
        status = ScientificClaimStatus.EXTERNALLY_CONFIRMED.value
        reentry_required = False
    elif exact_local_truth:
        status = ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
        reentry_required = True
    else:
        status = ScientificClaimStatus.PROVISIONAL.value
        reentry_required = True

    return PenroseProofObligation(
        protocol=SCIENTIFIC_RIGOR_PROTOCOL,
        claim=claim,
        status=status,
        required_truth_condition="Exact local verification plus non-revoked external confirmation for external success claims.",
        evidence_ids=tuple(evidence_ids),
        falsification_route=(
            "Any verifier failure, stale context, external rejection, revocation, or missing replay seal prevents escalation."
        ),
        cannot_self_certify=True,
        claim_boundary="Penrose-style proof humility: PYTHIA may reason autonomously but cannot self-certify external truth.",
        reentry_required=reentry_required,
        revocation_reason=revocation_reason if revoked else "",
    )


def compute_causal_integration_telemetry(
    channels: Mapping[str, Any],
    floor_threshold: float = DEFAULT_CAUSAL_INTEGRATION_FLOOR,
) -> CausalIntegrationTelemetry:
    """Compute IIT-style evidence-channel integration telemetry.

    This is an engineering proxy over evidence channels, not exact IIT Phi. The
    floor score gives the instrument a decision boundary: if the weakest causal
    channel collapses, escalation is blocked even when the average remains high.
    """

    if not (0.0 <= float(floor_threshold) <= 1.0):
        raise ValueError("floor_threshold_must_be_unit_interval")

    required = (
        "verifier_firewall",
        "job_binding",
        "external_truth",
        "learning_correction",
        "evidence_seal",
        "pitfalls_curriculum",
    )
    scores = {name: _score(channels.get(name, 0.0)) for name in required}
    whole = sum(scores.values()) / len(required)
    partition_scores = {}
    for name in required:
        remaining = [score for channel, score in scores.items() if channel != name]
        partition_scores[name] = sum(remaining) / len(remaining)
    weakest = min(partition_scores, key=partition_scores.get)
    weakest_score = partition_scores[weakest]
    phi_proxy = max(0.0, whole - weakest_score) + (0.10 * min(scores.values()))
    operational_floor_score = whole * min(scores.values())
    escalation_allowed = operational_floor_score >= floor_threshold
    escalation_reason = (
        "causal_integration_floor_satisfied"
        if escalation_allowed
        else "causal_integration_floor_failed_escalation_blocked"
    )
    return CausalIntegrationTelemetry(
        protocol=SCIENTIFIC_RIGOR_PROTOCOL,
        channels=required,
        channel_scores=scores,
        whole_score=whole,
        weakest_partition=weakest,
        weakest_partition_score=weakest_score,
        phi_proxy=phi_proxy,
        operational_phi_floor_score=operational_floor_score,
        floor_threshold=float(floor_threshold),
        escalation_allowed=escalation_allowed,
        escalation_reason=escalation_reason,
        claim_boundary="IIT-style causal integration telemetry only; not exact IIT Phi and not a consciousness claim.",
    )


__all__ = [
    "DEFAULT_CAUSAL_INTEGRATION_FLOOR",
    "SCIENTIFIC_RIGOR_PROTOCOL",
    "CausalIntegrationTelemetry",
    "PenroseProofObligation",
    "ScientificClaimStatus",
    "assess_penrose_obligation",
    "compute_causal_integration_telemetry",
]
