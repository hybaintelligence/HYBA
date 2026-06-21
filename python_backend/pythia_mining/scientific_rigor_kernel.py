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
import hashlib
import json
import platform
import sys
from typing import Any, Dict, Mapping, Sequence, Tuple

SCIENTIFIC_RIGOR_PROTOCOL = "PYTHIA_MINING_SCIENTIFIC_RIGOR_KERNEL_V4"
DEFAULT_CAUSAL_INTEGRATION_FLOOR = 0.75


class ScientificClaimStatus(str, Enum):
    PROVISIONAL = "provisional"
    REQUIRES_EXTERNAL_TRUTH = "requires_external_truth"
    FALSIFIED = "falsified"
    EXTERNALLY_CONFIRMED = "externally_confirmed"
    CONFIRMED_THEN_REVOKED = "confirmed_then_revoked"


class RevocationDisposition(str, Enum):
    """Machine-readable re-entry/falsification disposition for revoked truth."""

    NONE = "none"
    REENTER_EXTERNAL_TRUTH = "reenter_external_truth"
    REEVALUATE_AGAINST_UPDATED_TARGET = "reevaluate_against_updated_target"
    FALSIFIED_INVALID_LOCAL_OR_EXTERNAL_TRUTH = "falsified_invalid_local_or_external_truth"
    UNCLASSIFIED_REVOCATION = "unclassified_revocation"


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
    session_event_id: str = ""
    reentry_required: bool = False
    revocation_reason: str = ""
    revocation_disposition: str = RevocationDisposition.NONE.value
    revocation_classifier_source: str = "none"
    next_required_status: str = ""

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
    score_domain_policy: str
    sanitized_channels: Tuple[str, ...]
    session_event_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReproducibilityAttestation:
    """Deterministic replay envelope for scientific and operational claims.

    The attestation is intentionally local and conservative: it records exactly
    which inputs, commands, seeds, dependency pins, and claim boundaries were
    used to produce a result. It is an audit checksum, not independent peer
    review and not external truth confirmation.
    """

    protocol: str
    claim_id: str
    commands: Tuple[str, ...]
    produced_artifacts: Tuple[str, ...]
    input_digest: str
    replay_digest: str
    environment: Dict[str, str]
    seeds: Dict[str, int]
    dependency_pins: Dict[str, str]
    reproducible: bool
    boundary: str
    falsification_route: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _score(value: Any) -> Tuple[float, bool]:
    """Return a score in [0, 1] and whether the input was sanitized."""

    if isinstance(value, bool):
        return (1.0 if value else 0.0), False
    if value is None:
        return 0.0, True
    if isinstance(value, (int, float)):
        numeric = float(value)
        clamped = max(0.0, min(1.0, numeric))
        return clamped, clamped != numeric
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "pass", "passed", "ok", "valid", "confirmed"}:
            return 1.0, False
        if normalized in {
            "false",
            "fail",
            "failed",
            "error",
            "invalid",
            "missing",
            "none",
            "unknown",
            "revoked",
        }:
            return 0.0, True
        return 0.0, True
    return 0.0, True


def _extract_revocation_code(evidence: Mapping[str, Any]) -> str:
    raw = (
        evidence.get("pool_response_code")
        or evidence.get("stratum_error_code")
        or evidence.get("pool_error_code")
        or evidence.get("revocation_code")
        or evidence.get("error_code")
        or ""
    )
    return str(raw).strip().lower()


def _revocation_disposition(
    evidence: Mapping[str, Any], reason: str
) -> Tuple[RevocationDisposition, str]:
    """Classify revocation code-first, with text only as fallback.

    Unknown response codes do not become falsification. They are explicit
    unclassified revocations and conservatively re-enter the external-truth path.
    """

    code = _extract_revocation_code(evidence)
    falsifying_codes = {
        "23",
        "low_difficulty",
        "low-difficulty",
        "invalid_hash",
        "bad_hash",
        "invalid_pow",
        "invalid_proof",
        "invalid_share",
        "malformed_header",
        "merkle_mismatch",
    }
    reevaluate_codes = {
        "vardiff",
        "vardiff_update",
        "vardiff_target_changed",
        "target_changed",
        "target_update",
        "difficulty_changed",
        "new_target",
    }
    reentry_codes = {
        "21",
        "22",
        "stale",
        "stale_job",
        "job_not_found",
        "job_expired",
        "duplicate_share",
        "late_submit",
        "previous_job",
    }
    if code:
        if code in falsifying_codes:
            return (
                RevocationDisposition.FALSIFIED_INVALID_LOCAL_OR_EXTERNAL_TRUTH,
                "pool_response_code",
            )
        if code in reevaluate_codes:
            return RevocationDisposition.REEVALUATE_AGAINST_UPDATED_TARGET, "pool_response_code"
        if code in reentry_codes:
            return RevocationDisposition.REENTER_EXTERNAL_TRUTH, "pool_response_code"
        return RevocationDisposition.UNCLASSIFIED_REVOCATION, "pool_response_code"

    explicit = str(
        evidence.get("revocation_type") or evidence.get("pool_revocation_type") or ""
    ).lower()
    haystack = f"{explicit} {reason.lower()}"
    falsifying_terms = (
        "invalid hash",
        "bad hash",
        "invalid pow",
        "invalid proof",
        "invalid share",
        "malformed header",
        "merkle mismatch",
        "target failure",
        "local verifier failed",
        "hash does not meet target",
    )
    reevaluate_terms = (
        "vardiff",
        "difficulty boundary",
        "new target",
        "target changed",
        "difficulty changed",
        "boundary crossed",
        "pool target update",
    )
    reentry_terms = (
        "stale",
        "stale job",
        "job invalidation",
        "job expired",
        "reorg",
        "pool invalidation",
        "late submit",
        "previous job",
    )
    if any(term in haystack for term in falsifying_terms):
        return RevocationDisposition.FALSIFIED_INVALID_LOCAL_OR_EXTERNAL_TRUTH, "text_fallback"
    if any(term in haystack for term in reevaluate_terms):
        return RevocationDisposition.REEVALUATE_AGAINST_UPDATED_TARGET, "text_fallback"
    if any(term in haystack for term in reentry_terms):
        return RevocationDisposition.REENTER_EXTERNAL_TRUTH, "text_fallback"
    return RevocationDisposition.UNCLASSIFIED_REVOCATION, "text_fallback"


def assess_penrose_obligation(
    claim: str,
    evidence: Mapping[str, Any],
    evidence_ids: Sequence[str] = (),
    session_event_id: str = "",
) -> PenroseProofObligation:
    """Classify a claim according to external-truth obligations.

    External confirmation is not monotonic in live mining. Revocation transition
    conditions are explicit and code-first:

    * stale/job/reorg-style revocation re-enters external-truth proof obligation;
    * invalid-hash / invalid-proof revocation terminates as falsified;
    * vardiff/target-boundary revocation requires re-evaluation against the new
      target before any renewed external-truth claim;
    * unclassified revocation conservatively re-enters proof and is not falsified.
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
    disposition, classifier_source = (
        _revocation_disposition(evidence, revocation_reason)
        if revoked
        else (RevocationDisposition.NONE, "none")
    )

    if falsified:
        status = ScientificClaimStatus.FALSIFIED.value
        reentry_required = False
        next_required_status = ""
    elif revoked and disposition == RevocationDisposition.FALSIFIED_INVALID_LOCAL_OR_EXTERNAL_TRUTH:
        status = ScientificClaimStatus.FALSIFIED.value
        reentry_required = False
        next_required_status = ""
    elif revoked:
        status = ScientificClaimStatus.CONFIRMED_THEN_REVOKED.value
        reentry_required = True
        next_required_status = ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
    elif exact_local_truth and external_truth:
        status = ScientificClaimStatus.EXTERNALLY_CONFIRMED.value
        reentry_required = False
        next_required_status = ""
    elif exact_local_truth:
        status = ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
        reentry_required = True
        next_required_status = ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value
    else:
        status = ScientificClaimStatus.PROVISIONAL.value
        reentry_required = True
        next_required_status = ScientificClaimStatus.REQUIRES_EXTERNAL_TRUTH.value

    return PenroseProofObligation(
        protocol=SCIENTIFIC_RIGOR_PROTOCOL,
        claim=claim,
        status=status,
        required_truth_condition="Exact local verification plus non-revoked external confirmation for external success claims.",
        evidence_ids=tuple(evidence_ids),
        falsification_route=(
            "Verifier failure, invalid-hash revocation, stale context without re-entry, external rejection, "
            "or missing replay seal prevents escalation."
        ),
        cannot_self_certify=True,
        claim_boundary="Penrose-style proof humility: PYTHIA may reason autonomously but cannot self-certify external truth.",
        session_event_id=session_event_id or str(evidence.get("session_event_id") or ""),
        reentry_required=reentry_required,
        revocation_reason=revocation_reason if revoked else "",
        revocation_disposition=disposition.value,
        revocation_classifier_source=classifier_source,
        next_required_status=next_required_status,
    )


def compute_causal_integration_telemetry(
    channels: Mapping[str, Any],
    floor_threshold: float = DEFAULT_CAUSAL_INTEGRATION_FLOOR,
    session_event_id: str = "",
) -> CausalIntegrationTelemetry:
    """Compute IIT-style evidence-channel integration telemetry."""

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
    scores: Dict[str, float] = {}
    sanitized = []
    for name in required:
        score, was_sanitized = _score(channels.get(name, 0.0))
        scores[name] = score
        if was_sanitized:
            sanitized.append(name)
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
        score_domain_policy="Channel inputs are mapped to [0,1]; negative, missing, error-like, or unrecognised values map to zero before floor scoring.",
        sanitized_channels=tuple(sanitized),
        session_event_id=session_event_id or str(channels.get("session_event_id") or ""),
    )


def _canonical_json(value: Any) -> str:
    """Serialize replay material in a stable, cross-run order."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def build_reproducibility_attestation(
    claim_id: str,
    inputs: Mapping[str, Any],
    commands: Sequence[str],
    seeds: Mapping[str, int] | None = None,
    dependency_pins: Mapping[str, str] | None = None,
    produced_artifacts: Sequence[str] = (),
    boundary: str = "Local deterministic replay only; not external validation or peer review.",
) -> ReproducibilityAttestation:
    """Build a deterministic local replay attestation for a bounded claim.

    A claim is considered locally reproducible only when it has a claim id,
    at least one replay command, a non-empty boundary, and all seed values are
    integers. The replay digest is derived solely from canonicalized inputs,
    commands, seeds, pins, and boundary text, so repeated calls with equivalent
    material produce byte-identical digests.
    """

    normalized_commands = tuple(
        str(command).strip() for command in commands if str(command).strip()
    )
    normalized_seeds = {str(key): int(value) for key, value in (seeds or {}).items()}
    normalized_pins = {str(key): str(value) for key, value in (dependency_pins or {}).items()}
    normalized_artifacts = tuple(
        str(path).strip() for path in produced_artifacts if str(path).strip()
    )
    input_payload = _canonical_json(inputs)
    input_digest = hashlib.sha256(input_payload.encode("utf-8")).hexdigest()
    replay_payload = {
        "boundary": str(boundary).strip(),
        "claim_id": str(claim_id).strip(),
        "commands": normalized_commands,
        "dependency_pins": normalized_pins,
        "input_digest": input_digest,
        "produced_artifacts": normalized_artifacts,
        "protocol": SCIENTIFIC_RIGOR_PROTOCOL,
        "seeds": normalized_seeds,
    }
    replay_digest = hashlib.sha256(_canonical_json(replay_payload).encode("utf-8")).hexdigest()
    reproducible = bool(
        replay_payload["claim_id"] and normalized_commands and replay_payload["boundary"]
    )
    return ReproducibilityAttestation(
        protocol=SCIENTIFIC_RIGOR_PROTOCOL,
        claim_id=replay_payload["claim_id"],
        commands=normalized_commands,
        produced_artifacts=normalized_artifacts,
        input_digest=input_digest,
        replay_digest=replay_digest,
        environment={
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
        },
        seeds=normalized_seeds,
        dependency_pins=normalized_pins,
        reproducible=reproducible,
        boundary=replay_payload["boundary"],
        falsification_route=(
            "Digest mismatch, missing replay command, changed seed/dependency pin, "
            "or boundary violation invalidates this local reproducibility attestation."
        ),
    )


__all__ = [
    "DEFAULT_CAUSAL_INTEGRATION_FLOOR",
    "SCIENTIFIC_RIGOR_PROTOCOL",
    "CausalIntegrationTelemetry",
    "PenroseProofObligation",
    "ReproducibilityAttestation",
    "RevocationDisposition",
    "ScientificClaimStatus",
    "assess_penrose_obligation",
    "build_reproducibility_attestation",
    "compute_causal_integration_telemetry",
]
