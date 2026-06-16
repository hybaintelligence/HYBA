from __future__ import annotations

import pytest
from python_backend.pythia_mining.mining_validation import (
    MiningValidationError,
    build_block_header,
    coinbase_transaction_hex,
)
from python_backend.pythia_mining.stratum_client import MiningJob


def make_job() -> MiningJob:
    return MiningJob(
        job_id="job",
        prevhash="00" * 32,
        coinbase_parts=("aa", "bb"),
        merkle_branch=[],
        version="01000000",
        nbits="200fffff",
        ntime="5f5e1000",
        target=1,
        extranonce1="abcd",
        extranonce2_size=4,
        stratum_version=1,
    )


def test_coinbase_transaction_hex_raises_on_wrong_extranonce_length() -> None:
    job = make_job()
    # extranonce2 should be 8 hex chars (4 bytes)
    with pytest.raises(MiningValidationError):
        coinbase_transaction_hex(job, "000000")


def test_build_block_header_has_correct_length() -> None:
    job = make_job()
    merkle_root = "00" * 32
    header = build_block_header(job, merkle_root, nonce=0)
    assert isinstance(header, bytes)
    assert len(header) == 80


def test_build_block_header_raises_on_wrong_version_length() -> None:
    job = make_job()
    # Modify version to be too short (3 bytes instead of 4)
    job.version = "010000"
    merkle_root = "00" * 32
    with pytest.raises(MiningValidationError):
        build_block_header(job, merkle_root, nonce=0)
