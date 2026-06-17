"""Read-only criticism ledger renderer for DIFC / AAOIFI Sukuk packets.

The renderer converts generated evidence packets or lifecycle simulations into a
human-readable Markdown ledger for Shariah scholars, SSSB members, trustees,
compliance officers, counsel, or regulator-authorised reviewers.

Boundary: presentation only. The ledger produces text for human review and does
not perform external actions.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

LEDGER_SCHEMA_VERSION = "PYTHIA_DIFC_AAOIFI_CRITICISM_LEDGER_V1"


def _cell(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def _finding_rows(findings: Iterable[Mapping[str, Any]]) -> list[str]:
    rows = ["| Finding | Status | Severity | Human owner | Review tag |", "|---|---:|---:|---|---|"]
    for finding in findings:
        rows.append(
            "| {finding_id} | {status} | {severity} | {owner} | {tag} |".format(
                finding_id=_cell(finding.get("finding_id")),
                status=_cell(finding.get("status")),
                severity=_cell(finding.get("severity")),
                owner=_cell(finding.get("human_owner")),
                tag=_cell(finding.get("standard_reference")),
            )
        )
    return rows


def render_packet_ledger(packet: Mapping[str, Any]) -> str:
    """Render one DIFC / AAOIFI Sukuk evidence packet as Markdown."""

    candidate = packet.get("candidate", {}) if isinstance(packet.get("candidate", {}), Mapping) else {}
    findings = packet.get("difc_aaiofi_findings", [])
    failed = [finding for finding in findings if finding.get("status") == "failed"]
    warnings = [finding for finding in findings if finding.get("status") == "warning"]

    lines = [
        "# PYTHIA DIFC / AAOIFI Read-Only Criticism Ledger",
        "",
        f"**Ledger schema:** `{LEDGER_SCHEMA_VERSION}`  ",
        f"**Packet schema:** `{_cell(packet.get('schema'))}`  ",
        f"**Domain:** {_cell(packet.get('domain'))}  ",
        f"**Candidate:** `{_cell(candidate.get('candidate_id'))}` / `{_cell(candidate.get('sukuk_type'))}`  ",
        f"**Lifecycle stage:** `{_cell(candidate.get('lifecycle_stage'))}`  ",
        f"**Verdict:** `{_cell(packet.get('verdict'))}`  ",
        f"**Human review required:** `{str(packet.get('human_review_required')).lower()}`  ",
        f"**Automatic action allowed:** `{str(packet.get('automatic_action_allowed')).lower()}`  ",
        f"**Action:** `ESCALATE_TO_SOVEREIGN_HUMAN`  ",
        f"**Packet hash:** `{_cell(packet.get('difc_aaiofi_packet_hash'))}`",
        "",
        "> Presentation only. This ledger is a human-review aid, not a legal, regulatory, religious, capital, investment, credit, or operational decision.",
        "",
        "## Finding summary",
        "",
        f"- Failed findings: `{len(failed)}`",
        f"- Warning findings: `{len(warnings)}`",
        f"- Total findings: `{len(findings)}`",
        "",
        "## Findings",
        "",
    ]
    lines.extend(_finding_rows(findings))
    lines.extend(["", "## Criticism details", ""])
    for finding in findings:
        lines.extend(
            [
                f"### `{_cell(finding.get('finding_id'))}`",
                "",
                f"- Status: `{_cell(finding.get('status'))}`",
                f"- Severity: `{_cell(finding.get('severity'))}`",
                f"- Human owner: {_cell(finding.get('human_owner'))}",
                f"- Review tag: {_cell(finding.get('standard_reference'))}",
                f"- Reasoning: {_cell(finding.get('reasoning'))}",
                "",
            ]
        )
    lines.extend(["## Recommended next action", "", _cell(packet.get("recommended_next_action")), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_lifecycle_ledger(bundle: Mapping[str, Any]) -> str:
    """Render a lifecycle simulation bundle as a board-facing Markdown ledger."""

    timeline = bundle.get("timeline", [])
    summary = bundle.get("summary", {}) if isinstance(bundle.get("summary", {}), Mapping) else {}
    lines = [
        "# PYTHIA DIFC / AAOIFI Sukuk Lifecycle Criticism Ledger",
        "",
        f"**Ledger schema:** `{LEDGER_SCHEMA_VERSION}`  ",
        f"**Simulation schema:** `{_cell(bundle.get('schema'))}`  ",
        f"**Domain:** {_cell(bundle.get('domain'))}  ",
        f"**Lifecycle hash:** `{_cell(bundle.get('lifecycle_packet_hash'))}`  ",
        f"**Human review required:** `{str(bundle.get('human_review_required')).lower()}`  ",
        f"**Automatic action allowed:** `{str(bundle.get('automatic_action_allowed')).lower()}`",
        "",
        "> Read-only lifecycle evidence. The simulation escalates findings to sovereign human review and performs no external action.",
        "",
        "## Summary",
        "",
        f"- Total steps: `{_cell(summary.get('total_steps'))}`",
        f"- Warning steps: `{_cell(summary.get('warning_steps'))}`",
        f"- Blocker steps: `{_cell(summary.get('blocker_steps'))}`",
        f"- First warning step: `{_cell(summary.get('first_warning_step_id'))}`",
        f"- First blocker step: `{_cell(summary.get('first_blocker_step_id'))}` / `{_cell(summary.get('first_blocker_stage'))}`",
        "",
        "## Lifecycle table",
        "",
        "| Step | Stage | Verdict | Warnings | Failures | Action |",
        "|---:|---|---|---|---|---|",
    ]
    for entry in timeline:
        lines.append(
            "| {step} | {stage} | {verdict} | {warnings} | {failures} | {action} |".format(
                step=_cell(entry.get("step_id")),
                stage=_cell(entry.get("lifecycle_stage")),
                verdict=_cell(entry.get("verdict")),
                warnings=_cell(", ".join(entry.get("warning_findings", [])) if entry.get("warning_findings") else "-"),
                failures=_cell(", ".join(entry.get("failed_findings", [])) if entry.get("failed_findings") else "-"),
                action=_cell(entry.get("action")),
            )
        )
    lines.extend(["", "## Step details", ""])
    for entry in timeline:
        lines.extend(
            [
                f"### Step `{_cell(entry.get('step_id'))}` — {_cell(entry.get('lifecycle_stage'))}",
                "",
                f"- Candidate: `{_cell(entry.get('candidate_id'))}`",
                f"- Review focus: {_cell(entry.get('review_focus'))}",
                f"- Verdict: `{_cell(entry.get('verdict'))}`",
                f"- Packet hash: `{_cell(entry.get('packet_hash'))}`",
                f"- Warning findings: {_cell(', '.join(entry.get('warning_findings', [])) if entry.get('warning_findings') else '-')}",
                f"- Failed findings: {_cell(', '.join(entry.get('failed_findings', [])) if entry.get('failed_findings') else '-')}",
                "",
            ]
        )
    lines.extend(["## Recommended next action", "", _cell(bundle.get("recommended_next_action")), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_criticism_ledger(data: Mapping[str, Any]) -> str:
    """Render either a single packet or lifecycle bundle."""

    if "timeline" in data:
        return render_lifecycle_ledger(data)
    return render_packet_ledger(data)


__all__ = [
    "LEDGER_SCHEMA_VERSION",
    "render_criticism_ledger",
    "render_lifecycle_ledger",
    "render_packet_ledger",
]
