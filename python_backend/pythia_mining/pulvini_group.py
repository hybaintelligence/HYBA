"""PULVINI graph automorphism utilities."""

from __future__ import annotations

NONCE_SPACE = 2 ** 32


def identity_permutation(size: int = 32) -> tuple[int, ...]:
    return tuple(range(size))
