#!/usr/bin/env python3
"""Static local gate for the June 2026 HYBA forensic gap closure.

The gate deliberately excludes PYTHIA autonomy internals. It verifies the
security/config/operations controls around the platform: credentials, browser
session posture, security headers, production-error sanitisation, secret hygiene,
and required operational runbooks.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "scripts/check_secret_hygiene.py",
    "scripts/run_local_security_scan.py",
    "docs/security/FORENSIC_GAP_CLOSURE_MATRIX_2026-06-19.md",
    "docs/security/DEPENDENCY_SECURITY_AND_SBOM.md",
    "docs/runbooks/INCIDENT_RESPONSE_PLAYBOOK.md",
    "docs/runbooks/DISASTER_RECOVERY_AND_BACKUP.md",
    "docs/runbooks/DATABASE_MIGRATION_ROLLBACK.md",
    "docs/observability/MONITORING_ALERTING_BASELINE.md",
]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED_FILES:
        require((ROOT / path).exists(), f"Missing required closure artifact: {path}", errors)

    seed = read("python_backend/scripts/seed_admin_user.py")
    require("admin123456" not in seed, "seed_admin_user.py still contains admin123456", errors)
    require(
        "HYBA_INITIAL_ADMIN_PASSWORD" in seed and "validate_password_strength" in seed,
        "seed_admin_user.py must require HYBA_INITIAL_ADMIN_PASSWORD/--password and validate strength",
        errors,
    )

    auth = read("python_backend/hyba_genesis_api/api/auth.py")
    jwt_handler = read("python_backend/hyba_genesis_api/auth/jwt_handler.py")
    require("httponly=True" in auth, "auth login must set an httpOnly cookie", errors)
    require("ACCESS_COOKIE_NAME" in jwt_handler, "JWT handler must define/access the auth cookie", errors)
    require("Cookie(None" in jwt_handler, "JWT handler must accept cookie-authenticated browser sessions", errors)
    require("/logout" in auth and "delete_cookie" in auth, "auth API must expose logout cookie clearing", errors)

    auth_provider = read("src/components/AuthProvider.tsx")
    require("localStorage" not in auth_provider, "AuthProvider must not read auth tokens from localStorage", errors)
    require("credentials: \"include\"" in auth_provider, "AuthProvider must request backend profile with cookies", errors)

    posture = read("python_backend/hyba_genesis_api/core/api_posture.py")
    for header in [
        "Strict-Transport-Security",
        "X-Frame-Options",
        "Content-Security-Policy",
        "X-Content-Type-Options",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Resource-Policy",
    ]:
        require(header in posture, f"API posture missing security header {header}", errors)
    require(
        "sanitize_production_errors" in posture and "Internal server error. Reference the request_id" in posture,
        "API posture must sanitize production errors",
        errors,
    )

    for path in ["config/mining_pools_live.json", "python_backend/mining_pools_config.json"]:
        text = read(path)
        require("${HYBA_POOL_" in text, f"{path} must use environment-backed pool credentials", errors)
        require(
            not re.search(r'"password"\s*:\s*"(123|anything123|admin123456|password|changeme)"', text),
            f"{path} still contains a concrete known/default password",
            errors,
        )

    if errors:
        print("Forensic gap closure gate failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("✓ Forensic gap closure gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
