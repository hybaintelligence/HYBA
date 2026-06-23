#!/usr/bin/env python3
"""Scan Python and TypeScript source for committed credential patterns."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}
PATTERNS = {
    "raw_hyba_api_key": re.compile(r"hyba_live_[A-Za-z0-9_\-]{20,}"),
    "jwt_token": re.compile(
        r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"
    ),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "wallet_address_assignment": re.compile(
        r"(?i)(wallet|payout)_address\s*=\s*['\"](?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}['\"]"
    ),
    "private_key_assignment": re.compile(
        r"(?i)(private_key|pool_password|jwt_secret|api_key_secret)\s*=\s*['\"][^'\"]{12,}['\"]"
    ),
}
ALLOWLIST = {"scripts/check_secrets.py"}


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in {".py", ".ts", ".tsx"}:
            files.append(path)
    return files


def main() -> int:
    findings: list[str] = []
    for path in iter_source_files():
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if "pragma: allow-secret-pattern" in line:
                continue
            for name, pattern in PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{rel}:{line_no}: {name}")
    if findings:
        print("Secret hygiene scan failed:")
        print("\n".join(findings))
        return 1
    print(
        "Secret hygiene scan passed: no credential patterns found in .py/.ts/.tsx files"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
