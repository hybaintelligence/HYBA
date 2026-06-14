#!/usr/bin/env python3
"""Forensic live-deployment repository audit.

This check is intentionally filesystem-only. It blocks committed runtime secrets,
SQLite telemetry artifacts, stale state snapshots, and unsafe live mining
placeholders before a production cut.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKED_FORBIDDEN = {
    "config/mining.pools.env": "runtime pool secret file must not be tracked",
    "python_backend/pythia_state.json": "runtime daemon state snapshot must not be tracked",
    "data/metrics.db": "SQLite metrics artifact must not be tracked",
    "python_backend/data/metrics.db": "SQLite metrics artifact must not be tracked",
}
SECRET_PATTERNS = [
    (
        re.compile(r"HYBA_AUTH_TOKEN\s*=\s*eyJ", re.IGNORECASE),
        "committed JWT bearer token",
    ),
    (
        re.compile(r"JWT_SECRET\s*=\s*(?!replace-with)[^\s#]{24,}", re.IGNORECASE),
        "committed JWT secret",
    ),
    (
        re.compile(
            r"HYBA_POOL_[A-Z0-9_]+_PASSWORD\s*=\s*(?:123|password|secret|changeme|todo)\b",
            re.IGNORECASE,
        ),
        "placeholder pool password",
    ),
    (
        re.compile(r"HYBA_OPERATOR_CREDENTIALS\s*=.*admin123", re.IGNORECASE),
        "documented raw operator password",
    ),
]
TEXT_SUFFIXES = {
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".ts",
    ".tsx",
    ".toml",
    ".yml",
    ".yaml",
}
EXCLUDED_PARTS = {
    ".git",
    "node_modules",
    "venv",
    "dist",
    "__pycache__",
    ".pytest_cache",
}


def tracked_files() -> set[str]:
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def iter_text_files(paths: set[str]):
    for rel in sorted(paths):
        path = ROOT / rel
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and not path.name.endswith(".env"):
            continue
        yield rel, path


def main() -> int:
    tracked = tracked_files()
    violations: list[str] = []
    for rel, reason in TRACKED_FORBIDDEN.items():
        if rel in tracked:
            violations.append(f"{rel}: {reason}")

    for rel, path in iter_text_files(tracked):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, reason in SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                violations.append(f"{rel}:{line_no}: {reason}")

    if violations:
        print("Live deployment forensic audit failed:", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print("Live deployment forensic audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
