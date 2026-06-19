#!/usr/bin/env python3
"""Validate proactive claim-tier guardrails for external-facing materials."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TIERS = {"FORMALISM_VALIDATED", "PROTOTYPE_VALIDATED", "HYPOTHETICAL"}
REQUIRED_TEMPLATE_KEYS = {
    "claim",
    "tier",
    "evidence_file",
    "evidence_claim_id",
    "audience",
    "owner",
    "last_reviewed",
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise AssertionError(f"{path}: missing YAML-style claim-tier front matter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise AssertionError(f"{path}: front matter is not closed")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise AssertionError(f"{path}: malformed front matter line: {line!r}")
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def validate_template() -> None:
    template = ROOT / "docs" / "templates" / "external_claim_material.md"
    fields = parse_frontmatter(template)
    missing = REQUIRED_TEMPLATE_KEYS - set(fields)
    if missing:
        raise AssertionError(f"{template}: missing required keys {sorted(missing)}")
    if fields["tier"] not in ALLOWED_TIERS:
        raise AssertionError(f"{template}: invalid tier {fields['tier']!r}")
    evidence = ROOT / fields["evidence_file"]
    if not evidence.exists():
        raise AssertionError(f"{template}: evidence_file does not exist: {fields['evidence_file']}")
    manifest = json.loads(evidence.read_text(encoding="utf-8"))
    claim_ids = {claim["id"] for claim in manifest.get("claims", [])}
    if fields["evidence_claim_id"] not in claim_ids:
        raise AssertionError(
            f"{template}: evidence_claim_id {fields['evidence_claim_id']!r} missing from manifest"
        )


def validate_mining_manifest() -> None:
    manifest_path = ROOT / "docs" / "mining" / "evidence" / "mining_validation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "HYBA_MINING_VALIDATION_MANIFEST_V1"
    assert manifest["current_repository_state"] == "entangled_with_hyba_fullstack"
    assert manifest["standalone_repository"] is False
    assert manifest["independent_ci"] is False
    for claim in manifest["claims"]:
        if claim["tier"] not in ALLOWED_TIERS:
            raise AssertionError(f"{manifest_path}: invalid tier {claim['tier']!r}")
        text = json.dumps(claim).lower()
        for phrase in [
            "no guaranteed mining revenue claim",
            "no sha-256 quantum acceleration claim",
            "no antminer s21 superiority claim",
            "real_double_sha256_loop_pending",
        ]:
            if phrase not in text:
                raise AssertionError(f"{manifest_path}: missing mining boundary {phrase!r}")
        for rel_path in claim.get("evidence_files", []):
            if not (ROOT / rel_path).exists():
                raise AssertionError(f"{manifest_path}: missing evidence file {rel_path}")


def scan_external_materials() -> None:
    """Require front matter on markdown files under docs/external_materials when present."""
    external_dir = ROOT / "docs" / "external_materials"
    if not external_dir.exists():
        return
    for path in external_dir.rglob("*.md"):
        fields = parse_frontmatter(path)
        if fields.get("tier") not in ALLOWED_TIERS:
            raise AssertionError(f"{path}: invalid or missing tier")
        if not fields.get("evidence_claim_id"):
            raise AssertionError(f"{path}: missing evidence_claim_id")


def main() -> int:
    try:
        validate_template()
        validate_mining_manifest()
        scan_external_materials()
    except Exception as exc:  # noqa: BLE001 - CLI should print concise guardrail failure
        print(f"validation-claim-tier guard failed: {exc}", file=sys.stderr)
        return 1
    print("validation-claim-tier guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
