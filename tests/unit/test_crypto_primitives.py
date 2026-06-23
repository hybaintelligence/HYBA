"""Unit tests for cryptographic primitives."""
from __future__ import annotations
import hashlib
import pytest


def test_sha256_digest_length():
    """Verify SHA-256 produces 32-byte digests."""
    data = b"test data"
    digest = hashlib.sha256(data).digest()
    assert len(digest) == 32


def test_sha256_hex_length():
    """Verify SHA-256 hex output is 64 characters."""
    data = b"test data"
    hex_digest = hashlib.sha256(data).hexdigest()
    assert len(hex_digest) == 64


def test_sha256_deterministic():
    """Verify SHA-256 is deterministic."""
    data = b"deterministic test"
    assert hashlib.sha256(data).hexdigest() == hashlib.sha256(data).hexdigest()


def test_sha256_avalanche_effect():
    """Verify small input changes produce completely different hashes."""
    hash1 = hashlib.sha256(b"hello").hexdigest()
    hash2 = hashlib.sha256(b"hellp").hexdigest()
    diff_count = sum(1 for a, b in zip(hash1, hash2) if a != b)
    assert diff_count > 30


@pytest.mark.parametrize(
    "input_data",
    [b"", b"a", b"abc" * 1000, bytes(range(256))],
)
def test_sha256_various_inputs(input_data):
    """Verify SHA-256 handles various input sizes."""
    digest = hashlib.sha256(input_data).hexdigest()
    assert len(digest) == 64
    assert isinstance(digest, str)


