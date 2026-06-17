"""Replayable sealed mining evidence schema for PYTHIA.

This module turns the policy phrase "replayable sealed evidence required" into a
concrete engineering constraint. A sealed bundle commits to the pool job context,
local verifier result, verifier-firewall decision, learning correction, pool
response, redacted runtime configuration hash, and curriculum/protocol tags.

The schema does not submit shares and does not mutate mining state. It exists so
PYTHIA can prove what happened after the fact without leaking credentials or
claiming success beyond the evidence.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from .mining_learning_signal import LEARNING_SIGNAL_PROTOCOL
from .mining_verification_firewall import VERIFICATION_FIREWALL_PROTOCOL, stable_hash
from .pythia_mining_pitfalls_curriculum import CURRICULUM_PROTOCOL

MINING_EVIDENCE_SEAL_PROTOCOL = "PYTHIA_MINING_EVIDENCE_SEAL_V1"


class EvidenceSealError(ValueError):
    """Raised when a sealed evidence bundle is incomplete or inconsistent."""


@dataclass(frozen=True)
class TimestampAuthority:
    """Timestamp authority for a sealed mining bundle.

    The default is local monotonic/wall-clock evidence. A future production
    adapter may add RFC3161, ledger, object-store, or notarisation proofs without
    changing the core bundle hash semantics.
    """

    authority: str = "local_system_clock"
    unix_seconds: float = field(default_factory=time.time)
    external_timestamp_token_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SealedMiningEvidenceBundle:
    """Canonical replay bundle for candidate/share/block evidence."""

    protocol: str
    mission_id: str
    event_type: str
    job_context: Mapping[str, Any]
    candidate: Mapping[str, Any]
    verifier_result: Mapping[str, Any]
    firewall_decision: Mapping[str, Any]
    learning_correction: Mapping[str, Any]
    pool_response: Mapping[str, Any]
    redacted_runtime_config_hash: str
    lesson_ids: List[str]
    timestamp_authority: Mapping[str, Any]
    prior_bundle_hash: Optional[str] = None
    bundle_hash: str = ""

    def unsigned_payload(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload.pop("bundle_hash", None)
        return payload

    def to_dict(self) -> Dict[str, Any]:
        payload = self.unsigned_payload()
        payload["bundle_hash"] = self.bundle_hash or stable_hash(payload)
        return payload


def redact_and_hash_runtime_config(config: Mapping[str, Any]) -> str:
    """Hash runtime config after dropping obvious secret-bearing values."""

    redacted: Dict[str, Any] = {}
    secret_terms = ("password", "secret", "token", "key", "wallet", "credential")
    for key, value in sorted(config.items(), key=lambda item: str(item[0])):
        key_text = str(key)
        if any(term in key_text.lower() for term in secret_terms):
            redacted[key_text] = "<redacted>"
        else:
            redacted[key_text] = value
    return stable_hash(redacted)


def build_sealed_mining_evidence_bundle(
    *,
    mission_id: str,
    event_type: str,
    job_context: Mapping[str, Any],
    candidate: Mapping[str, Any],
    verifier_result: Mapping[str, Any],
    firewall_decision: Mapping[str, Any],
    learning_correction: Mapping[str, Any],
    pool_response: Mapping[str, Any],
    runtime_config: Mapping[str, Any],
    lesson_ids: List[str],
    timestamp_authority: Optional[TimestampAuthority] = None,
    prior_bundle_hash: Optional[str] = None,
) -> SealedMiningEvidenceBundle:
    """Create a replayable sealed mining evidence bundle."""

    timestamp = timestamp_authority or TimestampAuthority()
    bundle = SealedMiningEvidenceBundle(
        protocol=MINING_EVIDENCE_SEAL_PROTOCOL,
        mission_id=mission_id,
        event_type=event_type,
        job_context=dict(job_context),
        candidate=dict(candidate),
        verifier_result=dict(verifier_result),
        firewall_decision=dict(firewall_decision),
        learning_correction=dict(learning_correction),
        pool_response=dict(pool_response),
        redacted_runtime_config_hash=redact_and_hash_runtime_config(runtime_config),
        lesson_ids=list(lesson_ids),
        timestamp_authority=timestamp.to_dict(),
        prior_bundle_hash=prior_bundle_hash,
    )
    sealed = SealedMiningEvidenceBundle(**{**bundle.unsigned_payload(), "bundle_hash": stable_hash(bundle.unsigned_payload())})
    validate_sealed_mining_evidence_bundle(sealed.to_dict())
    return sealed


def validate_sealed_mining_evidence_bundle(bundle: Mapping[str, Any]) -> bool:
    """Validate the sealed bundle schema and hash commitment."""

    required = (
        "protocol",
        "mission_id",
        "event_type",
        "job_context",
        "candidate",
        "verifier_result",
        "firewall_decision",
        "learning_correction",
        "pool_response",
        "redacted_runtime_config_hash",
        "lesson_ids",
        "timestamp_authority",
        "bundle_hash",
    )
    missing = [key for key in required if key not in bundle]
    if missing:
        raise EvidenceSealError(f"missing_fields:{','.join(missing)}")
    if bundle.get("protocol") != MINING_EVIDENCE_SEAL_PROTOCOL:
        raise EvidenceSealError("wrong_evidence_protocol")
    firewall = bundle.get("firewall_decision") or {}
    learning = bundle.get("learning_correction") or {}
    if firewall.get("protocol") != VERIFICATION_FIREWALL_PROTOCOL:
        raise EvidenceSealError("missing_verification_firewall_protocol")
    if learning.get("protocol") != LEARNING_SIGNAL_PROTOCOL:
        raise EvidenceSealError("missing_learning_signal_protocol")
    if not bundle.get("lesson_ids"):
        raise EvidenceSealError("missing_curriculum_lesson_ids")
    if not str(bundle.get("redacted_runtime_config_hash") or ""):
        raise EvidenceSealError("missing_redacted_runtime_config_hash")

    unsigned = dict(bundle)
    expected_hash = unsigned.pop("bundle_hash")
    if stable_hash(unsigned) != expected_hash:
        raise EvidenceSealError("bundle_hash_mismatch")
    return True


def seal_schema_summary() -> Dict[str, Any]:
    """Return schema summary for PYTHIA education/readiness checks."""

    return {
        "protocol": MINING_EVIDENCE_SEAL_PROTOCOL,
        "depends_on": [
            VERIFICATION_FIREWALL_PROTOCOL,
            LEARNING_SIGNAL_PROTOCOL,
            CURRICULUM_PROTOCOL,
        ],
        "required_bundle_parts": [
            "job_context",
            "candidate",
            "verifier_result",
            "firewall_decision",
            "learning_correction",
            "pool_response",
            "redacted_runtime_config_hash",
            "timestamp_authority",
            "bundle_hash",
        ],
        "success_boundary": "accepted shares are learning events; pool-confirmed accepted block is mission completion",
    }


__all__ = [
    "EvidenceSealError",
    "MINING_EVIDENCE_SEAL_PROTOCOL",
    "SealedMiningEvidenceBundle",
    "TimestampAuthority",
    "build_sealed_mining_evidence_bundle",
    "redact_and_hash_runtime_config",
    "seal_schema_summary",
    "validate_sealed_mining_evidence_bundle",
]
