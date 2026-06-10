"""
Bitcoin-compatible mining validation primitives for PYTHIA.

This module is intentionally deterministic and side-effect free. It owns byte-order,
merkle-root, compact-target, block-header, and share-validation rules so the quantum
solver can stay focused on search and the Stratum client can stay focused on transport.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from pythia_mining.stratum_client import MiningJob

_HEX_RE = re.compile(r"^[0-9a-fA-F]*$")
UINT32_MAX = 2**32 - 1
MAX_TARGET = int("00000000ffff" + "0" * 52, 16)


class MiningValidationError(ValueError):
    """Raised when a mining payload cannot be validated safely."""


@dataclass(frozen=True)
class ShareValidationResult:
    """Immutable result of local proof-of-work validation."""

    valid: bool
    block_hash: str
    header_hex: str
    target: int
    hash_int: int
    merkle_root: str
    reason: Optional[str] = None


def require_hex(value: str, *, field: str, expected_bytes: Optional[int] = None) -> str:
    """Validate and normalize a hexadecimal string."""
    if not isinstance(value, str):
        raise MiningValidationError(f"{field} must be a hex string")
    normalized = value.strip().lower()
    if len(normalized) % 2 != 0:
        raise MiningValidationError(f"{field} must contain an even number of hex characters")
    if not _HEX_RE.fullmatch(normalized):
        raise MiningValidationError(f"{field} contains non-hex characters")
    if expected_bytes is not None and len(normalized) != expected_bytes * 2:
        raise MiningValidationError(f"{field} must be exactly {expected_bytes} bytes")
    return normalized


def hash256(payload: bytes) -> bytes:
    """Bitcoin double-SHA256 digest."""
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()


def reverse_hex_bytes(hex_value: str, *, field: str, expected_bytes: Optional[int] = None) -> str:
    """Reverse byte order of a validated hex string."""
    normalized = require_hex(hex_value, field=field, expected_bytes=expected_bytes)
    return bytes.fromhex(normalized)[::-1].hex()


def uint32_little_endian_hex(value: int, *, field: str) -> str:
    """Encode an unsigned 32-bit integer as little-endian hex."""
    if not isinstance(value, int) or value < 0 or value > UINT32_MAX:
        raise MiningValidationError(f"{field} must be an unsigned 32-bit integer")
    return value.to_bytes(4, byteorder="little", signed=False).hex()


def compact_to_target(nbits_hex: str) -> int:
    """
    Convert Bitcoin compact difficulty bits into a full integer target.

    The compact field stores ``exponent`` in the most-significant byte and a 3-byte
    mantissa in the remaining bytes. This follows Bitcoin Core's target expansion for
    positive, non-overflowing compact values.
    """
    normalized = require_hex(nbits_hex, field="nbits", expected_bytes=4)
    compact = int(normalized, 16)
    exponent = compact >> 24
    mantissa = compact & 0x007FFFFF
    negative = bool(compact & 0x00800000)
    if negative or mantissa == 0:
        raise MiningValidationError("nbits encodes an invalid target")
    if exponent <= 3:
        target = mantissa >> (8 * (3 - exponent))
    else:
        target = mantissa << (8 * (exponent - 3))
    if target <= 0 or target > 2**256 - 1:
        raise MiningValidationError("nbits target is outside uint256 bounds")
    return target


def effective_target(job: MiningJob) -> int:
    """Return the stricter positive target from the Stratum job and its compact bits."""
    if not isinstance(job.target, int) or job.target <= 0:
        raise MiningValidationError("job target must be a positive integer")
    compact_target = compact_to_target(job.nbits)
    return min(job.target, compact_target)


def coinbase_transaction_hex(job: MiningJob, extranonce2: str) -> str:
    """Assemble the Stratum coinbase transaction hex from its split parts and extranonces."""
    extranonce2_hex = require_hex(extranonce2, field="extranonce2")
    expected_extranonce2_chars = job.extranonce2_size * 2
    if len(extranonce2_hex) != expected_extranonce2_chars:
        raise MiningValidationError(
            f"extranonce2 must be exactly {job.extranonce2_size} bytes for this job"
        )
    return "".join([
        require_hex(job.coinbase_parts[0], field="coinbase part 1"),
        require_hex(job.extranonce1, field="extranonce1"),
        extranonce2_hex,
        require_hex(job.coinbase_parts[1], field="coinbase part 2"),
    ])


def coinbase_hash_hex(job: MiningJob, extranonce2: str) -> str:
    """Return internal byte-order double-SHA256 hash of the assembled coinbase."""
    coinbase_hex = coinbase_transaction_hex(job, extranonce2)
    return hash256(bytes.fromhex(coinbase_hex)).hex()


def compute_merkle_root(coinbase_hash_internal_hex: str, merkle_branch: Iterable[str]) -> str:
    """
    Compute a Bitcoin merkle root in internal byte order.

    Stratum merkle branches are concatenated to the current hash in the given order and
    double-SHA256 hashed at each level. The returned value is internal byte order, ready
    to be inserted into the block header after byte reversal.
    """
    current = bytes.fromhex(require_hex(coinbase_hash_internal_hex, field="coinbase hash", expected_bytes=32))
    for index, branch_hex in enumerate(merkle_branch):
        branch = bytes.fromhex(require_hex(branch_hex, field=f"merkle branch {index}", expected_bytes=32))
        current = hash256(current + branch)
    return current.hex()


def build_block_header(job: MiningJob, merkle_root_internal_hex: str, nonce: int) -> bytes:
    """Build an 80-byte Bitcoin block header from a Stratum mining job."""
    header_hex = "".join([
        reverse_hex_bytes(job.version, field="version", expected_bytes=4),
        reverse_hex_bytes(job.prevhash, field="previous block hash", expected_bytes=32),
        reverse_hex_bytes(merkle_root_internal_hex, field="merkle root", expected_bytes=32),
        reverse_hex_bytes(job.ntime, field="ntime", expected_bytes=4),
        reverse_hex_bytes(job.nbits, field="nbits", expected_bytes=4),
        uint32_little_endian_hex(nonce, field="nonce"),
    ])
    header = bytes.fromhex(header_hex)
    if len(header) != 80:
        raise MiningValidationError("block header must be exactly 80 bytes")
    return header


def block_hash(header: bytes) -> bytes:
    """Return Bitcoin block hash digest in internal byte order."""
    if len(header) != 80:
        raise MiningValidationError("block header must be exactly 80 bytes")
    return hash256(header)


def display_hash(internal_hash: bytes) -> str:
    """Convert internal byte-order hash bytes into conventional displayed hash hex."""
    if len(internal_hash) != 32:
        raise MiningValidationError("hash must be exactly 32 bytes")
    return internal_hash[::-1].hex()


def validate_share(job: MiningJob, nonce: int, extranonce2: str) -> ShareValidationResult:
    """
    Validate a solved nonce locally before any pool submission.

    Returns a structured result instead of raising for ordinary non-winning shares. It
    still raises ``MiningValidationError`` for malformed job data because malformed job
    data is an upstream correctness/security fault.
    """
    coinbase_hash = coinbase_hash_hex(job, extranonce2)
    merkle_root = compute_merkle_root(coinbase_hash, job.merkle_branch)
    header = build_block_header(job, merkle_root, nonce)
    digest = block_hash(header)
    hash_int = int.from_bytes(digest, byteorder="little", signed=False)
    target = effective_target(job)
    valid = hash_int <= target
    return ShareValidationResult(
        valid=valid,
        block_hash=display_hash(digest),
        header_hex=header.hex(),
        target=target,
        hash_int=hash_int,
        merkle_root=merkle_root,
        reason=None if valid else "hash_above_target",
    )


def validate_merkle_branch_hex(merkle_branch: List[str]) -> List[str]:
    """Normalize and validate every merkle-branch element as a 32-byte hash."""
    return [require_hex(value, field=f"merkle branch {index}", expected_bytes=32) for index, value in enumerate(merkle_branch)]
