#!/usr/bin/env python3
"""Local source-control hygiene gate for sensitive defaults.

This is intentionally local-first and dependency-free. It prevents the repo from
reintroducing known default credentials or concrete pool auth values into tracked
configuration templates.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BAD_LITERALS = {
    "admin123456",
    "anything123",
    "Password123",
    "password123",
    "changeme",
}
FILES_TO_SCAN = [
    "python_backend/scripts/seed_admin_user.py",
    "config/mining_pools_live.json",
    "python_backend/mining_pools_config.json",
    "scripts/configure_live_mining.py",
    "config/.env.example",
    "config/.env.docker",
]
ENV_REF = re.compile(r"^(\$\{[A-Za-z_][A-Za-z0-9_]*\}|env:[A-Za-z_][A-Za-z0-9_]*|x|)$")


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _walk_values(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict):
        items: list[tuple[str, Any]] = []
        for key, nested in value.items():
            items.extend(
                _walk_values(nested, f"{prefix}.{key}" if prefix else str(key))
            )
        return items
    if isinstance(value, list):
        items = []
        for idx, nested in enumerate(value):
            items.extend(_walk_values(nested, f"{prefix}[{idx}]"))
        return items
    return [(prefix, value)]


def _validate_pool_template(path: Path, errors: list[str]) -> None:
    if not path.exists():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path.relative_to(ROOT)} is invalid JSON: {exc}")
        return
    for key_path, value in _walk_values(payload):
        if key_path.endswith("password"):
            text = str(value or "")
            if not ENV_REF.match(text):
                errors.append(
                    f"{path.relative_to(ROOT)}:{key_path} must be empty, x, or env-backed; got concrete value"
                )


def main() -> int:
    errors: list[str] = []
    for rel in FILES_TO_SCAN:
        path = ROOT / rel
        text = _read(path)
        for literal in BAD_LITERALS:
            if literal in text:
                errors.append(
                    f"{rel} contains blocked default/credential literal: {literal}"
                )
    _validate_pool_template(ROOT / "config/mining_pools_live.json", errors)
    _validate_pool_template(ROOT / "python_backend/mining_pools_config.json", errors)

    if errors:
        print("Secret hygiene gate failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Secret hygiene gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
