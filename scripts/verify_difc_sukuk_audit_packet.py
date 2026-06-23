#!/usr/bin/env python3
"""Verify a DIFC / AAOIFI Sukuk audit packet hash and no-action boundary.

This is intentionally lightweight and independent of the PYTHIA runtime. It
verifies the JSON artifact shape and recomputes the stable packet hash.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


REQUIRED_FALSE_FIELDS = ("automatic_action_allowed",)
REQUIRED_TRUE_FIELDS = ("human_review_required",)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    body = dict(payload)
    body.pop("generated_at_unix", None)
    body.pop("difc_aaiofi_packet_hash", None)
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_packet(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    reported_hash = data.get("difc_aaiofi_packet_hash")
    computed_hash = _stable_hash(data)
    errors: list[str] = []

    if data.get("schema") != "PYTHIA_DIFC_AAOIFI_SUKUK_AUDIT_V1":
        errors.append("Unexpected schema.")
    if not reported_hash:
        errors.append("Missing difc_aaiofi_packet_hash.")
    if reported_hash != computed_hash:
        errors.append("Packet hash mismatch.")
    for field in REQUIRED_TRUE_FIELDS:
        if data.get(field) is not True:
            errors.append(f"{field} must be true.")
    for field in REQUIRED_FALSE_FIELDS:
        if data.get(field) is not False:
            errors.append(f"{field} must be false.")
    if "difc_aaiofi_findings" not in data:
        errors.append("Missing DIFC/AAOIFI findings.")
    if "core_finance_packet" not in data:
        errors.append("Missing core finance packet.")

    return {
        "path": str(path),
        "valid": not errors,
        "reported_hash": reported_hash,
        "computed_hash": computed_hash,
        "errors": errors,
        "verdict": data.get("verdict"),
        "automatic_action_allowed": data.get("automatic_action_allowed"),
        "human_review_required": data.get("human_review_required"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify a DIFC / AAOIFI Sukuk audit packet."
    )
    parser.add_argument("packet", type=Path, help="Path to the generated JSON packet.")
    args = parser.parse_args()

    result = verify_packet(args.packet)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
