"""Runtime integration between Stratum submission and the verifier firewall.

This module is the seam between the formal verification contract and the live
submission method. It preserves PYTHIA's search autonomy while ensuring every
candidate crossing into Stratum submission has already passed the immutable
firewall precondition.
"""

from __future__ import annotations

import functools
from typing import Any, Optional

from .mining_verification_firewall import (
    CandidateVerificationPrecondition,
    VerificationFirewallError,
    assert_verification_firewall_precondition,
    build_candidate_binding_hash,
    stable_hash,
    verifier_contract,
)

PATCH_MARKER = "_pythia_verification_firewall_installed"
ORIGINAL_MARKER = "_pythia_original_submit_validated_share"
VERIFIER_BACKEND = "pythia_mining.mining_validation.validate_share.exact_sha256d"


class StratumSubmissionFirewallError(RuntimeError):
    """Raised when the Stratum submit path cannot be firewall protected."""


def build_stratum_firewall_precondition(
    job: Any, nonce: int, extranonce2: Optional[str] = None
) -> CandidateVerificationPrecondition:
    """Validate and bind a Stratum candidate immediately before submission."""

    from .mining_validation import validate_share

    extranonce2_value = extranonce2 or ("00" * int(getattr(job, "extranonce2_size", 4)))
    validation = validate_share(job, int(nonce), extranonce2_value)
    contract = verifier_contract()
    job_epoch = stable_hash(
        {
            "job_id": getattr(job, "job_id", ""),
            "received_timestamp": getattr(job, "received_timestamp", None),
            "stratum_version": getattr(job, "stratum_version", None),
            "is_stale": getattr(job, "is_stale", None),
        }
    )
    extranonce_commitment = stable_hash(
        {
            "extranonce1": getattr(job, "extranonce1", ""),
            "extranonce2": extranonce2_value,
            "extranonce2_size": getattr(job, "extranonce2_size", None),
        }
    )
    binding = build_candidate_binding_hash(
        job_id=getattr(job, "job_id", ""),
        nonce=int(nonce),
        nbits=getattr(job, "nbits", ""),
        pool_target=int(getattr(job, "target", 0)),
        job_epoch=job_epoch,
        extranonce_commitment=extranonce_commitment,
        ntime=getattr(job, "ntime", ""),
    )
    return CandidateVerificationPrecondition(
        job_id=getattr(job, "job_id", ""),
        nonce=int(nonce),
        local_valid=bool(validation.valid),
        block_hash=validation.block_hash,
        effective_target=int(validation.target),
        nbits=getattr(job, "nbits", ""),
        pool_target=int(getattr(job, "target", 0)),
        verifier_backend=VERIFIER_BACKEND,
        job_epoch=job_epoch,
        extranonce_commitment=extranonce_commitment,
        ntime=getattr(job, "ntime", ""),
        candidate_binding_hash=binding,
        verifier_contract_hash=contract.contract_hash,
    )


def assert_stratum_submission_firewall(
    job: Any, nonce: int, extranonce2: Optional[str] = None
) -> dict:
    """Return the firewall decision dict or raise before Stratum submission."""

    precondition = build_stratum_firewall_precondition(job, nonce, extranonce2)
    return assert_verification_firewall_precondition(precondition).to_dict()


def verify_stratum_firewall_integrity() -> bool:
    """Verify that the Stratum submission firewall is currently installed.

    Returns True when the firewall wrapper is the active submit method, False
    if the original unwrapped method is in place or the method has been
    replaced. This check should be called after installation and as part of
    production readiness gates.
    """

    from .stratum_client import StratumClient

    submit_method = getattr(StratumClient, "submit_validated_share", None)
    if submit_method is None:
        return False
    return bool(getattr(submit_method, PATCH_MARKER, False))


def install_stratum_submit_firewall() -> bool:
    """Wrap ``StratumClient.submit_validated_share`` with the verifier firewall.

    Returns True when the wrapper is installed and False when it was already
    present. The wrapper fails closed by returning a rejected ``ShareResult`` and
    never calling the original submit method if the firewall raises.

    Post-install integrity is verified immediately; a mismatch raises
    ``StratumSubmissionFirewallError`` so production mode cannot continue with
    an unwrapped or tampered submit path.
    """

    from .mining_validation import MiningValidationError
    from .stratum_client import ShareResult, StratumClient

    if getattr(StratumClient.submit_validated_share, PATCH_MARKER, False):
        return False

    original = StratumClient.submit_validated_share

    @functools.wraps(original)
    async def guarded_submit(
        self: Any, job: Any, nonce: int, extranonce2: Optional[str] = None
    ) -> ShareResult:
        # Pre-submit integrity assertion: if this wrapper has been replaced
        # at runtime by a monkey-patch, mock leak, or dynamic reassignment,
        # refuse to submit rather than silently bypass the firewall.
        if not verify_stratum_firewall_integrity():
            reason = "stratum_firewall_integrity_check_failed"
            try:
                self.shares_submitted += 1
                self.shares_rejected += 1
                self.last_share_error = reason
                self.metrics_store.record_share_submission(
                    pool_name=self.pool_name,
                    pool_url=self.pool_url,
                    job_id=getattr(job, "job_id", ""),
                    nonce=int(nonce),
                    accepted=False,
                    error_code=428,
                    error_message=reason,
                )
                await self._persist_metrics()
            except Exception:
                pass
            return ShareResult(
                False, 428, reason, getattr(job, "job_id", ""), int(nonce)
            )

        try:
            decision = assert_stratum_submission_firewall(job, nonce, extranonce2)
        except (MiningValidationError, VerificationFirewallError, ValueError) as exc:
            reason = f"verification_firewall_blocked:{exc}"
            try:
                self.shares_submitted += 1
                self.shares_rejected += 1
                self.last_share_error = reason
                self.metrics_store.record_share_submission(
                    pool_name=self.pool_name,
                    pool_url=self.pool_url,
                    job_id=getattr(job, "job_id", ""),
                    nonce=int(nonce),
                    accepted=False,
                    error_code=428,
                    error_message=reason,
                )
                await self._persist_metrics()
            except Exception:
                pass
            return ShareResult(
                False, 428, reason, getattr(job, "job_id", ""), int(nonce)
            )

        self.last_verification_firewall_decision = decision
        # Pass _firewall_validated=True to eliminate the redundant second
        # validate_share call. The firewall is the sole pre-submit oracle for
        # local SHA-256d verification; the original method must trust this
        # result rather than re-validating against the same job state.
        return await original(self, job, nonce, extranonce2, _firewall_validated=True)

    setattr(guarded_submit, PATCH_MARKER, True)
    setattr(guarded_submit, ORIGINAL_MARKER, original)
    StratumClient.submit_validated_share = guarded_submit

    if not verify_stratum_firewall_integrity():
        raise StratumSubmissionFirewallError(
            "post_install_firewall_integrity_check_failed: submit_validated_share is not wrapped"
        )
    return True


__all__ = [
    "PATCH_MARKER",
    "ORIGINAL_MARKER",
    "StratumSubmissionFirewallError",
    "VERIFIER_BACKEND",
    "assert_stratum_submission_firewall",
    "build_stratum_firewall_precondition",
    "install_stratum_submit_firewall",
    "verify_stratum_firewall_integrity",
]
