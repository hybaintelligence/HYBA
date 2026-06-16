from __future__ import annotations

import pytest
from python_backend.pythia_mining.mining_validation import (
    MiningValidationError,
    compact_to_target,
    effective_target,
)
from python_backend.pythia_mining.stratum_client import MiningJob


def make_job(target: int, nbits: str) -> MiningJob:
    return MiningJob(
        job_id="job",
        prevhash="00" * 32,
        coinbase_parts=("aa", "bb"),
        merkle_branch=[],
        version="01000000",
        nbits=nbits,
        ntime="5f5e1000",
        target=target,
        extranonce1="abcd",
        extranonce2_size=4,
        stratum_version=1,
    )


def test_compact_to_target_valid_exponent_mantissa() -> None:
    # Exponent=4, mantissa non-zero -> valid target
    nbits = "04010203"
    target = compact_to_target(nbits)
    assert isinstance(target, int)
    assert target > 0


def test_compact_to_target_raises_on_invalid_negative_bit() -> None:
    # Negative bit set (0x00800000) triggers a validation error
    nbits = "21800000"  # exponent=0x21, mantissa with negative flag
    with pytest.raises(MiningValidationError):
        compact_to_target(nbits)


def test_compact_to_target_raises_on_zero_mantissa() -> None:
    # Mantissa = 0 is invalid
    nbits = "21000000"
    with pytest.raises(MiningValidationError):
        compact_to_target(nbits)


def test_effective_target_uses_minimum() -> None:
    job = make_job(1000, "200fffff")
    result = effective_target(job)
    from python_backend.pythia_mining.mining_validation import compact_to_target

    compact_target = compact_to_target("200fffff")
    assert result == min(1000, compact_target)


def test_effective_target_raises_on_non_positive_target() -> None:
    job = make_job(0, "200fffff")
    with pytest.raises(MiningValidationError):
        effective_target(job)
