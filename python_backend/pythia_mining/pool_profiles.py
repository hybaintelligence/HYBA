"""Validated pool profiles for HYBA production mining.

Profiles intentionally avoid embedding credentials. Credentials must come from
runtime configuration or a secret manager.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlparse


class PoolProfileError(ValueError):
    """Raised when a pool profile is invalid for launch."""


@dataclass(frozen=True)
class PoolProfile:
    pool_id: str
    name: str
    url: str
    username: str
    password: str
    stratum_version: int = 1
    priority: int = 100
    tls_required: bool = False
    def to_dict(self, include_secret_fields: bool = False) -> Dict[str, Any]:
        payload = asdict(self)
        if not include_secret_fields:
            payload["username"] = "<redacted>" if self.username else ""
            payload["password"] = "<redacted>" if self.password else ""
        return payload


SUPPORTED_SCHEMES = {"stratum+tcp", "stratum+ssl", "stratum2+tcp", "stratum2+ssl", "stratum+tls"}
SUPPORTED_VERSIONS = {1, 2}


def validate_pool_url(url: str, *, tls_required: bool = False) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in SUPPORTED_SCHEMES:
        raise PoolProfileError(f"unsupported pool URL scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise PoolProfileError("pool URL must include hostname")
    if parsed.port is not None and not (1 <= int(parsed.port) <= 65535):
        raise PoolProfileError("pool URL port is out of range")
    if tls_required and parsed.scheme not in {"stratum+ssl", "stratum+tls", "stratum2+ssl"}:
        raise PoolProfileError("TLS is required for this pool profile")
    return url


def validate_profile(profile: PoolProfile) -> PoolProfile:
    if not profile.pool_id:
        raise PoolProfileError("pool_id is required")
    if not profile.name:
        raise PoolProfileError("pool name is required")
    validate_pool_url(profile.url, tls_required=profile.tls_required)
    if not profile.username:
        raise PoolProfileError(f"pool {profile.pool_id} requires username")
    if profile.password is None or profile.password == "":
        raise PoolProfileError(f"pool {profile.pool_id} requires password")
    if int(profile.stratum_version) not in SUPPORTED_VERSIONS:
        raise PoolProfileError("stratum_version must be 1 or 2")
    if int(profile.priority) < 0:
        raise PoolProfileError("priority must be non-negative")
    return profile


def build_profile(
    pool_id: str,
    *,
    name: str,
    url: str,
    username: str,
    password: str,
    stratum_version: int = 1,
    priority: int = 100,
    tls_required: bool = False,
) -> PoolProfile:
    return validate_profile(PoolProfile(
        pool_id=pool_id.lower(),
        name=name,
        url=url,
        username=username,
        password=password,
        stratum_version=int(stratum_version),
        priority=int(priority),
        tls_required=bool(tls_required),
    ))


def order_profiles(profiles: Iterable[PoolProfile]) -> list[PoolProfile]:
    checked = [validate_profile(profile) for profile in profiles]
    return sorted(checked, key=lambda item: (item.priority, item.pool_id))


__all__ = ["PoolProfileError", "PoolProfile", "validate_pool_url", "validate_profile", "build_profile", "order_profiles"]
