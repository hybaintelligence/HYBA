"""Replayable sealed mining evidence schema for PYTHIA.

This module turns the policy phrase "replayable sealed evidence required" into a
concrete engineering constraint. A sealed bundle commits to the pool job context,
local verifier result, verifier-firewall decision, learning correction, pool
response, redacted runtime configuration hash, curriculum/protocol tags, a shared
session event id, and a Bitcoin job anchor.

The schema does not submit shares and does not mutate mining state. It exists so
PYTHIA can prove what happened after the fact without leaking private runtime
values or claiming success beyond the evidence.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from .mining_learning_signal import LEARNING_SIGNAL_PROTOCOL
from .mining_verification_firewall import VERIFICATION_FIREWALL_PROTOCOL, stable_hash
from .pythia_mining_pitfalls_curriculum import CURRICULUM_PROTOCOL

MINING_EVIDENCE_SEAL_PROTOCOL = "PYTHIA_MINING_EVIDENCE_SEAL_V2"
TIMESTAMP_AUTHORITY = "bitcoin_job_anchor"


class EvidenceSealError(ValueError):
    """Raised when a sealed evidence bundle is incomplete or inconsistent."""


@dataclass(frozen=True)
class TimestampAuthority:
    """Externally anchored timestamp authority for a sealed mining bundle.

    The authority is the Bitcoin job context, not PYTHIA's local clock. Local
    wall-clock time is retained only as auxiliary evidence; the replay anchor is
    ``bitcoin_block_height + stratum_job_id + prevhash``.

    ``chain_validity_at_seal`` records whether the anchored ``job_prevhash``
    matched the canonical chain tip at seal time. Under a shallow reorg the
    prevhash at height ``h`` can change, turning a previously-canonical anchor
    into an orphaned-branch record. This field makes the chain context
    machine-readable without invalidating historical bundles.
    """

    authority: str = TIMESTAMP_AUTHORITY
    bitcoin_block_height: int = 0
    stratum_job_id: str = ""
    job_prevhash: str = ""
    unix_seconds: float = field(default_factory=time.time)
    anchor_hash: str = ""
    external_timestamp_token_hash: Optional[str] = None
    chain_validity_at_seal: str = "canonical"

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        if not payload["anchor_hash"]:
            payload["anchor_hash"] = stable_hash(
                {
                    "authority": payload["authority"],
                    "bitcoin_block_height": payload["bitcoin_block_height"],
                    "stratum_job_id": payload["stratum_job_id"],
                    "job_prevhash": payload["job_prevhash"],
                }
            )
        return payload


@dataclass(frozen=True)
class SealedMiningEvidenceBundle:
    """Canonical replay bundle for candidate/share/block evidence."""

    protocol: str
    mission_id: str
    session_event_id: str
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
    """Hash runtime config after dropping private-bearing values."""

    redacted: Dict[str, Any] = {}
    private_terms = ("password", "secret", "token", "key", "wallet", "credential")
    for key, value in sorted(config.items(), key=lambda item: str(item[0])):
        key_text = str(key)
        if any(term in key_text.lower() for term in private_terms):
            redacted[key_text] = "<redacted>"
        else:
            redacted[key_text] = value
    return stable_hash(redacted)


def _check_chain_validity(prevhash: str, block_height: int) -> str:
    """Check whether a job prevhash is still anchored to the canonical chain tip.

    Returns ``canonical`` when the prevhash matches the current tip at the same
    height, and ``orphan_risk`` when it does not match (shallow reorg or tip
    change). Failures to reach the chain oracle are recorded as ``unverified``
    so the seal is not incorrectly flagged canonical without evidence.
    """

    try:
        from .blockchain_oracle import BlockchainOracle

        oracle = BlockchainOracle()
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            tip = asyncio.run(oracle.get_current_block_tip(force_refresh=True))
        else:
            tip = loop.run_until_complete(oracle.get_current_block_tip(force_refresh=True))
        if tip is None:
            return "unverified"
        if tip.hash.lower() == prevhash.lower():
            return "canonical"
        return "orphan_risk"
    except Exception:
        return "unverified"


def bitcoin_job_timestamp_authority(job_context: Mapping[str, Any], *, unix_seconds: Optional[float] = None) -> TimestampAuthority:
    """Build the minimum viable external timestamp anchor from Bitcoin job context."""

    job_id = str(job_context.get("job_id") or job_context.get("stratum_job_id") or "")
    prevhash = str(job_context.get("prevhash") or job_context.get("job_prevhash") or "")
    block_height = job_context.get("bitcoin_block_height", job_context.get("block_height", job_context.get("height", 0)))
    try:
        height_int = int(block_height)
    except (TypeError, ValueError):
        raise EvidenceSealError("invalid_bitcoin_block_height")
    if not job_id:
        raise EvidenceSealError("missing_stratum_job_id_anchor")
    if height_int <= 0:
        raise EvidenceSealError("missing_bitcoin_block_height_anchor")
    if not prevhash:
        raise EvidenceSealError("missing_prevhash_anchor")
    anchor_payload = {
        "authority": TIMESTAMP_AUTHORITY,
        "bitcoin_block_height": height_int,
        "stratum_job_id": job_id,
        "job_prevhash": prevhash,
    }
    chain_validity = _check_chain_validity(prevhash, height_int)
    return TimestampAuthority(
        authority=TIMESTAMP_AUTHORITY,
        bitcoin_block_height=height_int,
        stratum_job_id=job_id,
        job_prevhash=prevhash,
        unix_seconds=time.time() if unix_seconds is None else float(unix_seconds),
        anchor_hash=stable_hash(anchor_payload),
        chain_validity_at_seal=chain_validity,
    )


def derive_session_event_id(
    *,
    mission_id: str,
    event_type: str,
    job_context: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> str:
    """Derive a deterministic join key for all artefacts in a candidate lifecycle."""

    job_id = str(job_context.get("job_id") or job_context.get("stratum_job_id") or "")
    height = job_context.get("bitcoin_block_height", job_context.get("block_height", job_context.get("height", 0)))
    prevhash = str(job_context.get("prevhash") or job_context.get("job_prevhash") or "")
    nonce = str(candidate.get("nonce", candidate.get("nonce_hex", candidate.get("candidate_nonce", ""))))
    candidate_id = str(candidate.get("candidate_id") or candidate.get("id") or "")
    payload = {
        "mission_id": mission_id,
        "event_type": event_type,
        "job_id": job_id,
        "bitcoin_block_height": height,
        "job_prevhash": prevhash,
        "candidate_id": candidate_id,
        "nonce": nonce,
    }
    return stable_hash(payload)


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
    session_event_id: Optional[str] = None,
) -> SealedMiningEvidenceBundle:
    """Create a replayable sealed mining evidence bundle."""

    timestamp = timestamp_authority or bitcoin_job_timestamp_authority(job_context)
    event_id = session_event_id or derive_session_event_id(
        mission_id=mission_id,
        event_type=event_type,
        job_context=job_context,
        candidate=candidate,
    )
    bundle = SealedMiningEvidenceBundle(
        protocol=MINING_EVIDENCE_SEAL_PROTOCOL,
        mission_id=mission_id,
        session_event_id=event_id,
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


def _validate_nested_session_event_id(bundle: Mapping[str, Any], key: str, expected: str) -> None:
    payload = bundle.get(key) or {}
    if isinstance(payload, Mapping):
        nested = str(payload.get("session_event_id") or "")
        if nested and nested != expected:
            raise EvidenceSealError(f"session_event_id_mismatch:{key}")


def validate_sealed_mining_evidence_bundle(bundle: Mapping[str, Any]) -> bool:
    """Validate the sealed bundle schema and hash commitment."""

    required = (
        "protocol",
        "mission_id",
        "session_event_id",
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
    session_event_id = str(bundle.get("session_event_id") or "")
    if not session_event_id:
        raise EvidenceSealError("missing_session_event_id")
    for nested_key in ("verifier_result", "firewall_decision", "learning_correction", "pool_response"):
        _validate_nested_session_event_id(bundle, nested_key, session_event_id)

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

    job_context = bundle.get("job_context") or {}
    timestamp = bundle.get("timestamp_authority") or {}
    if timestamp.get("authority") != TIMESTAMP_AUTHORITY:
        raise EvidenceSealError("timestamp_authority_not_bitcoin_anchored")
    if str(timestamp.get("stratum_job_id")) != str(job_context.get("job_id") or job_context.get("stratum_job_id") or ""):
        raise EvidenceSealError("timestamp_job_id_anchor_mismatch")
    if int(timestamp.get("bitcoin_block_height") or 0) <= 0:
        raise EvidenceSealError("timestamp_missing_bitcoin_block_height")
    if not str(timestamp.get("job_prevhash") or ""):
        raise EvidenceSealError("timestamp_missing_prevhash")
    if not str(timestamp.get("chain_validity_at_seal") or ""):
        raise EvidenceSealError("timestamp_missing_chain_validity_at_seal")
    expected_anchor = stable_hash(
        {
            "authority": TIMESTAMP_AUTHORITY,
            "bitcoin_block_height": int(timestamp.get("bitcoin_block_height")),
            "stratum_job_id": str(timestamp.get("stratum_job_id")),
            "job_prevhash": str(timestamp.get("job_prevhash")),
        }
    )
    if timestamp.get("anchor_hash") != expected_anchor:
        raise EvidenceSealError("timestamp_anchor_hash_mismatch")

    unsigned = dict(bundle)
    expected_hash = unsigned.pop("bundle_hash")
    if stable_hash(unsigned) != expected_hash:
        raise EvidenceSealError("bundle_hash_mismatch")
    return True


def seal_schema_summary() -> Dict[str, Any]:
    """Return schema summary for PYTHIA education/readiness checks."""

    return {
        "protocol": MINING_EVIDENCE_SEAL_PROTOCOL,
        "timestamp_authority": TIMESTAMP_AUTHORITY,
        "depends_on": [
            VERIFICATION_FIREWALL_PROTOCOL,
            LEARNING_SIGNAL_PROTOCOL,
            CURRICULUM_PROTOCOL,
        ],
        "required_bundle_parts": [
            "session_event_id",
            "job_context",
            "candidate",
            "verifier_result",
            "firewall_decision",
            "learning_correction",
            "pool_response",
            "redacted_runtime_config_hash",
            "timestamp_authority",
            "bitcoin_block_height",
            "stratum_job_id",
            "job_prevhash",
            "chain_validity_at_seal",
            "bundle_hash",
        ],
        "success_boundary": "accepted shares are learning events; pool-confirmed accepted block is mission completion",
    }


__all__ = [
    "EvidenceSealError",
    "MINING_EVIDENCE_SEAL_PROTOCOL",
    "TIMESTAMP_AUTHORITY",
    "SealedMiningEvidenceBundle",
    "TimestampAuthority",
    "bitcoin_job_timestamp_authority",
    "build_sealed_mining_evidence_bundle",
    "derive_session_event_id",
    "redact_and_hash_runtime_config",
    "seal_schema_summary",
    "validate_sealed_mining_evidence_bundle",
]