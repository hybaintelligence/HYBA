#!/usr/bin/env python3
"""Validate institutional QaaS gap-closure registry completeness."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_TOP_LEVEL = {"version", "status", "claim_boundary", "gates", "gaps"}
REQUIRED_GAP_FIELDS = {
    "id",
    "lens",
    "gap",
    "artifact",
    "owner",
    "acceptance_criteria",
    "validation_hook",
}
EXPECTED_GATES = {
    "artifact",
    "owner",
    "acceptance_criteria",
    "claim_boundary",
    "validation_hook",
}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    registry_path = (
        repo_root / "docs" / "institutional_qaas" / "gap_closure_registry.json"
    )
    protocol_path = repo_root / "docs" / "INSTITUTIONAL_QAAS_GAP_CLOSURE.md"

    errors: list[str] = []

    if not protocol_path.exists():
        errors.append(
            f"Missing protocol document: {protocol_path.relative_to(repo_root)}"
        )

    if not registry_path.exists():
        errors.append(f"Missing registry: {registry_path.relative_to(repo_root)}")
        print("\n".join(errors), file=sys.stderr)
        return 1

    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    missing_top_level = REQUIRED_TOP_LEVEL - set(registry)
    if missing_top_level:
        errors.append(f"Registry missing top-level fields: {sorted(missing_top_level)}")

    gates = set(registry.get("gates", []))
    if gates != EXPECTED_GATES:
        errors.append(
            f"Registry gates mismatch: expected {sorted(EXPECTED_GATES)}, got {sorted(gates)}"
        )

    claim_boundary = registry.get("claim_boundary", "")
    for required_phrase in ("Local reproducible", "external evidence"):
        if required_phrase not in claim_boundary:
            errors.append(f"Claim boundary missing phrase: {required_phrase}")

    gaps = registry.get("gaps", [])
    if len(gaps) < 19:
        errors.append(f"Expected at least 19 institutional gaps, found {len(gaps)}")

    seen_ids: set[str] = set()
    for index, gap in enumerate(gaps, start=1):
        missing_fields = REQUIRED_GAP_FIELDS - set(gap)
        if missing_fields:
            errors.append(f"Gap #{index} missing fields: {sorted(missing_fields)}")
        gap_id = gap.get("id")
        if gap_id in seen_ids:
            errors.append(f"Duplicate gap id: {gap_id}")
        seen_ids.add(gap_id)
        for field in REQUIRED_GAP_FIELDS:
            if not str(gap.get(field, "")).strip():
                errors.append(f"Gap #{index} has empty field: {field}")

    if errors:
        print("Institutional QaaS gap-closure validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        f"Institutional QaaS gap-closure validation passed: {len(gaps)} gaps tracked with {len(gates)} closure gates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
