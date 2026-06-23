#!/usr/bin/env python3
"""Validate that all review-gap closures needed for a first customer pilot exist.

This is a static repository gate. It proves that internal artifacts, code paths,
and validation hooks are present; it deliberately does not claim external customer
acceptance, regulatory certification, or live revenue.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "review_gap_closure_registry.json"


def _load_registry() -> dict[str, Any]:
    with REGISTRY.open(encoding="utf-8") as fh:
        return json.load(fh)


def _path_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def _validate_enterprise_telemetry_bridge(
    registry: dict[str, Any], errors: list[str]
) -> None:
    """Assert the Phase 3.5 bridge is wired into the first-customer gate."""
    bridge_review = next(
        (
            review
            for review in registry.get("reviews", [])
            if review.get("id") == "phase_3_5_enterprise_telemetry_bridge"
        ),
        None,
    )
    if not bridge_review:
        errors.append("Missing phase_3_5_enterprise_telemetry_bridge review track.")
        return

    required_paths = set(bridge_review.get("required_paths", []))
    for rel_path in [
        "reproducibility/benchmarks/telemetry_bridge.py",
        "reproducibility/benchmarks/test_mckinsey_additions.py",
    ]:
        if rel_path not in required_paths:
            errors.append(
                f"phase_3_5_enterprise_telemetry_bridge: {rel_path} must be required."
            )

    expected_outputs = {
        "sla_report",
        "chargeback_report",
        "retention_curve",
        "risk_count",
        "weekly_ops_review",
        "quarterly_deck",
    }
    configured_outputs = set(bridge_review.get("expected_bridge_outputs", []))
    missing_outputs = sorted(expected_outputs - configured_outputs)
    if missing_outputs:
        errors.append(
            "phase_3_5_enterprise_telemetry_bridge: missing expected bridge outputs "
            + ", ".join(missing_outputs)
        )

    bridge_source = ROOT / "reproducibility/benchmarks/telemetry_bridge.py"
    if bridge_source.exists():
        source_text = bridge_source.read_text(encoding="utf-8")
        for output in expected_outputs:
            if f'"{output}"' not in source_text:
                errors.append(
                    f"telemetry_bridge.py does not statically expose {output}."
                )

    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from telemetry_bridge import EnterpriseTelemetryBridge\n"
                "out = EnterpriseTelemetryBridge().ingest_snapshot({\n"
                "  'timestamp': '2026-06-20T00:00:00Z',\n"
                "  'period': 'gate-smoke',\n"
                "  'sla': {'availability': 0.999, 'latency_p99': 125},\n"
                "  'costs': [{'service_id': 'qaas-api', 'department': 'platform', 'vcpu_hours': 1}],\n"
                "  'cohorts': [{'cohort_id': 'gate', 'initial_size': 1, 'month': 1, 'metrics': {'retained_customers': 1}}],\n"
                "  'incidents': [{'category': 'operational', 'severity': 'medium'}],\n"
                "  'customers': {'customer_count': 1},\n"
                "})\n"
                f"missing = {sorted(expected_outputs)!r}\n"
                "missing = [key for key in missing if key not in out]\n"
                "raise SystemExit('missing bridge outputs: ' + ', '.join(missing) if missing else 0)\n"
            ),
        ],
        cwd=ROOT / "reproducibility/benchmarks",
        text=True,
        capture_output=True,
    )
    if smoke.returncode != 0:
        errors.append(
            "EnterpriseTelemetryBridge smoke validation failed with "
            f"{smoke.returncode}: {smoke.stderr or smoke.stdout}"
        )


def main() -> int:
    errors: list[str] = []
    registry = _load_registry()

    if "external" not in registry.get("claim_boundary", ""):
        errors.append(
            "Registry claim_boundary must explicitly distinguish internal closure from external validation."
        )

    reviews = registry.get("reviews", [])
    if not reviews:
        errors.append("Registry must contain at least one review entry.")

    for review in reviews:
        review_id = review.get("id", "<unknown>")
        total = int(review.get("total_count", 0))
        closed = int(review.get("closed_count", -1))
        if total <= 0 or closed < total:
            errors.append(
                f"{review_id}: closed_count must be >= total_count and total_count must be positive."
            )
        if not review.get("remaining_external_gaps"):
            errors.append(
                f"{review_id}: remaining external gaps must be listed to prevent over-claiming."
            )
        for rel_path in review.get("required_paths", []):
            if not _path_exists(rel_path):
                errors.append(f"{review_id}: missing required path {rel_path}")

    _validate_enterprise_telemetry_bridge(registry, errors)

    # Run the two authoritative static gates that are fast and environment-local.
    for command in [
        [sys.executable, "scripts/check_institutional_qaas_gap_closure.py"],
        [sys.executable, "scripts/check_forensic_gap_closure.py"],
    ]:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if result.returncode != 0:
            errors.append(
                f"Command {' '.join(command)} failed with {result.returncode}: {result.stderr or result.stdout}"
            )

    if errors:
        print("First-customer readiness gate failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(
        "✓ First-customer readiness gate passed: all review-gap closure artifacts are present and claim-bounded."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
