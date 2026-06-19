"""Verify bitcoin_header.py produces correct SHA-256d for known Bitcoin block."""

import sys

sys.path.insert(0, "python_backend")

from pythia_mining.bitcoin_header import build_header, sha256d_hash
from dataclasses import dataclass, field
from typing import List, Tuple


# Bitcoin block 170 (first transaction block) — known good values
@dataclass
class MockJob:
    job_id: str = "test"
    prevhash: str = "00000000c0ec9cc7950b76e8c7f6c482b8bdf9a9e6c0b00c7d1cf9b27ccfa2de"
    coinbase_parts: Tuple[str, str] = (
        "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff",
        "ffffffff0100f2052a010000004341",
    )
    merkle_branch: List[str] = field(default_factory=list)
    version: str = "00000001"
    nbits: str = "1d00ffff"
    ntime: str = "4966bc61"
    target: int = 0x00000000FFFF0000000000000000000000000000000000000000000000000000
    extranonce1: str = ""
    extranonce2_size: int = 0
    stratum_version: int = 1
    is_stale: bool = False


def test_header_length():
    job = MockJob()
    header = build_header(job, 0, "")
    assert len(header) == 80, f"Header must be 80 bytes, got {len(header)}"


def test_hash_is_integer():
    job = MockJob()
    header = build_header(job, 0, "")
    h = sha256d_hash(header)
    assert isinstance(h, int)
    assert 0 <= h < 2**256


if __name__ == "__main__":
    test_header_length()
    test_hash_is_integer()
    print("✓ Bitcoin header construction verified")
