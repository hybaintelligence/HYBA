"""Structured reporting helpers for replay verification diagnostics."""

from __future__ import annotations

import difflib
import html
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class VerificationReport:
    """Serializable replay/falsification/stress summary."""

    ok: bool
    operation: str
    claim_id: str
    message: str
    result: Mapping[str, Any] = field(default_factory=dict)
    error: str = ""
    diagnostics: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def unified_text_diff(
    expected: str, actual: str, *, fromfile: str = "expected", tofile: str = "actual"
) -> str:
    """Return a stable unified diff for human-readable diagnostics."""

    return "".join(
        difflib.unified_diff(
            expected.splitlines(keepends=True),
            actual.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )


def build_verification_report(
    *,
    ok: bool,
    operation: str,
    claim_id: str = "",
    message: str = "",
    result: Any = None,
    error: Exception | str | None = None,
    diagnostics: Mapping[str, Any] | None = None,
) -> VerificationReport:
    """Build a JSON/HTML-ready verification report."""

    if hasattr(result, "to_dict"):
        result_payload = result.to_dict()
    elif isinstance(result, Mapping):
        result_payload = dict(result)
    elif result is None:
        result_payload = {}
    else:
        result_payload = {"value": str(result)}
    error_text = "" if error is None else str(error)
    return VerificationReport(
        ok=ok,
        operation=operation,
        claim_id=claim_id or str(result_payload.get("claim_id", "")),
        message=message,
        result=result_payload,
        error=error_text,
        diagnostics=dict(diagnostics or {}),
    )


def write_report_json(report: VerificationReport, path: str | Path) -> None:
    Path(path).write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def write_report_html(report: VerificationReport, path: str | Path) -> None:
    payload = html.escape(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    status = "PASS" if report.ok else "FAIL"
    color = "#067d17" if report.ok else "#b00020"
    document = f"""<!doctype html>
<html><head><meta charset=\"utf-8\"><title>HYBA Replay Report</title></head>
<body><h1 style=\"color:{color}\">{status}: {html.escape(report.operation)}</h1>
<p><strong>Claim:</strong> {html.escape(report.claim_id)}</p>
<p>{html.escape(report.message)}</p>
<pre>{payload}</pre>
</body></html>
"""
    Path(path).write_text(document, encoding="utf-8")


__all__ = [
    "VerificationReport",
    "build_verification_report",
    "unified_text_diff",
    "write_report_html",
    "write_report_json",
]
