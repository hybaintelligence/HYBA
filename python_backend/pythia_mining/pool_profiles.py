"""Validated open-network Bitcoin/Stratum pool profiles.

Pool URL, payout address, worker name, pool id, and the conventional Stratum
password value ``x`` are launch configuration for an open Bitcoin network, not
HYBA application secrets. Runtime profile files are still written with 0600 file
permissions so operators do not accidentally expose deployment routing choices.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable
from urllib.parse import unquote, urlparse, urlunparse


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
    max_reconnect_attempts: int = 10
    max_share_retry_attempts: int = 3
    reconnect_backoff_base: float = 1.0
    reconnect_backoff_max: float = 60.0
    share_retry_backoff_base: float = 0.5
    share_retry_backoff_max: float = 5.0

    def to_dict(self, include_secret_fields: bool = False) -> Dict[str, Any]:
        payload = asdict(self)
        if not include_secret_fields:
            payload["username"] = "<configured>" if self.username else ""
            payload["password"] = "<configured>" if self.password else ""
        return payload


@dataclass(frozen=True)
class PoolCredentialConfig:
    pool_id: str
    name: str
    url: str
    stratum_version: int
    tls_required: bool
    credential_mode: str
    username: str = ""
    password: str = ""
    btc_address: str = ""
    worker: str = ""
    nicehash_pool_id: str = ""
    priority: int = 100
    enabled: bool = True
    source: str = "runtime"
    max_reconnect_attempts: int = 10
    max_share_retry_attempts: int = 3
    reconnect_backoff_base: float = 1.0
    reconnect_backoff_max: float = 60.0
    share_retry_backoff_base: float = 0.5
    share_retry_backoff_max: float = 5.0

    def resolved_username(self) -> str:
        _clean_url, inline_username, _inline_password = split_pool_url_credentials(self.url)
        if self.pool_id == "ckpool":
            return self.btc_address or self.username or inline_username
        if self.pool_id == "nicehash":
            return self.username or inline_username or f"{self.nicehash_pool_id}.{self.worker}".strip(".")
        return self.username or inline_username

    def resolved_password(self) -> str:
        _clean_url, _inline_username, inline_password = split_pool_url_credentials(self.url)
        if self.pool_id in {"ckpool", "nicehash"}:
            return self.password or inline_password or "x"
        return self.password or inline_password

    def to_profile(self) -> PoolProfile:
        return build_profile(
            self.pool_id,
            name=self.name,
            url=self.url,
            username=self.resolved_username(),
            password=self.resolved_password(),
            stratum_version=self.stratum_version,
            priority=self.priority,
            tls_required=self.tls_required,
            max_reconnect_attempts=self.max_reconnect_attempts,
            max_share_retry_attempts=self.max_share_retry_attempts,
            reconnect_backoff_base=self.reconnect_backoff_base,
            reconnect_backoff_max=self.reconnect_backoff_max,
            share_retry_backoff_base=self.share_retry_backoff_base,
            share_retry_backoff_max=self.share_retry_backoff_max,
        )

    def to_dict(self, include_secret_fields: bool = False) -> Dict[str, Any]:
        payload = asdict(self)
        payload["configured"] = bool(self.resolved_username() and self.resolved_password())
        payload["resolved_username"] = (
            self.resolved_username()
            if include_secret_fields
            else ("<configured>" if self.resolved_username() else "")
        )
        if not include_secret_fields:
            clean_url, inline_username, inline_password = split_pool_url_credentials(self.url)
            payload["url"] = clean_url if (inline_username or inline_password) else self.url
            if payload.get("username"):
                payload["username"] = "<configured>"
            if payload.get("password"):
                payload["password"] = "<configured>"
            if payload.get("btc_address"):
                payload["btc_address"] = "<configured>"
            if payload.get("worker"):
                payload["worker"] = "<configured>"
            if payload.get("nicehash_pool_id"):
                payload["nicehash_pool_id"] = "<configured>"
        return payload


SUPPORTED_SCHEMES = {
    "stratum+tcp",
    "stratum+ssl",
    "stratum+tls",
    "stratum2+tcp",
    "stratum2+ssl",
    "stratum2+tls",
}
SUPPORTED_VERSIONS = {1, 2}
DEFAULT_POOL_SPECS: dict[str, dict[str, Any]] = {
    "viabtc": {
        "name": "ViaBTC BTC",
        "url": "stratum+ssl://btc.viabtc.io:3334",
        "stratum_version": 1,
        "tls_required": True,
        "credential_mode": "username_password",
        "required_fields": ["username", "password"],
        "priority": 10,
    },
    "braiins": {
        "name": "Braiins Pool",
        "url": "stratum+tcp://stratum.braiins.com:3333",
        "stratum_version": 1,
        "tls_required": False,
        "credential_mode": "username_password",
        "required_fields": ["username", "password"],
        "priority": 20,
    },
    "ckpool": {
        "name": "Solo CKPool",
        "url": "stratum+tcp://solo.ckpool.org:3333",
        "stratum_version": 1,
        "tls_required": False,
        "credential_mode": "btc_address",
        "required_fields": ["btc_address"],
        "priority": 30,
    },
    "nicehash": {
        "name": "NiceHash SHA256",
        "url": "stratum+ssl://sha256.auto.nicehash.com:443",
        "stratum_version": 1,
        "tls_required": True,
        "credential_mode": "nicehash_worker_pool_id",
        "required_fields": ["worker", "nicehash_pool_id"],
        "priority": 40,
    },
    "stratumv2": {
        "name": "Operator Stratum V2 Pool",
        "url": "stratum2+ssl://pool.example.com:3336",
        "stratum_version": 2,
        "tls_required": True,
        "credential_mode": "username_password",
        "required_fields": ["username", "password"],
        "priority": 50,
    },
}


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def runtime_pool_config_path() -> Path:
    return Path(
        os.getenv("HYBA_POOL_CONFIG_PATH", str(_backend_root() / "mining_pools_config.json"))
    )


def split_pool_url_credentials(url: str) -> tuple[str, str, str]:
    """Return ``(clean_url, username, password)`` for Stratum URLs.

    Operators sometimes paste pool credentials in URL authority form, e.g.
    ``stratum+tcp://worker:token@host:3333``. The live Stratum protocol still
    requires username/password in the ``mining.authorize`` payload, while status
    surfaces must never echo those credentials back. This helper extracts the
    inline credentials and returns a credential-free URL for storage/status.
    """

    parsed = urlparse(url)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    if not username and not password:
        return url, "", ""
    hostname = parsed.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = hostname
    if parsed.port is not None:
        netloc = f"{netloc}:{parsed.port}"
    clean_url = urlunparse(
        (
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment,
        )
    )
    return clean_url, username, password


def validate_pool_url(url: str, *, tls_required: bool = False) -> str:
    clean_url, _username, _password = split_pool_url_credentials(url)
    parsed = urlparse(clean_url)
    if parsed.scheme not in SUPPORTED_SCHEMES:
        raise PoolProfileError(f"unsupported pool URL scheme: {parsed.scheme}")
    if parsed.scheme.startswith("stratum+") and parsed.netloc.endswith(":3336"):
        raise PoolProfileError("Stratum V2 port 3336 requires a stratum2+ URL scheme")
    if not parsed.hostname:
        raise PoolProfileError("pool URL must include hostname")
    if parsed.port is None:
        raise PoolProfileError("pool URL must include an explicit port")
    if not (1 <= int(parsed.port) <= 65535):
        raise PoolProfileError("pool URL port is out of range")
    if tls_required and parsed.scheme not in {
        "stratum+ssl",
        "stratum+tls",
        "stratum2+ssl",
        "stratum2+tls",
    }:
        raise PoolProfileError("TLS is required for this pool profile")
    return clean_url


def validate_profile(profile: PoolProfile) -> PoolProfile:
    if not profile.pool_id:
        raise PoolProfileError("pool_id is required")
    if not profile.name:
        raise PoolProfileError("pool name is required")
    clean_url = validate_pool_url(profile.url, tls_required=profile.tls_required)
    if not profile.username:
        raise PoolProfileError(f"pool {profile.pool_id} requires username")
    if profile.password is None or profile.password == "":
        raise PoolProfileError(f"pool {profile.pool_id} requires password/auth value")
    if int(profile.stratum_version) not in SUPPORTED_VERSIONS:
        raise PoolProfileError("stratum_version must be 1 or 2")
    if int(profile.priority) < 0:
        raise PoolProfileError("priority must be non-negative")
    if clean_url != profile.url:
        return PoolProfile(
            **{
                **asdict(profile),
                "url": clean_url,
            }
        )
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
    max_reconnect_attempts: int = 10,
    max_share_retry_attempts: int = 3,
    reconnect_backoff_base: float = 1.0,
    reconnect_backoff_max: float = 60.0,
    share_retry_backoff_base: float = 0.5,
    share_retry_backoff_max: float = 5.0,
) -> PoolProfile:
    clean_url, inline_username, inline_password = split_pool_url_credentials(url)
    resolved_username = username or inline_username
    resolved_password = password or inline_password
    return validate_profile(
        PoolProfile(
            pool_id=pool_id.lower(),
            name=name,
            url=clean_url,
            username=resolved_username,
            password=resolved_password,
            stratum_version=int(stratum_version),
            priority=int(priority),
            tls_required=bool(tls_required),
            max_reconnect_attempts=int(max_reconnect_attempts),
            max_share_retry_attempts=int(max_share_retry_attempts),
            reconnect_backoff_base=float(reconnect_backoff_base),
            reconnect_backoff_max=float(reconnect_backoff_max),
            share_retry_backoff_base=float(share_retry_backoff_base),
            share_retry_backoff_max=float(share_retry_backoff_max),
        )
    )


def order_profiles(profiles: Iterable[PoolProfile]) -> list[PoolProfile]:
    checked = [validate_profile(profile) for profile in profiles]
    return sorted(checked, key=lambda item: (item.priority, item.pool_id))


def _env_value(pool_id: str, field: str) -> str:
    return os.getenv(f"HYBA_POOL_{pool_id.upper()}_{field.upper()}", "")


def default_pool_config(pool_id: str) -> PoolCredentialConfig:
    spec = DEFAULT_POOL_SPECS[pool_id]
    return PoolCredentialConfig(
        pool_id=pool_id,
        name=spec["name"],
        url=os.getenv(f"HYBA_POOL_{pool_id.upper()}_URL", spec["url"]),
        stratum_version=int(
            os.getenv(f"HYBA_POOL_{pool_id.upper()}_STRATUM_VERSION", spec["stratum_version"])
        ),
        tls_required=bool(spec["tls_required"]),
        credential_mode=spec["credential_mode"],
        priority=int(os.getenv(f"HYBA_POOL_{pool_id.upper()}_PRIORITY", spec["priority"])),
        source="default",
    )


def validate_pool_config(config: PoolCredentialConfig) -> PoolCredentialConfig:
    if config.pool_id not in DEFAULT_POOL_SPECS:
        raise PoolProfileError(f"unsupported pool_id: {config.pool_id}")
    spec = DEFAULT_POOL_SPECS[config.pool_id]
    validate_pool_url(config.url, tls_required=bool(spec["tls_required"]))
    if int(config.stratum_version) not in SUPPORTED_VERSIONS:
        raise PoolProfileError("stratum_version must be 1 or 2")
    resolved_username = config.resolved_username()
    resolved_password = config.resolved_password()
    if config.pool_id in {"viabtc", "braiins"}:
        if not resolved_username or not resolved_password:
            raise PoolProfileError(f"{config.pool_id} requires username and password/auth value")
    elif config.pool_id == "ckpool":
        if not config.btc_address and not config.username and not resolved_username:
            raise PoolProfileError("ckpool requires a BTC address")
    elif config.pool_id == "nicehash":
        if not config.worker and not config.nicehash_pool_id and not resolved_username:
            raise PoolProfileError("nicehash requires worker and NH pool id")
    elif config.pool_id == "stratumv2":
        if not resolved_username or not resolved_password:
            raise PoolProfileError("stratumv2 requires username and password/auth value")
    config.to_profile()
    return config


def load_runtime_pool_configs(
    include_env: bool = True,
) -> dict[str, PoolCredentialConfig]:
    configs = {pool_id: default_pool_config(pool_id) for pool_id in DEFAULT_POOL_SPECS}
    if include_env:
        for pool_id in DEFAULT_POOL_SPECS:
            env_config = configs[pool_id]
            username = _env_value(pool_id, "USERNAME")
            password = _env_value(pool_id, "PASSWORD")
            btc_address = _env_value(pool_id, "BTC_ADDRESS")
            worker = _env_value(pool_id, "WORKER")
            nicehash_pool_id = _env_value(pool_id, "NH_POOL_ID") or _env_value(
                pool_id, "NICEHASH_POOL_ID"
            )
            if any([username, password, btc_address, worker, nicehash_pool_id]):
                configs[pool_id] = PoolCredentialConfig(
                    pool_id=pool_id,
                    name=env_config.name,
                    url=env_config.url,
                    stratum_version=env_config.stratum_version,
                    tls_required=env_config.tls_required,
                    credential_mode=env_config.credential_mode,
                    username=username,
                    password=password,
                    btc_address=btc_address,
                    worker=worker,
                    nicehash_pool_id=nicehash_pool_id,
                    priority=env_config.priority,
                    enabled=True,
                    source="env",
                )
    path = runtime_pool_config_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PoolProfileError(f"failed to read runtime pool config: {exc}") from exc
        for pool_id, payload in raw.get("pools", {}).items():
            if pool_id not in DEFAULT_POOL_SPECS:
                continue
            base = configs[pool_id]
            configs[pool_id] = PoolCredentialConfig(
                pool_id=pool_id,
                name=base.name,
                url=str(payload.get("url") or base.url),
                stratum_version=int(payload.get("stratum_version") or base.stratum_version),
                tls_required=base.tls_required,
                credential_mode=base.credential_mode,
                username=str(payload.get("username") or ""),
                password=str(payload.get("password") or ""),
                btc_address=str(payload.get("btc_address") or ""),
                worker=str(payload.get("worker") or ""),
                nicehash_pool_id=str(payload.get("nicehash_pool_id") or ""),
                priority=int(payload.get("priority") or base.priority),
                enabled=bool(payload.get("enabled", True)),
                source="runtime",
            )
    return configs


def save_runtime_pool_config(config: PoolCredentialConfig) -> PoolCredentialConfig:
    checked = validate_pool_config(config)
    path = runtime_pool_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    raw: dict[str, Any] = {"pools": {}}
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw = {"pools": {}}
    profile = checked.to_profile()
    raw.setdefault("pools", {})[checked.pool_id] = {
        "url": profile.url,
        "stratum_version": checked.stratum_version,
        "username": checked.resolved_username(),
        "password": checked.resolved_password(),
        "btc_address": checked.btc_address,
        "worker": checked.worker,
        "nicehash_pool_id": checked.nicehash_pool_id,
        "priority": checked.priority,
        "enabled": checked.enabled,
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(raw, handle, indent=2, sort_keys=True)
    os.replace(tmp, path)
    os.chmod(path, 0o600)
    return checked


def load_pool_profiles() -> list[PoolProfile]:
    profiles: list[PoolProfile] = []
    for config in load_runtime_pool_configs().values():
        if not config.enabled:
            continue
        try:
            profiles.append(config.to_profile())
        except PoolProfileError:
            continue
    return order_profiles(profiles)


__all__ = [
    "DEFAULT_POOL_SPECS",
    "PoolCredentialConfig",
    "PoolProfileError",
    "PoolProfile",
    "default_pool_config",
    "load_pool_profiles",
    "load_runtime_pool_configs",
    "runtime_pool_config_path",
    "save_runtime_pool_config",
    "split_pool_url_credentials",
    "validate_pool_config",
    "validate_pool_url",
    "validate_profile",
    "build_profile",
    "order_profiles",
]
