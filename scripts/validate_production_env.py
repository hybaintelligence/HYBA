#!/usr/bin/env python3
"""Validate HYBA_FULLSTACK production environment before deployment."""

from __future__ import annotations

import os
import re
import sys
from urllib.parse import urlparse

ARGON2ID = re.compile(r"^\$argon2id\$v=\d+\$m=\d+,t=\d+,p=\d+\$[^$]+\$[^$]+$")
POOL_IDS = ("VIABTC", "NICEHASH", "BRAIINS", "CKPOOL")
APPROVED_ROLES = {"ceo", "treasury_admin", "mining_operator", "treasury_viewer", "mining:read", "mining:operate"}
TRUE_VALUES = {"1", "true", "yes", "on"}
STRATUM_V1_SCHEMES = {"stratum+ssl", "stratum+tls", "stratum+tcp"}
STRATUM_V2_SCHEMES = {"stratum2+ssl", "stratum2+tls", "stratum2+tcp"}
PULVINI_HASHRATE_CAP_EHS = 1.0


def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    lowered = value.strip().lower()
    return not lowered or "replace-with" in lowered or lowered in {"123", "changeme", "password", "secret", "todo"}


def _require(name: str, errors: list[str]) -> str | None:
    value = os.getenv(name)
    if _is_placeholder(value):
        errors.append(f"{name} is required and must not be a placeholder")
    return value


def _credential_entries(raw: str) -> list[str]:
    normalized = raw.strip()
    if not normalized:
        return []
    if ";" in normalized or "\n" in normalized:
        return [item.strip() for item in normalized.replace("\n", ";").split(";") if item.strip()]
    if "$argon2" in normalized:
        return [normalized]
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _validate_operator_credentials(errors: list[str]) -> None:
    raw = _require("HYBA_OPERATOR_CREDENTIALS", errors)
    if not raw:
        return
    for item in _credential_entries(raw):
        parts = item.split(":", 2)
        if len(parts) != 3:
            errors.append("HYBA_OPERATOR_CREDENTIALS entries must use username:$argon2id$...:role separated by semicolons")
            continue
        username, password_hash, role = (part.strip() for part in parts)
        if not username:
            errors.append("HYBA_OPERATOR_CREDENTIALS contains an empty username")
        if not ARGON2ID.match(password_hash):
            errors.append("HYBA_OPERATOR_CREDENTIALS password field must be an Argon2id encoded hash")
        if role not in APPROVED_ROLES:
            errors.append(f"HYBA_OPERATOR_CREDENTIALS role {role!r} is not an approved production role/scope")


def _validate_backend_url(errors: list[str]) -> None:
    url = _require("PULVINI_BACKEND_URL", errors)
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        errors.append("PULVINI_BACKEND_URL must be a valid http(s) URL")


def _pool_secret_env(pool_id: str) -> str:
    return f"HYBA_POOL_{pool_id}_" + "PASSWORD"


def _parse_stratum_version(raw: str | None, pool_id: str, errors: list[str]) -> int | None:
    normalized = (raw or "1").strip().lower().removeprefix("v")
    if normalized not in {"1", "2"}:
        errors.append(f"HYBA_POOL_{pool_id}_STRATUM_VERSION must be 1, v1, 2, or v2")
        return None
    return int(normalized)


def _validate_pool_config(errors: list[str]) -> None:
    configured = []
    for pool_id in POOL_IDS:
        url = os.getenv(f"HYBA_POOL_{pool_id}_URL")
        username = os.getenv(f"HYBA_POOL_{pool_id}_USERNAME")
        pool_secret = os.getenv(_pool_secret_env(pool_id))
        version_raw = os.getenv(f"HYBA_POOL_{pool_id}_STRATUM_VERSION")
        if any([url, username, pool_secret, version_raw]):
            missing = [
                name
                for name, value in [("URL", url), ("USERNAME", username), ("SECRET", pool_secret)]
                if _is_placeholder(value)
            ]
            if missing:
                errors.append(f"HYBA_POOL_{pool_id}_* is partially configured or contains placeholders: missing/invalid {', '.join(missing)}")
                continue
            parsed = urlparse(str(url))
            version = _parse_stratum_version(version_raw, pool_id, errors)
            valid_schemes = STRATUM_V2_SCHEMES if version == 2 else STRATUM_V1_SCHEMES
            if parsed.scheme not in valid_schemes or not parsed.hostname:
                errors.append(
                    f"HYBA_POOL_{pool_id}_URL has invalid Stratum URL format for version {version}: {parsed.scheme or '<missing>'}"
                )
            configured.append(pool_id)
    if not configured:
        errors.append("At least one HYBA_POOL_<ID>_URL/USERNAME/SECRET set is required before live mining deployment")


def _validate_flags(errors: list[str], warnings: list[str]) -> None:
    for name in ("NODE_ENV", "HYBA_ENV"):
        value = os.getenv(name, "").lower()
        if value != "production":
            errors.append(f"{name}=production is required for production deployment")
    if os.getenv("HYBA_ALLOW_DEV_FIXTURES", "false").strip().lower() in TRUE_VALUES:
        errors.append("HYBA_ALLOW_DEV_FIXTURES must be false in production")
    if os.getenv("HYBA_ENABLE_LIVE_STRATUM", "false").strip().lower() not in TRUE_VALUES:
        errors.append("HYBA_ENABLE_LIVE_STRATUM=true is required for production live mining")
    if os.getenv("HYBA_ENABLE_MINING_AUTOCONNECT", "false").strip().lower() in TRUE_VALUES:
        warnings.append("HYBA_ENABLE_MINING_AUTOCONNECT is enabled; this must be approved as an operator-controlled exception")
    if os.getenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "false").strip().lower() in TRUE_VALUES:
        if _is_placeholder(os.getenv("HYBA_LIVE_SHARE_APPROVAL_ID")):
            errors.append("HYBA_ENABLE_LIVE_SHARE_SUBMIT=true requires HYBA_LIVE_SHARE_APPROVAL_ID")
    if os.getenv("HYBA_ENABLE_AUDIT_LOGGING", "false").strip().lower() not in TRUE_VALUES:
        errors.append("HYBA_ENABLE_AUDIT_LOGGING=true is required for production mining")
    capacity = os.getenv("HYBA_QUANTUM_CAPACITY_EHS")
    if capacity:
        try:
            parsed = float(capacity)
        except ValueError:
            errors.append("HYBA_QUANTUM_CAPACITY_EHS must be numeric when set")
        else:
            if parsed <= 0:
                errors.append("HYBA_QUANTUM_CAPACITY_EHS must be positive when set")
            if parsed > PULVINI_HASHRATE_CAP_EHS:
                errors.append(f"HYBA_QUANTUM_CAPACITY_EHS must be <= {PULVINI_HASHRATE_CAP_EHS} EH/s")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    _validate_flags(errors, warnings)
    jwt_secret = _require("JWT_SECRET", errors)
    if jwt_secret and len(jwt_secret) < 32:
        errors.append("JWT_SECRET must be at least 32 characters")
    _validate_operator_credentials(errors)
    _validate_backend_url(errors)
    _validate_pool_config(errors)

    if warnings:
        print("Production environment warnings:", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)
    if errors:
        print("Production environment validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Production environment validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
