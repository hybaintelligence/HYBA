from __future__ import annotations

import pytest

from pythia_mining.pool_profiles import (
    PoolProfileError,
    build_profile,
    validate_pool_url,
)

TLS_SCHEMES = ("stratum+ssl", "stratum+tls", "stratum2+ssl", "stratum2+tls")
CLEAR_SCHEMES = ("stratum+tcp", "stratum2+tcp")


@pytest.mark.parametrize("scheme", CLEAR_SCHEMES)
@pytest.mark.parametrize("port", [1, 3333, 443, 65535])
def test_tls_required_rejects_all_cleartext_stratum_urls(scheme: str, port: int) -> None:
    with pytest.raises(PoolProfileError, match="TLS is required"):
        validate_pool_url(f"{scheme}://pool.example:{port}", tls_required=True)


@pytest.mark.parametrize("scheme", TLS_SCHEMES)
@pytest.mark.parametrize("port", [1, 3334, 443, 65535])
def test_tls_required_accepts_all_tls_stratum_urls(scheme: str, port: int) -> None:
    assert (
        validate_pool_url(f"{scheme}://pool.example:{port}", tls_required=True)
        == f"{scheme}://pool.example:{port}"
    )


def test_pool_profile_preserves_tls_requirement_for_runtime_enforcement() -> None:
    profile = build_profile(
        "securepool",
        name="Secure Pool",
        url="stratum+ssl://pool.example:3334",
        username="worker",
        password="x",
        tls_required=True,
    )

    assert profile.tls_required is True
