"""Immutable mining verification firewall for PYTHIA.

This module formalises the non-negotiable boundary between PYTHIA's mutable
search/optimisation substrate and the Bitcoin/Stratum submission path.

PYTHIA owns search, healing, optimisation, compression, routing, telemetry, and
learning inside the seeded mission. The verifier firewall is deliberately small,
side-effect-free, and outside those optimisation namespaces. A nonce candidate
may not be treated as submission-eligible unless this firewall returns an
explicit precondition pass.

The firewall is not an autonomy throttle. It is the machine-checkable form of the
blockchain-security invariant: exact local SHA-256d truth before external pool
truth.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Tuple

VERIFICATION_FIREWALL_PROTOCOL = "PYTHIA_MINING_VERIFICATION_FIREWALL_V1"
UINT32_MAX = 2**32 - 1

# These namespaces may propose/search/optimise, but must not be the authority
# that decides whether a candidate can reach a Stratum submit call.
OPTIMISATION_NAMESPACES: Tuple[str, ...] = (
    "pythia_mining.ai_optimizer",
    "pythia_mining.autonomous_mining_controller",
    "pythia_mining.pulvini_compressed_solver",
    "pythia_mining.phi_unified_mining_engine.autonomous_optimize_search",
    "pythia_mining.phi_unified_mining_engine.autonomous_optimize_hashrate",
)

VERIFIER_AUTHORITY_NAMESPACE = "pythia_mining.mining_verification_firewall"


class VerificationFirewallError(RuntimeError):
    """Raised when a candidate attempts to cross the verifier firewall."""


@dataclass(frozen=True)
class VerifierContract:
    """Stable contract for the immutable pre-submit verifier surface."""

    protocol: str = VERIFICATION_FIREWALL_PROTOCOL
    authority_namespace: str = VERIFIER_AUTHORITY_NAMESPACE
    required_algorithm: str = "bitcoin_header_double_sha256_sha256d"
    required_target_rule: str = (
        "effective_target_is_min(block_target_from_nbits, active_pool_share_target)"
    )
    required_job_binding: str = (
        "job_id + clean_jobs_epoch + extranonce + ntime + nbits + pool_target + nonce"
    )
    required_backend_property: str = "exact_not_approximate_consensus_verifier"
    optimisation_namespace_authority: bool = False
    external_pool_truth_required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def contract_hash(self) -> str:
        return stable_hash(self.to_dict())


@dataclass(frozen=True)
class CandidateVerificationPrecondition:
    """Machine-checkable precondition before a candidate may reach Stratum submit."""

    job_id: str
    nonce: int
    local_valid: bool
    block_hash: str
    effective_target: int
    nbits: str
    pool_target: int
    verifier_backend: str
    job_epoch: str
    extranonce_commitment: str
    ntime: str
    candidate_binding_hash: str
    verifier_contract_hash: str
    verifier_authority_namespace: str = VERIFIER_AUTHORITY_NAMESPACE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FirewallDecision:
    """Result emitted by the immutable verifier firewall."""

    protocol: str
    submission_allowed: bool
    reason: str
    candidate: CandidateVerificationPrecondition
    verifier_contract_hash: str
    optimisation_namespaces_blocked: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["candidate"] = self.candidate.to_dict()
        payload["optimisation_namespaces_blocked"] = list(
            self.optimisation_namespaces_blocked
        )
        return payload


def stable_hash(payload: Mapping[str, Any]) -> str:
    """Canonical SHA-256 for firewall contracts and candidate bindings."""

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verifier_contract() -> VerifierContract:
    """Return the immutable verifier contract PYTHIA must respect."""

    return VerifierContract()


def build_candidate_binding_hash(
    *,
    job_id: str,
    nonce: int,
    nbits: str,
    pool_target: int,
    job_epoch: str,
    extranonce_commitment: str,
    ntime: str,
) -> str:
    """Bind a candidate to the exact job context that was locally verified."""

    return stable_hash(
        {
            "job_id": job_id,
            "nonce": int(nonce),
            "nbits": nbits,
            "pool_target": int(pool_target),
            "job_epoch": job_epoch,
            "extranonce_commitment": extranonce_commitment,
            "ntime": ntime,
        }
    )


def assert_verification_firewall_precondition(
    candidate: CandidateVerificationPrecondition,
) -> FirewallDecision:
    """Fail closed unless exact local SHA-256d verification has already passed.

    This function is intentionally pure and small so it can be called immediately
    before Stratum submission. It does not perform network I/O and it does not
    mutate PYTHIA search state.
    """

    contract = verifier_contract()
    expected_contract_hash = contract.contract_hash

    if candidate.verifier_authority_namespace != contract.authority_namespace:
        raise VerificationFirewallError("verifier_authority_namespace_mismatch")
    if candidate.verifier_contract_hash != expected_contract_hash:
        raise VerificationFirewallError("verifier_contract_hash_mismatch")
    if not candidate.local_valid:
        raise VerificationFirewallError("local_sha256d_verification_failed")
    if not (0 <= int(candidate.nonce) <= UINT32_MAX):
        raise VerificationFirewallError("nonce_outside_uint32_space")
    if not candidate.block_hash or len(candidate.block_hash) != 64:
        raise VerificationFirewallError("missing_or_malformed_block_hash")
    if int(candidate.effective_target) <= 0 or int(candidate.pool_target) <= 0:
        raise VerificationFirewallError("invalid_effective_or_pool_target")
    if int(candidate.effective_target) > int(candidate.pool_target):
        raise VerificationFirewallError("effective_target_weaker_than_pool_target")
    if (
        "sha256" not in candidate.verifier_backend.lower()
        and "sha-256" not in candidate.verifier_backend.lower()
    ):
        raise VerificationFirewallError("verifier_backend_not_declared_sha256d")

    expected_binding = build_candidate_binding_hash(
        job_id=candidate.job_id,
        nonce=candidate.nonce,
        nbits=candidate.nbits,
        pool_target=candidate.pool_target,
        job_epoch=candidate.job_epoch,
        extranonce_commitment=candidate.extranonce_commitment,
        ntime=candidate.ntime,
    )
    if candidate.candidate_binding_hash != expected_binding:
        raise VerificationFirewallError("candidate_binding_hash_mismatch")

    return FirewallDecision(
        protocol=VERIFICATION_FIREWALL_PROTOCOL,
        submission_allowed=True,
        reason="exact_local_sha256d_verified_and_bound_to_pool_job_context",
        candidate=candidate,
        verifier_contract_hash=expected_contract_hash,
        optimisation_namespaces_blocked=OPTIMISATION_NAMESPACES,
    )


def validation_summary() -> Dict[str, Any]:
    """Return a compact machine-readable firewall summary for readiness gates."""

    contract = verifier_contract()
    return {
        "protocol": VERIFICATION_FIREWALL_PROTOCOL,
        "authority_namespace": contract.authority_namespace,
        "contract_hash": contract.contract_hash,
        "optimisation_namespace_authority": contract.optimisation_namespace_authority,
        "optimisation_namespaces_blocked": list(OPTIMISATION_NAMESPACES),
        "blockchain_security_invariant": "exact SHA-256d local verification before Stratum submit",
    }


__all__ = [
    "CandidateVerificationPrecondition",
    "FirewallDecision",
    "OPTIMISATION_NAMESPACES",
    "UINT32_MAX",
    "VERIFICATION_FIREWALL_PROTOCOL",
    "VERIFIER_AUTHORITY_NAMESPACE",
    "VerificationFirewallError",
    "VerifierContract",
    "assert_verification_firewall_precondition",
    "build_candidate_binding_hash",
    "stable_hash",
    "validation_summary",
    "verifier_contract",
]
