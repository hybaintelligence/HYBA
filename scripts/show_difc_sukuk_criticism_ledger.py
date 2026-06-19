#!/usr/bin/env python3
"""Render a scholar/compliance-facing criticism ledger from a DIFC Sukuk packet.

This script is deliberately read-only. It does not approve, issue, trade, book,
file, or submit anything. It translates an existing evidence packet into a
plain-text ledger for human SSSB / compliance review.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


NO_ACTION_BOUNDARY = (
    "READ-ONLY LEDGER: not a fatwa, Shariah ruling, legal opinion, regulatory "
    "determination, issuance approval, trade instruction, booking instruction, "
    "or external filing. Human SSSB/compliance authority remains sovereign."
)


def _status_label(status: str) -> str:
    normalized = str(status or "").upper()
    if normalized == "PASSED":
        return "PASS"
    if normalized == "FAILED":
        return "FAIL"
    if normalized == "WARNING":
        return "WARN"
    return normalized or "UNKNOWN"


def _load_packet(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError("Packet must be a JSON object.")
    return packet


def _overlay_findings(packet: Dict[str, Any]) -> List[Dict[str, Any]]:
    findings = packet.get("difc_aaiofi_findings") or packet.get("difc_aaoifi_findings") or []
    if not isinstance(findings, list):
        raise ValueError("Packet findings must be a list.")
    return [finding for finding in findings if isinstance(finding, dict)]


def _ledger_lines(packet: Dict[str, Any]) -> Iterable[str]:
    candidate = packet.get("candidate", {}) if isinstance(packet.get("candidate"), dict) else {}
    jurisdiction = (
        packet.get("jurisdiction_context", {})
        if isinstance(packet.get("jurisdiction_context"), dict)
        else {}
    )
    findings = _overlay_findings(packet)
    failed = [f for f in findings if str(f.get("status", "")).lower() == "failed"]
    warnings = [f for f in findings if str(f.get("status", "")).lower() == "warning"]

    yield "PYTHIA DIFC / AAOIFI SUKUK CRITICISM LEDGER"
    yield "=" * 55
    yield f"Packet hash: {packet.get('difc_aaiofi_packet_hash') or packet.get('difc_aaoifi_packet_hash') or 'MISSING'}"
    yield f"Schema: {packet.get('schema', 'UNKNOWN')}"
    yield f"Domain: {packet.get('domain', 'UNKNOWN')}"
    yield f"Verdict: {packet.get('verdict', 'UNKNOWN')}"
    yield f"Human review required: {packet.get('human_review_required', 'UNKNOWN')}"
    yield f"Automatic action allowed: {packet.get('automatic_action_allowed', 'UNKNOWN')}"
    yield ""
    yield "Candidate"
    yield "---------"
    yield f"ID: {candidate.get('candidate_id', 'UNKNOWN')}"
    yield f"Type: {candidate.get('sukuk_type', 'UNKNOWN')}"
    yield f"Lifecycle stage: {candidate.get('lifecycle_stage', 'UNKNOWN')}"
    yield f"Purpose: {candidate.get('purpose', 'UNKNOWN')}"
    yield ""
    yield "Jurisdiction / review tags"
    yield "--------------------------"
    yield f"Jurisdiction: {jurisdiction.get('jurisdiction', 'UNKNOWN')}"
    yield f"Regulator: {jurisdiction.get('regulator', 'UNKNOWN')}"
    yield f"Standard tags: {', '.join(jurisdiction.get('standard_tags', [])) if isinstance(jurisdiction.get('standard_tags'), list) else 'UNKNOWN'}"
    yield ""
    yield "Finding summary"
    yield "---------------"
    yield f"Total findings: {len(findings)}"
    yield f"Failed blockers: {len(failed)}"
    yield f"Warnings: {len(warnings)}"
    yield ""
    yield "Criticism trail"
    yield "---------------"
    for idx, finding in enumerate(findings, start=1):
        yield f"{idx}. [{_status_label(finding.get('status', ''))}] {finding.get('name', finding.get('finding_id', 'UNKNOWN'))}"
        yield f"   Severity: {finding.get('severity', 'UNKNOWN')}"
        yield f"   Review tag: {finding.get('standard_reference', 'UNSPECIFIED')}"
        yield f"   Human owner: {finding.get('human_owner', 'UNSPECIFIED')}"
        yield f"   Reasoning: {finding.get('reasoning', 'UNSPECIFIED')}"
        yield ""
    yield "Boundary"
    yield "--------"
    yield packet.get("claim_boundary", NO_ACTION_BOUNDARY)
    yield NO_ACTION_BOUNDARY


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a read-only DIFC Sukuk criticism ledger.")
    parser.add_argument(
        "packet", type=Path, help="Path to a generated DIFC Sukuk evidence packet JSON file."
    )
    parser.add_argument(
        "--output", type=Path, default=None, help="Optional path for the rendered ledger text."
    )
    args = parser.parse_args()

    packet = _load_packet(args.packet)
    rendered = "\n".join(_ledger_lines(packet)) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
