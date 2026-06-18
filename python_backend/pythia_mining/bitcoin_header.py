"""Bitcoin block header construction and SHA-256d hashing.

Converts a MiningJob + nonce into the canonical 80-byte header and returns the
hash as an integer (little-endian) for target comparison.
"""

from __future__ import annotations

import hashlib
import struct
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .stratum_client import MiningJob


def build_coinbase(job: "MiningJob", extranonce2: str) -> bytes:
    """Assemble coinbase transaction bytes from pool job fields."""
    coinbase1 = bytes.fromhex(job.coinbase_parts[0])
    en1 = bytes.fromhex(job.extranonce1)
    en2 = bytes.fromhex(extranonce2.zfill(job.extranonce2_size * 2))
    coinbase2 = bytes.fromhex(job.coinbase_parts[1])
    return coinbase1 + en1 + en2 + coinbase2


def coinbase_txid(coinbase: bytes) -> bytes:
    """Double-SHA256 of coinbase bytes → txid (32 bytes)."""
    return hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()


def merkle_root(coinbase_txid_bytes: bytes, branch: list[str]) -> bytes:
    """Compute merkle root by folding coinbase txid through merkle branch."""
    root = coinbase_txid_bytes
    for node_hex in branch:
        node = bytes.fromhex(node_hex)
        root = hashlib.sha256(
            hashlib.sha256(root + node).digest()
        ).digest()
    return root


def build_header(job: "MiningJob", nonce: int, extranonce2: str) -> bytes:
    """
    Construct the canonical 80-byte Bitcoin block header.

    Layout (all little-endian):
      version   (4 bytes)
      prevhash  (32 bytes, reversed)
      merkleroot(32 bytes)
      ntime     (4 bytes)
      nbits     (4 bytes)
      nonce     (4 bytes)
    """
    version = struct.pack("<I", int(job.version, 16))

    # prevhash: reverse byte order of each 4-byte word (stratum byte-reversal)
    prev_bytes = bytes.fromhex(job.prevhash)
    prevhash = b"".join(
        prev_bytes[i:i+4][::-1] for i in range(0, 32, 4)
    )

    coinbase = build_coinbase(job, extranonce2)
    txid = coinbase_txid(coinbase)
    mroot = merkle_root(txid, job.merkle_branch)

    ntime = struct.pack("<I", int(job.ntime, 16))
    nbits = struct.pack("<I", int(job.nbits, 16))
    nonce_bytes = struct.pack("<I", nonce)

    return version + prevhash + mroot + ntime + nbits + nonce_bytes


def sha256d_hash(header: bytes) -> int:
    """Return SHA-256d of header as integer (little-endian comparison)."""
    h1 = hashlib.sha256(header).digest()
    h2 = hashlib.sha256(h1).digest()
    return int.from_bytes(h2, "little")


def meets_target(job: "MiningJob", nonce: int, extranonce2: str) -> bool:
    """Return True if this nonce produces a hash below job.target."""
    header = build_header(job, nonce, extranonce2)
    return sha256d_hash(header) <= job.target
