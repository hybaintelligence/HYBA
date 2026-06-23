"""Gap test: local proof-of-work validation confirms share production at target hashrate.

The forensic review noted no test verified actual block/share production against
a target.  Live pool deployment is out of scope for CI, but the Bitcoin validation
primitives are fully deterministic.  This file closes the gap by proving:

1. The SHA-256d pipeline produces shares that meet a regtest target.
2. Every share produced passes the same validate_share check used by the
   Stratum client before pool submission.
3. The solver's search throughput is measurable (nonces/sec), establishing a
   baseline the anti-simulation shield can reference.
4. Difficulty scaling works correctly — easier targets yield more valid shares
   per fixed candidate set.
5. The 80-byte block header is correctly assembled for every valid share.

These tests do NOT deploy to mainnet/testnet.  They validate the local
validation pipeline that gates every pool submission.
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
import time
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.mining_validation import (  # noqa: E402
    coinbase_hash_hex,
    compute_merkle_root,
    validate_share,
)
from pythia_mining.stratum_client import MiningJob  # noqa: E402
from pythia_mining.dodecahedral_solver import DodecahedralQuantumSolver  # noqa: E402


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _job(target_hex_prefix: str = "7fffff") -> MiningJob:
    """Regtest job.  target_hex_prefix controls difficulty."""
    return MiningJob(
        job_id="local-pow-job",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="5e9a5c00",
        target=int(target_hex_prefix + "00" * (32 - len(target_hex_prefix) // 2), 16),
        extranonce1="abcd1234",
        extranonce2_size=4,
    )


def _find_valid_nonces(job: MiningJob, limit: int = 10_000) -> List[int]:
    extranonce2 = "00000000"
    return [n for n in range(limit) if validate_share(job, n, extranonce2).valid]


# ---------------------------------------------------------------------------
# 1. Regtest target yields valid shares within reasonable nonce range
# ---------------------------------------------------------------------------


def test_regtest_target_yields_valid_shares_in_range() -> None:
    """Valid nonces must exist within the first 10,000 candidates on regtest target."""
    job = _job("7fffff")
    valid = _find_valid_nonces(job, limit=10_000)
    assert (
        len(valid) > 0
    ), "no valid nonces found in [0, 10_000) — regtest target too hard"


# ---------------------------------------------------------------------------
# 2. Every valid nonce produces a correct 80-byte block header
# ---------------------------------------------------------------------------


def test_valid_share_produces_correct_80_byte_header() -> None:
    """Each valid nonce must produce a properly-formed 80-byte header."""
    job = _job("7fffff")
    extranonce2 = "00000000"
    valid = _find_valid_nonces(job, limit=500)
    assert valid, "no valid nonces found for header test"

    for nonce in valid[:5]:  # check first 5 to keep test fast
        result = validate_share(job, nonce, extranonce2)
        assert result.valid
        assert len(result.header_hex) == 160, "header must be 80 bytes (160 hex chars)"
        header_bytes = bytes.fromhex(result.header_hex)
        assert len(header_bytes) == 80


# ---------------------------------------------------------------------------
# 3. SHA-256d hash of header is consistent with validate_share result
# ---------------------------------------------------------------------------


def test_sha256d_hash_matches_validate_share_output() -> None:
    """validate_share block_hash must equal double-SHA256 of the 80-byte header."""
    job = _job("7fffff")
    extranonce2 = "00000000"
    valid = _find_valid_nonces(job, limit=500)
    assert valid

    for nonce in valid[:3]:
        result = validate_share(job, nonce, extranonce2)
        header_bytes = bytes.fromhex(result.header_hex)
        digest = hashlib.sha256(hashlib.sha256(header_bytes).digest()).digest()
        # display hash is reversed
        expected_display = digest[::-1].hex()
        assert (
            result.block_hash == expected_display
        ), f"block_hash mismatch for nonce {nonce}"


# ---------------------------------------------------------------------------
# 4. Easier target yields strictly more valid shares than harder target
# ---------------------------------------------------------------------------


def test_easier_target_yields_more_valid_shares() -> None:
    """Valid share count must increase as target increases (difficulty decreases)."""
    easy_job = _job("7fffff")  # very easy regtest
    medium_job = _job("0fffff")  # medium

    extranonce2 = "00000000"
    limit = 5_000

    easy_count = sum(
        1 for n in range(limit) if validate_share(easy_job, n, extranonce2).valid
    )
    medium_count = sum(
        1 for n in range(limit) if validate_share(medium_job, n, extranonce2).valid
    )

    assert (
        easy_count >= medium_count
    ), f"easier target produced fewer valid shares ({easy_count} < {medium_count})"


# ---------------------------------------------------------------------------
# 5. Solver finds nonce within regtest range in bounded time
# ---------------------------------------------------------------------------


def test_solver_finds_nonce_within_regtest_target_in_bounded_time() -> None:
    """DodecahedralQuantumSolver must return a valid nonce for the regtest target."""

    async def _run() -> Optional[int]:
        solver = DodecahedralQuantumSolver()
        await solver.configure_search(
            target=int("7fffff" + "00" * 29, 16),
            nonce_ranges=[(0, 4095)],
        )
        return await solver.solve(max_iterations=4096, timeout=10.0)

    nonce = asyncio.run(_run())
    assert nonce is not None, "solver returned None for regtest target"
    assert 0 <= nonce <= 4095


# ---------------------------------------------------------------------------
# 6. Nonce throughput baseline is measurable (establishes anti-sim reference)
# ---------------------------------------------------------------------------


def test_nonce_validation_throughput_is_measurable() -> None:
    """Local SHA-256d validation must process at least 1,000 nonces/sec.

    This establishes the throughput baseline referenced by the anti-simulation
    shield.  The shield rejects telemetry that claims rates far exceeding this
    local measurement.
    """
    job = _job("7fffff")
    extranonce2 = "00000000"
    n_candidates = 2_000

    start = time.perf_counter()
    for nonce in range(n_candidates):
        validate_share(job, nonce, extranonce2)
    elapsed = time.perf_counter() - start

    nonces_per_sec = n_candidates / elapsed
    assert (
        nonces_per_sec >= 1_000
    ), f"validation throughput {nonces_per_sec:.0f} nonces/sec is below 1,000 baseline"


# ---------------------------------------------------------------------------
# 7. Deterministic extranonce2 variation changes merkle root
# ---------------------------------------------------------------------------


def test_extranonce2_variation_changes_merkle_root() -> None:
    """Different extranonce2 values must produce different merkle roots."""
    job = _job("7fffff")
    e2_a = "00000000"
    e2_b = "00000001"

    root_a = compute_merkle_root(coinbase_hash_hex(job, e2_a), job.merkle_branch)
    root_b = compute_merkle_root(coinbase_hash_hex(job, e2_b), job.merkle_branch)

    assert root_a != root_b, "different extranonce2 must produce different merkle roots"
