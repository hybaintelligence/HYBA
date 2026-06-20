#!/usr/bin/env python3
"""Validate that all review-gap closures needed for a first customer pilot exist.

This is a static repository gate. It proves that internal artifacts, code paths,
and validation hooks are present; it deliberately does not claim external customer
acceptance, regulatory certification, or live revenue.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "review_gap_closure_registry.json"


def _load_registry() -> dict[str, Any]:
    with REGISTRY.open(encoding="utf-8") as fh:
        return json.load(fh)


def _path_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def main() -> int:
    errors: list[str] = []
    registry = _load_registry()

    if "external" not in registry.get("claim_boundary", ""):
        errors.append("Registry claim_boundary must explicitly distinguish internal closure from external validation.")

    reviews = registry.get("reviews", [])
    if not reviews:
        errors.append("Registry must contain at least one review entry.")

    for review in reviews:
        review_id = review.get("id", "<unknown>")
        total = int(review.get("total_count", 0))
        closed = int(review.get("closed_count", -1))
        if total <= 0 or closed < total:
            errors.append(f"{review_id}: closed_count must be >= total_count and total_count must be positive.")
        if not review.get("remaining_external_gaps"):
            errors.append(f"{review_id}: remaining external gaps must be listed to prevent over-claiming.")
        for rel_path in review.get("required_paths", []):
            if not _path_exists(rel_path):
                errors.append(f"{review_id}: missing required path {rel_path}")

    # Run the two authoritative static gates that are fast and environment-local.
    for command in [
        [sys.executable, "scripts/check_institutional_qaas_gap_closure.py"],
        [sys.executable, "scripts/check_forensic_gap_closure.py"],
    ]:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if result.returncode != 0:
            errors.append(
                f"Command {' '.join(command)} failed with {result.returncode}: {result.stderr or result.stdout}"
            )

    if errors:
        print("First-customer readiness gate failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("✓ First-customer readiness gate passed: all review-gap closure artifacts are present and claim-bounded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
