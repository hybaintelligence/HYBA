#!/usr/bin/env python3
"""Validate proactive claim-tier guardrails for external-facing materials.

The guard intentionally treats external messaging as a production surface: claims,
slides, emails, and exports must be evidence-bound before distribution.  The
parser is deliberately small and dependency-free so it can run in CI before the
normal application dependency graph is installed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TIERS = {"FORMALISM_VALIDATED", "PROTOTYPE_VALIDATED", "HYPOTHETICAL"}
BOOLEAN_TRUE = {"true", "yes", "1"}
EXPORT_SUFFIXES = {".pptx", ".pdf", ".docx", ".eml", ".html"}

REQUIRED_TEMPLATE_KEYS = {
    "claim",
    "tier",
    "evidence_file",
    "evidence_claim_id",
    "audience",
    "channel",
    "owner",
    "last_reviewed",
    "review_status",
    "approved_by",
    "external_distribution",
}

REQUIRED_EXTERNAL_KEYS = REQUIRED_TEMPLATE_KEYS | {"distribution_boundary"}


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
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields


def _load_manifest(evidence_file: str, source_path: Path) -> dict[str, Any]:
    evidence = ROOT / evidence_file
    if not evidence.exists():
        raise AssertionError(f"{source_path}: evidence_file does not exist: {evidence_file}")
    try:
        return json.loads(evidence.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{source_path}: evidence manifest is not valid JSON: {evidence_file}") from exc


def _claim_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {claim["id"]: claim for claim in manifest.get("claims", []) if "id" in claim}


def _validate_required_fields(path: Path, fields: dict[str, str], required: set[str]) -> None:
    missing = required - set(fields)
    if missing:
        raise AssertionError(f"{path}: missing required front matter keys {sorted(missing)}")
    if fields["tier"] not in ALLOWED_TIERS:
        raise AssertionError(f"{path}: invalid tier {fields['tier']!r}")


def _validate_manifest_binding(path: Path, fields: dict[str, str], *, require_tier_match: bool) -> None:
    manifest = _load_manifest(fields["evidence_file"], path)
    claims = _claim_index(manifest)
    claim_id = fields["evidence_claim_id"]
    if claim_id not in claims:
        raise AssertionError(f"{path}: evidence_claim_id {claim_id!r} missing from manifest")
    manifest_claim = claims[claim_id]
    manifest_tier = manifest_claim.get("tier")
    if require_tier_match:
        if manifest_tier not in ALLOWED_TIERS:
            raise AssertionError(f"{path}: manifest claim {claim_id!r} must declare one of {sorted(ALLOWED_TIERS)}")
        if fields["tier"] != manifest_tier:
            raise AssertionError(
                f"{path}: claim tier {fields['tier']!r} does not match manifest tier {manifest_tier!r} for {claim_id!r}"
            )
    boundaries = manifest_claim.get("boundaries") or manifest_claim.get("boundary") or []
    if not boundaries:
        raise AssertionError(f"{path}: manifest claim {claim_id!r} must list explicit boundaries")
    reproduction = (
        manifest_claim.get("reproduction_command")
        or manifest_claim.get("required_to_promote")
        or manifest_claim.get("commands")
    )
    if not reproduction:
        raise AssertionError(f"{path}: manifest claim {claim_id!r} must include commands, reproduction_command, or required_to_promote")


def _external_distribution_requested(fields: dict[str, str]) -> bool:
    return fields.get("external_distribution", "").strip().lower() in BOOLEAN_TRUE


def validate_template() -> None:
    template = ROOT / "docs" / "templates" / "external_claim_material.md"
    fields = parse_frontmatter(template)
    _validate_required_fields(template, fields, REQUIRED_TEMPLATE_KEYS)
    # The template may bind to the legacy general evidence manifest, where older
    # implemented claims use status/commands instead of tier. Actual external
    # materials below must bind to a manifest claim with an explicit tier.
    _validate_manifest_binding(template, fields, require_tier_match=False)
    if _external_distribution_requested(fields):
        raise AssertionError(f"{template}: template must remain external_distribution=false")


def validate_mining_manifest() -> None:
    manifest_path = ROOT / "docs" / "mining" / "evidence" / "mining_validation_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema"] == "HYBA_MINING_VALIDATION_MANIFEST_V1"
    assert manifest["current_repository_state"] == "entangled_with_hyba_fullstack"
    assert manifest["standalone_repository"] is False
    assert manifest["independent_ci"] is False
    assert manifest.get("commercialization_stage") == "stage_0_pre_validation_research_only"
    for claim in manifest["claims"]:
        if claim["tier"] not in ALLOWED_TIERS:
            raise AssertionError(f"{manifest_path}: invalid tier {claim['tier']!r}")
        text = json.dumps(claim).lower()
        for phrase in [
            "no guaranteed mining revenue claim",
            "no sha-256 quantum acceleration claim",
            "no antminer s21 superiority claim",
            "real_double_sha256_loop_pending",
            "no commercialization before stage 2",
        ]:
            if phrase not in text:
                raise AssertionError(f"{manifest_path}: missing mining boundary {phrase!r}")
        for rel_path in claim.get("evidence_files", []):
            if not (ROOT / rel_path).exists():
                raise AssertionError(f"{manifest_path}: missing evidence file {rel_path}")


def _is_protocol_doc(path: Path) -> bool:
    return path.name.upper().startswith("README") or path.name.startswith("_")


def scan_external_materials() -> None:
    """Require evidence-bound approval on markdown files under docs/external_materials."""
    external_dir = ROOT / "docs" / "external_materials"
    if not external_dir.exists():
        return
    for path in external_dir.rglob("*.md"):
        if _is_protocol_doc(path):
            continue
        fields = parse_frontmatter(path)
        _validate_required_fields(path, fields, REQUIRED_EXTERNAL_KEYS)
        _validate_manifest_binding(path, fields, require_tier_match=True)
        if not _external_distribution_requested(fields):
            raise AssertionError(f"{path}: external materials must set external_distribution=true after approval")
        if fields.get("review_status") != "approved_for_external_use":
            raise AssertionError(f"{path}: review_status must be approved_for_external_use")
        if fields.get("approved_by", "").lower() in {"", "tbd", "pending", "none"}:
            raise AssertionError(f"{path}: approved_by must identify the accountable reviewer")


def scan_external_exports() -> None:
    """Prevent decks/emails/PDF exports without approved markdown source."""
    external_dir = ROOT / "docs" / "external_materials"
    if not external_dir.exists():
        return
    for path in external_dir.rglob("*"):
        if path.suffix.lower() not in EXPORT_SUFFIXES:
            continue
        source = path.with_suffix(".md")
        if not source.exists():
            raise AssertionError(f"{path}: exported material must have same-stem approved markdown source")
        fields = parse_frontmatter(source)
        if fields.get("review_status") != "approved_for_external_use" or not _external_distribution_requested(fields):
            raise AssertionError(f"{path}: source markdown is not approved for external distribution")


def main() -> int:
    try:
        validate_template()
        validate_mining_manifest()
        scan_external_materials()
        scan_external_exports()
    except Exception as exc:  # noqa: BLE001 - CLI should print concise guardrail failure
        print(f"validation-claim-tier guard failed: {exc}", file=sys.stderr)
        return 1
    print("validation-claim-tier guard passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
