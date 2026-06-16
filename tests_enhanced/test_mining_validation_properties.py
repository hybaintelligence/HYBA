from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from pythia_mining.mining_validation import (
    MiningValidationError,
    compute_merkle_root,
    display_hash,
    hash256,
    require_hex,
    reverse_hex_bytes,
    uint32_little_endian_hex,
)

hex_bytes = st.binary(min_size=0, max_size=64).map(bytes.hex)
full_hash_hex = st.binary(min_size=32, max_size=32).map(bytes.hex)
uint32s = st.integers(min_value=0, max_value=2**32 - 1)


@given(payload=st.binary(min_size=0, max_size=512))
def test_hash256_is_deterministic_and_exactly_32_bytes(payload: bytes) -> None:
    first = hash256(payload)
    second = hash256(payload)

    assert first == second
    assert len(first) == 32


@given(value=hex_bytes)
def test_require_hex_normalizes_valid_even_length_hex(value: str) -> None:
    normalized = require_hex(value.upper(), field="payload")

    assert normalized == value.lower()
    assert len(normalized) % 2 == 0


@given(
    value=st.text(min_size=1).filter(
        lambda text: any(ch not in "0123456789abcdefABCDEF" for ch in text)
    )
)
def test_require_hex_rejects_non_hex_payloads(value: str) -> None:
    if len(value) % 2 == 1:
        value = value + "0"

    with pytest.raises(MiningValidationError):
        require_hex(value, field="payload")


@given(value=hex_bytes)
def test_reverse_hex_bytes_is_an_involution(value: str) -> None:
    reversed_once = reverse_hex_bytes(value, field="payload")
    reversed_twice = reverse_hex_bytes(reversed_once, field="payload")

    assert reversed_twice == value.lower()


@given(value=uint32s)
def test_uint32_little_endian_round_trips(value: int) -> None:
    encoded = uint32_little_endian_hex(value, field="nonce")

    assert int.from_bytes(bytes.fromhex(encoded), byteorder="little", signed=False) == value


@given(value=st.one_of(st.integers(max_value=-1), st.integers(min_value=2**32)))
def test_uint32_little_endian_rejects_out_of_bounds(value: int) -> None:
    with pytest.raises(MiningValidationError):
        uint32_little_endian_hex(value, field="nonce")


@given(coinbase=full_hash_hex, branch=st.lists(full_hash_hex, max_size=8))
def test_merkle_root_is_deterministic_for_same_branch_order(
    coinbase: str, branch: list[str]
) -> None:
    first = compute_merkle_root(coinbase, branch)
    second = compute_merkle_root(coinbase, list(branch))

    assert first == second
    assert len(first) == 64


@given(internal_hash=st.binary(min_size=32, max_size=32))
def test_display_hash_reverses_internal_byte_order(internal_hash: bytes) -> None:
    displayed = display_hash(internal_hash)

    assert displayed == internal_hash[::-1].hex()
    assert len(displayed) == 64
