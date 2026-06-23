from __future__ import annotations

import pytest

from pythia_mining.mining_verification_firewall import (
    CandidateVerificationPrecondition,
    OPTIMISATION_NAMESPACES,
    VERIFICATION_FIREWALL_PROTOCOL,
    VERIFIER_AUTHORITY_NAMESPACE,
    VerificationFirewallError,
    assert_verification_firewall_precondition,
    build_candidate_binding_hash,
    validation_summary,
    verifier_contract,
)


def _candidate(**overrides: object) -> CandidateVerificationPrecondition:
    contract = verifier_contract()
    binding = build_candidate_binding_hash(
        job_id="job-1",
        nonce=42,
        nbits="1d00ffff",
        pool_target=1000,
        job_epoch="epoch-1",
        extranonce_commitment="sha256:extranonce",
        ntime="5f5e100",
    )
    payload = {
        "job_id": "job-1",
        "nonce": 42,
        "local_valid": True,
        "block_hash": "0" * 64,
        "effective_target": 500,
        "nbits": "1d00ffff",
        "pool_target": 1000,
        "verifier_backend": "cpu_parallel_exact_sha256d",
        "job_epoch": "epoch-1",
        "extranonce_commitment": "sha256:extranonce",
        "ntime": "5f5e100",
        "candidate_binding_hash": binding,
        "verifier_contract_hash": contract.contract_hash,
        "verifier_authority_namespace": VERIFIER_AUTHORITY_NAMESPACE,
    }
    payload.update(overrides)
    return CandidateVerificationPrecondition(**payload)


def test_verification_firewall_allows_only_exact_locally_verified_candidate() -> None:
    decision = assert_verification_firewall_precondition(_candidate())

    assert decision.protocol == VERIFICATION_FIREWALL_PROTOCOL
    assert decision.submission_allowed is True
    assert (
        decision.reason == "exact_local_sha256d_verified_and_bound_to_pool_job_context"
    )
    assert decision.optimisation_namespaces_blocked == OPTIMISATION_NAMESPACES


def test_verification_firewall_fails_closed_on_local_invalid_candidate() -> None:
    with pytest.raises(
        VerificationFirewallError, match="local_sha256d_verification_failed"
    ):
        assert_verification_firewall_precondition(_candidate(local_valid=False))


def test_verification_firewall_rejects_weaker_effective_target_than_pool_target() -> (
    None
):
    with pytest.raises(
        VerificationFirewallError, match="effective_target_weaker_than_pool_target"
    ):
        assert_verification_firewall_precondition(_candidate(effective_target=1001))


def test_verification_firewall_rejects_binding_mismatch() -> None:
    with pytest.raises(
        VerificationFirewallError, match="candidate_binding_hash_mismatch"
    ):
        assert_verification_firewall_precondition(
            _candidate(candidate_binding_hash="bad")
        )


def test_verification_firewall_is_outside_optimisation_authority() -> None:
    summary = validation_summary()

    assert summary["authority_namespace"] == VERIFIER_AUTHORITY_NAMESPACE
    assert summary["optimisation_namespace_authority"] is False
    assert "pythia_mining.ai_optimizer" in summary["optimisation_namespaces_blocked"]
    assert (
        "exact SHA-256d local verification before Stratum submit"
        in summary["blockchain_security_invariant"]
    )
