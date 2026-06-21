#!/usr/bin/env python3
"""Validate the enterprise production-readiness close-down evidence pack.

This gate is intentionally conservative. It verifies that each readiness gap has
an allowed status, that required implementation/evidence files exist, and that
external certifications are not represented as completed unless explicitly backed
by external evidence. It writes a JSON transcript to docs/governance so the final
close-down can be reviewed without re-running every command.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "docs" / "enterprise_gap_closure_status.json"
OUTPUT_FILE = ROOT / "docs" / "governance" / "enterprise_gap_closure_gate.json"

ALLOWED_STATUSES = {
    "closed_by_code",
    "closed_by_operational_control",
    "documented_but_external_dependency",
    "not_closed",
}

EXPECTED_GAPS = {
    "observability_monitoring",
    "security_compliance",
    "performance_scalability",
    "reliability_availability",
    "documentation_knowledge_management",
    "testing_quality_assurance",
    "cicd_deployment",
    "data_governance_privacy",
    "customer_experience",
    "financial_operations",
}

REQUIRED_FILES = [
    "python_backend/hyba_genesis_api/core/telemetry.py",
    "python_backend/hyba_genesis_api/core/api_posture.py",
    "python_backend/hyba_genesis_api/core/resilience.py",
    "tests/test_enterprise_telemetry_posture.py",
    "tests/test_enterprise_resilience.py",
    "docs/ENTERPRISE_GAP_CLOSURE_EVIDENCE_PACK.md",
    "docs/runbooks/OBSERVABILITY_AND_RELIABILITY.md",
    "docs/security/ENTERPRISE_SECURITY_BASELINE.md",
    "docs/compliance/SOC2_READINESS_EVIDENCE_MAP.md",
    "docs/privacy/DATA_GOVERNANCE_AND_PRIVACY.md",
    "docs/support/ENTERPRISE_CUSTOMER_EXPERIENCE.md",
    "docs/finops/ENTERPRISE_FINOPS.md",
]

FORBIDDEN_CLOSED_CERTIFICATION_PHRASES = [
    "soc2 certified",
    "soc 2 certified",
    "penetration test completed",
    "99.99% uptime guaranteed",
    "multi-region active-active completed",
]


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


def _load_status() -> dict[str, Any]:
    if not STATUS_FILE.exists():
        raise AssertionError(f"Missing status file: {STATUS_FILE.relative_to(ROOT)}")
    return json.loads(STATUS_FILE.read_text(encoding="utf-8"))


def _validate_status(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    gaps = payload.get("gaps")
    if not isinstance(gaps, list):
        return ["Status file must contain a list field named 'gaps'."]

    seen = set()
    for item in gaps:
        gap_id = item.get("id")
        status = item.get("status")
        seen.add(gap_id)
        if gap_id not in EXPECTED_GAPS:
            errors.append(f"Unexpected gap id: {gap_id}")
        if status not in ALLOWED_STATUSES:
            errors.append(f"Gap {gap_id} has invalid status {status!r}")
        evidence = item.get("evidence", [])
        if status in {"closed_by_code", "closed_by_operational_control"} and not evidence:
            errors.append(f"Gap {gap_id} is marked {status} without evidence entries")
        if status == "closed_by_code" and not any(str(entry).startswith(("python_backend/", "tests/", "scripts/")) for entry in evidence):
            errors.append(f"Gap {gap_id} is closed_by_code but has no code/test/script evidence")

    missing = EXPECTED_GAPS - seen
    if missing:
        errors.append(f"Missing gap statuses: {sorted(missing)}")
    return errors


def _validate_required_files() -> list[str]:
    return [path for path in REQUIRED_FILES if not (ROOT / path).exists()]


def _validate_claim_language() -> list[str]:
    errors: list[str] = []
    for path in [
        ROOT / "docs" / "ENTERPRISE_GAP_CLOSURE_EVIDENCE_PACK.md",
        ROOT / "docs" / "compliance" / "SOC2_READINESS_EVIDENCE_MAP.md",
    ]:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_CLOSED_CERTIFICATION_PHRASES:
            if phrase in text:
                errors.append(f"Forbidden unsupported certification claim {phrase!r} in {path.relative_to(ROOT)}")
    return errors


def main() -> int:
    transcript: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "status_file": str(STATUS_FILE.relative_to(ROOT)),
        "checks": {},
        "passed": False,
        "errors": [],
        "limitations": [
            "This gate validates repository evidence only.",
            "It does not certify SOC2, complete an external penetration test, or prove multi-region cloud deployment.",
            "Scientific and mathematical validation gates remain separate from enterprise engineering hardening.",
        ],
    }
    try:
        status_payload = _load_status()
        status_errors = _validate_status(status_payload)
    except Exception as exc:  # noqa: BLE001 - command-line gate must report all failure modes
        status_errors = [str(exc)]

    missing_files = _validate_required_files()
    claim_errors = _validate_claim_language()

    transcript["checks"] = {
        "status_file_valid": not status_errors,
        "required_files_present": not missing_files,
        "claim_language_conservative": not claim_errors,
        "expected_gap_count": len(EXPECTED_GAPS),
    }
    transcript["errors"] = status_errors + [f"Missing required file: {p}" for p in missing_files] + claim_errors
    transcript["passed"] = not transcript["errors"]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(transcript, indent=2, sort_keys=True))
    return 0 if transcript["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
