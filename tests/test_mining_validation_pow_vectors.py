"""Deterministic proof-of-work vectors for mining validation primitives."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.mining_validation import (  # noqa: E402
    MiningValidationError,
    build_block_header,
    coinbase_hash_hex,
    compute_merkle_root,
    validate_share,
)
from pythia_mining.stratum_client import MiningJob  # noqa: E402

GENESIS_COINBASE_TX = (
    "01000000010000000000000000000000000000000000000000000000000000000000000000"
    "ffffffff4d04ffff001d0104455468652054696d65732030332f4a616e2f32303039204368616e"
    "63656c6c6f72206f6e206272696e6b206f66207365636f6e64206261696c6f757420666f7220"
    "62616e6b73ffffffff0100f2052a01000000434104678afdb0fe5548271967f1a67130b7105"
    "cd6a828e03909a67962e0ea1f61deb649f6bc3f4cef38c4f35504e51ec112de5c384df7ba0"
    "b8d578a4c702b6bf11d5fac00000000"
)
GENESIS_BLOCK_HASH = "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
GENESIS_MERKLE_ROOT = "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"
GENESIS_NONCE = 2_083_236_893
MAX_TARGET = int("00000000ffff" + "0" * 52, 16)


def genesis_job() -> MiningJob:
    """Return the Bitcoin genesis block as a Stratum-shaped local validation job."""
    return MiningJob(
        job_id="bitcoin-genesis",
        prevhash="00" * 32,
        coinbase_parts=(GENESIS_COINBASE_TX, ""),
        merkle_branch=[],
        version="00000001",
        nbits="1d00ffff",
        ntime="495fab29",
        target=MAX_TARGET,
        extranonce1="",
        extranonce2_size=0,
    )


def test_validate_share_accepts_bitcoin_genesis_pow_vector() -> None:
    """Known winning nonce must reproduce the canonical genesis block hash exactly."""
    result = validate_share(genesis_job(), GENESIS_NONCE, "")

    assert result.valid is True
    assert result.block_hash == GENESIS_BLOCK_HASH
    assert result.merkle_root == GENESIS_MERKLE_ROOT
    assert result.hash_int <= result.target
    assert len(bytes.fromhex(result.header_hex)) == 80


def test_validate_share_rejects_adjacent_wrong_nonce_against_same_target() -> None:
    """A one-off nonce must keep serialization stable while failing the target gate."""
    result = validate_share(genesis_job(), GENESIS_NONCE - 1, "")

    assert result.valid is False
    assert result.block_hash != GENESIS_BLOCK_HASH
    assert result.hash_int > result.target
    assert result.reason == "hash_above_target"


def test_genesis_merkle_and_header_serialization_are_canonical() -> None:
    """Coinbase hashing, merkle construction, and 80-byte header assembly are byte-exact."""
    job = genesis_job()
    coinbase_hash = coinbase_hash_hex(job, "")
    merkle_root = compute_merkle_root(coinbase_hash, job.merkle_branch)
    header = build_block_header(job, merkle_root, GENESIS_NONCE)

    assert merkle_root == GENESIS_MERKLE_ROOT
    assert header.hex() == (
        "01000000"
        "0000000000000000000000000000000000000000000000000000000000000000"
        "3ba3edfd7a7b12b27ac72c3e67768f617fc81bc3888a51323a9fb8aa4b1e5e4a"
        "29ab5f49"
        "ffff001d"
        "1dac2b7c"
    )


def test_validate_share_rejects_malformed_extranonce_before_hashing() -> None:
    """Malformed extranonce data must raise a deterministic validation error, not return a stub result."""
    with pytest.raises(MiningValidationError, match="extranonce2"):
        validate_share(genesis_job(), GENESIS_NONCE, "00")
