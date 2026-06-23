#!/usr/bin/env python3
"""Generate a repository evidence-boundary report.

This scanner distinguishes implemented protocol/governance capability from
artifact-backed operational evidence. It is passive: it only reads local JSON
artifacts and emits a structured report.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "evidence_boundary" / "latest.json"


@dataclass(frozen=True)
class EvidenceCheck:
    name: str
    status: str
    summary: str
    evidence_path: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceBoundaryReport:
    schema: str
    generated_at_utc: str
    status: str
    passed: bool
    checks: list[EvidenceCheck]
    claim_boundaries: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [asdict(check) for check in self.checks]
        return payload


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _scan_for_acceptance_marker(payload: Any) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in {"accepted", "accepted_share", "pool_ack"} and value is True:
                return True
            if (
                lowered
                in {"shares_accepted", "accepted_shares", "accepted_share_count"}
                and _as_int(value) > 0
            ):
                return True
            if _scan_for_acceptance_marker(value):
                return True
    elif isinstance(payload, list):
        return any(_scan_for_acceptance_marker(item) for item in payload)
    return False


def check_session_stats(root: Path = ROOT) -> EvidenceCheck:
    path = root / "logs" / "braiins_session_stats.json"
    payload = _load_json(path)
    if payload is None:
        return EvidenceCheck(
            name="session_stats",
            status="missing",
            summary="No session statistics artifact found.",
            evidence_path=str(path.relative_to(root)),
        )
    accepted = _as_int(payload.get("shares_accepted") or payload.get("accepted_shares"))
    return EvidenceCheck(
        name="session_stats",
        status="pass" if accepted > 0 else "warning",
        summary=(
            "Session statistics include acceptance evidence."
            if accepted > 0
            else "Session statistics exist but do not prove acceptance evidence."
        ),
        evidence_path=str(path.relative_to(root)),
        detail={
            "connected": bool(payload.get("connected")),
            "jobs_received": _as_int(payload.get("jobs_received")),
            "shares_submitted": _as_int(payload.get("shares_submitted")),
            "shares_accepted": accepted,
            "errors": payload.get("errors", []),
        },
    )


def check_gate_output(root: Path = ROOT) -> EvidenceCheck:
    path = root / "artifacts" / "production_gate_output.json"
    payload = _load_json(path)
    if payload is None:
        return EvidenceCheck(
            name="production_gate_output",
            status="missing",
            summary="No production gate output artifact found.",
            evidence_path=str(path.relative_to(root)),
        )
    has_marker = _scan_for_acceptance_marker(payload)
    return EvidenceCheck(
        name="production_gate_output",
        status="pass" if has_marker else "warning",
        summary=(
            "Production gate artifact includes acceptance evidence."
            if has_marker
            else "Production gate artifact does not include acceptance evidence."
        ),
        evidence_path=str(path.relative_to(root)),
        detail={"acceptance_evidence_present": has_marker},
    )


def check_clean_gate(root: Path = ROOT) -> EvidenceCheck:
    path = root / "artifacts" / "clean_10" / "latest.json"
    payload = _load_json(path)
    if payload is None:
        return EvidenceCheck(
            name="clean_10_gate",
            status="missing",
            summary="No local clean evidence gate artifact found.",
            evidence_path=str(path.relative_to(root)),
        )
    passed = bool(payload.get("passed"))
    return EvidenceCheck(
        name="clean_10_gate",
        status="pass" if passed else "fail",
        summary=(
            "Local clean evidence gate passed."
            if passed
            else "Local clean evidence gate has failures."
        ),
        evidence_path=str(path.relative_to(root)),
        detail={
            "status": payload.get("status"),
            "required_failures": payload.get("required_failures", []),
        },
    )


def generate_report(root: Path = ROOT) -> EvidenceBoundaryReport:
    checks = [
        check_session_stats(root),
        check_gate_output(root),
        check_clean_gate(root),
    ]
    acceptance_evidenced = any(
        check.status == "pass"
        and (
            check.detail.get("shares_accepted", 0) > 0
            or check.detail.get("acceptance_evidence_present") is True
        )
        for check in checks
    )
    clean_gate_failed = any(
        check.name == "clean_10_gate" and check.status == "fail" for check in checks
    )
    passed = acceptance_evidenced and not clean_gate_failed
    return EvidenceBoundaryReport(
        schema="HYBA_REPOSITORY_EVIDENCE_BOUNDARY_V1",
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        status="GO" if passed else "NO_GO",
        passed=passed,
        checks=checks,
        claim_boundaries=[
            "Protocol correctness, validation, governance and auditability may be claimed from code and test evidence.",
            "Operational acceptance, economic performance and advantage claims require acceptance artifacts.",
            "Synthetic or local benchmark evidence must be labelled as synthetic/local benchmark evidence.",
        ],
        next_actions=(
            ["Archive this report with the clean gate and runtime bootstrap artifacts."]
            if passed
            else [
                "Resolve missing or warning evidence checks before making unqualified operational claims.",
                "Resolve any local clean evidence gate failures before describing the repo as clean.",
            ]
        ),
    )


def write_report(report: EvidenceBoundaryReport, output: Path = DEFAULT_OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".tmp")
    tmp.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8"
    )
    tmp.replace(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate repository evidence-boundary report."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = generate_report(ROOT)
    path = write_report(report, args.output)
    print(
        json.dumps(
            {**report.to_dict(), "artifact_path": str(path)}, indent=2, sort_keys=True
        )
    )
    return 0 if report.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
