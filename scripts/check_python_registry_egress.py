#!/usr/bin/env python3
"""Check package-registry egress for handover-critical Python pins.

This is a network preflight, not an installer. It verifies that the command-room
host can reach PyPI JSON metadata for the exact backend dependency pins that are
required before full FastAPI/backend tests can collect. It exits non-zero with a
machine-readable payload when DNS/proxy/TLS egress is blocked.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "python_backend" / "requirements.txt"
CRITICAL_PACKAGES = {
    "email-validator",
    "SQLAlchemy",
    "alembic",
}


@dataclass(frozen=True)
class PackageCheck:
    package: str
    version: str
    status: str
    url: str
    message: str


def parse_pins(requirements: Path) -> dict[str, str]:
    pins: dict[str, str] = {}
    for raw_line in requirements.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "==" not in line:
            continue
        package, version = line.split("==", 1)
        normalized = package.strip()
        if normalized in CRITICAL_PACKAGES:
            pins[normalized] = version.strip()
    missing = sorted(CRITICAL_PACKAGES - set(pins))
    if missing:
        raise SystemExit(
            f"requirements lock is missing critical pins: {', '.join(missing)}"
        )
    return pins


def fetch_package(package: str, version: str, timeout: float) -> PackageCheck:
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    request = urllib.request.Request(
        url, headers={"User-Agent": "hyba-registry-egress-check/1"}
    )
    try:
        with urllib.request.urlopen(
            request, timeout=timeout, context=ssl.create_default_context()
        ) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return PackageCheck(
            package=package,
            version=version,
            status="blocked",
            url=url,
            message=f"{type(exc).__name__}: {exc}",
        )
    info = payload.get("info", {}) if isinstance(payload, dict) else {}
    resolved = str(info.get("version", ""))
    if resolved != version:
        return PackageCheck(
            package=package,
            version=version,
            status="mismatch",
            url=url,
            message=f"PyPI returned version {resolved or '<missing>'}",
        )
    return PackageCheck(
        package=package,
        version=version,
        status="reachable",
        url=url,
        message="metadata reachable",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="per-package request timeout in seconds",
    )
    args = parser.parse_args(argv)

    pins = parse_pins(REQUIREMENTS)
    checks = [
        fetch_package(package, version, args.timeout)
        for package, version in sorted(pins.items())
    ]
    status = (
        "ready" if all(check.status == "reachable" for check in checks) else "blocked"
    )
    payload = {
        "status": status,
        "requirements_lock": str(REQUIREMENTS.relative_to(ROOT)),
        "checks": [asdict(check) for check in checks],
        "proxy_environment_present": {
            key: bool(os.getenv(key))
            for key in (
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "http_proxy",
                "https_proxy",
                "npm_config_http_proxy",
                "npm_config_https_proxy",
            )
        },
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if status != "ready":
        print(
            "\nPython package registry egress is blocked. Resolve DNS/proxy/TLS access to PyPI "
            "or provide an approved internal mirror before running the backend handover gate.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
