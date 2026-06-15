#!/usr/bin/env python3
"""Fast integrity gate for the HYBA benchmark portfolio.

This validates portfolio documentation and, when a saved JSON report is present,
checks that reported benchmark values stay inside expected technical bounds. It
intentionally does not run the full benchmark suite because historical block
analysis can be network-bound and slow.

A saved report is invalid when any component script failed or timed out. This
keeps the dashboard/report layer aligned with the actual benchmark run status.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = ROOT / "benchmark_portfolio"
REQUIRED_DOCS = ("README.md", "TOPOLOGICAL_SCALING.md")
OPTIONAL_FILES = (
    "index.html",
    "run_benchmarks.py",
    "run_output/portfolio_report.json",
    "run_output/PORTFOLIO_SUMMARY.md",
)


def exists(rel: str) -> dict[str, object]:
    path = PORTFOLIO / rel
    return {"name": rel, "passed": path.exists(), "detail": "present" if path.exists() else "missing"}


def find_number(payload: Any, names: set[str]) -> float | None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalised = key.lower().replace("-", "_").replace(" ", "_")
            if normalised in names and isinstance(value, (int, float)):
                return float(value)
        for value in payload.values():
            found = find_number(value, names)
            if found is not None:
                return found
    if isinstance(payload, list):
        for item in payload:
            found = find_number(item, names)
            if found is not None:
                return found
    return None


def completion_checks(payload: dict[str, Any]) -> list[dict[str, object]]:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    results = payload.get("scripts_results", [])
    failed = int(summary.get("failed", 0) or 0)
    timed_out = int(summary.get("timed_out", 0) or 0)
    skipped = int(summary.get("skipped", 0) or 0)
    total = int(summary.get("total_scripts", len(results)) or 0)
    passed_count = int(summary.get("passed", 0) or 0)

    incomplete = []
    if isinstance(results, list):
        for item in results:
            if isinstance(item, dict) and str(item.get("status", "")).upper() != "PASSED":
                incomplete.append({"script": item.get("script"), "status": item.get("status")})

    ok = failed == 0 and timed_out == 0 and skipped == 0 and passed_count == total and not incomplete
    return [{
        "name": "script_completion",
        "passed": ok,
        "detail": {
            "total": total,
            "passed": passed_count,
            "failed": failed,
            "timed_out": timed_out,
            "skipped": skipped,
            "incomplete": incomplete,
        },
    }]


def claim_checks() -> list[dict[str, object]]:
    report_path = PORTFOLIO / "run_output" / "portfolio_report.json"
    if not report_path.exists():
        return [{"name": "portfolio_report", "passed": True, "detail": "optional saved report absent"}]

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [{"name": "portfolio_report_json", "passed": False, "detail": str(exc)}]

    checks: list[dict[str, object]] = []
    checks.extend(completion_checks(payload))

    resonance = find_number(payload, {"resonance", "resonance_rate", "phi15_resonance", "phi_15_resonance", "resonance_percent", "phi_resonance_rate"})
    if resonance is not None:
        normalised = resonance / 100.0 if resonance > 1.0 else resonance
        checks.append({"name": "phi15_resonance", "passed": 0.5 <= normalised <= 1.0, "detail": resonance})

    z_score = find_number(payload, {"z", "z_score", "zscore", "phi_resonance_z_score"})
    if z_score is not None:
        checks.append({"name": "phi15_z_score", "passed": z_score >= 3.0, "detail": z_score})

    corr = find_number(payload, {"hash_correlation", "sha_correlation", "validity_correlation", "correlation", "r"})
    if corr is not None:
        checks.append({"name": "hash_validity_boundary", "passed": abs(corr) <= 0.10, "detail": corr})

    advantage = find_number(payload, {"advantage", "grover_advantage", "advantage_over_grover", "structured_advantage"})
    if advantage is not None:
        checks.append({"name": "structured_advantage", "passed": advantage > 1.0, "detail": advantage})

    if len(checks) == 1:
        checks.append({"name": "portfolio_report_shape", "passed": True, "detail": "parsed without standard metric keys"})
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate benchmark portfolio integrity")
    parser.add_argument("--strict-optional", action="store_true")
    args = parser.parse_args()

    required = [exists(rel) for rel in REQUIRED_DOCS]
    optional = [exists(rel) for rel in OPTIONAL_FILES]
    claims = claim_checks()

    required_ok = all(item["passed"] for item in required)
    optional_ok = all(item["passed"] for item in optional) if args.strict_optional else True
    claims_ok = all(item["passed"] for item in claims)
    passed = required_ok and optional_ok and claims_ok

    result = {
        "status": "passed" if passed else "blocked",
        "passed": passed,
        "required_docs": required,
        "optional_files": optional,
        "saved_report_checks": claims,
        "doctrine": {
            "runs_full_benchmarks": False,
            "validates_saved_portfolio": True,
            "topological_scaling_doc_required": True,
            "failed_scripts_block_saved_report": True,
        },
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
