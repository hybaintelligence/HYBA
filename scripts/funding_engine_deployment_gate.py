#!/usr/bin/env python3
"""HYBA_FULLSTACK funding-engine deployment gate.

This gate is intentionally local and deterministic. It does not connect to pools,
does not submit shares, and does not infer revenue. It verifies the funding-engine
preconditions that must hold before the command room treats HYBA_FULLSTACK as
ready for live accepted-share capture:

1. Phi empirical evidence artifacts are present and schema-valid.
2. Deterministic PYTHIA search returns the same nonce for the same target/range.
3. Optional: an accepted-share artifact exists before MD-offer release.

The output is a timestamped JSON packet under artifacts/funding_engine/.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

REQUIRED_CSV_FIELDS = {
    "height",
    "timestamp",
    "nonce",
    "diff",
    "precision_pct",
    "resonance_strength",
}

SECRET_KEYWORDS = ("password", "secret", "token", "key", "jwt")


@dataclass
class GateCheck:
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FundingGateReport:
    status: str
    generated_at_utc: str
    repository: str
    mode: str
    checks: list[GateCheck]
    next_actions: list[str]
    environment: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _redact_env() -> dict[str, str]:
    visible_prefixes = ("HYBA_", "NODE_ENV", "PYTHONPATH")
    result: dict[str, str] = {}
    for key, value in sorted(os.environ.items()):
        if not key.startswith(visible_prefixes):
            continue
        if any(word in key.lower() for word in SECRET_KEYWORDS):
            result[key] = "<redacted>"
        else:
            result[key] = value[:160]
    return result


def _load_summary_payload(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("summary JSON must contain an object")
    return payload


def _summary_values(payload: dict[str, Any]) -> dict[str, Any]:
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return summary
    return payload


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def check_phi_resonance_artifacts(phi_dir: Path) -> GateCheck:
    csv_path = phi_dir / "phi_resonance_blocks.csv"
    json_path = phi_dir / "phi_resonance_summary.json"
    details: dict[str, Any] = {
        "phi_dir": str(phi_dir),
        "csv_path": str(csv_path),
        "json_path": str(json_path),
        "accepted_schemas": [
            "legacy_mean_resonance_strength",
            "phi15_100block_summary",
            "computed_from_csv",
        ],
    }

    if not csv_path.exists() or not json_path.exists():
        missing = [str(p) for p in (csv_path, json_path) if not p.exists()]
        details["missing"] = missing
        return GateCheck(
            name="phi_resonance_artifacts",
            status="failed",
            details=details,
        )

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        rows = list(reader)

    missing_fields = sorted(REQUIRED_CSV_FIELDS - fieldnames)
    details["csv_rows"] = len(rows)
    details["csv_fields"] = sorted(fieldnames)
    if missing_fields:
        details["missing_csv_fields"] = missing_fields
        return GateCheck("phi_resonance_artifacts", "failed", details)
    if not rows:
        details["error"] = "CSV has no block rows"
        return GateCheck("phi_resonance_artifacts", "failed", details)

    strengths: list[float] = []
    for row in rows:
        try:
            value = float(row.get("resonance_strength", ""))
        except ValueError:
            details["error"] = "CSV contains non-numeric resonance_strength"
            return GateCheck("phi_resonance_artifacts", "failed", details)
        if value < 0.0 or value > 1.0:
            details["error"] = "CSV resonance_strength outside [0, 1]"
            details["bad_value"] = value
            return GateCheck("phi_resonance_artifacts", "failed", details)
        strengths.append(value)

    payload = _load_summary_payload(json_path)
    values = _summary_values(payload)
    details["summary_fields"] = sorted(values.keys())

    computed_mean = sum(strengths) / len(strengths)
    computed_above = sum(1 for item in strengths if item >= 0.5)
    computed_rate = computed_above / len(strengths)
    total_blocks = _safe_int(
        _first_present(values, "total_blocks", "blocks", "csv_rows"), len(rows)
    )
    reported_mean = _first_present(
        values, "mean_resonance_strength", "mean_phi_resonance"
    )
    reported_above_count = _first_present(
        values,
        "resonance_above_05_count",
        "phi_resonant_count",
        "phi15_resonant_count",
    )
    reported_rate = _first_present(
        values,
        "resonance_above_05_rate",
        "phi_resonance_rate",
        "phi15_resonance_rate",
    )
    z_score = _first_present(values, "z_score_vs_random", "z_score")
    p_value = _first_present(values, "p_value_binomial", "p_value")

    details.update(
        {
            "computed_mean_resonance_strength": round(computed_mean, 8),
            "computed_resonance_above_05_count": computed_above,
            "computed_resonance_above_05_rate": round(computed_rate, 8),
            "reported_total_blocks": total_blocks,
            "reported_mean_resonance_strength": reported_mean,
            "reported_resonance_above_05_count": reported_above_count,
            "reported_resonance_rate": reported_rate,
            "z_score": z_score,
            "p_value": p_value,
        }
    )

    if total_blocks and total_blocks != len(rows):
        details["error"] = "summary total block count does not match CSV rows"
        return GateCheck("phi_resonance_artifacts", "failed", details)

    if (
        reported_mean is not None
        and abs(_safe_float(reported_mean) - computed_mean) > 0.001
    ):
        details["error"] = "summary mean resonance does not match CSV within tolerance"
        return GateCheck("phi_resonance_artifacts", "failed", details)

    if (
        reported_above_count is not None
        and _safe_int(reported_above_count) != computed_above
    ):
        details["error"] = "summary resonance above-threshold count does not match CSV"
        return GateCheck("phi_resonance_artifacts", "failed", details)

    if reported_rate is not None:
        rate = _safe_float(reported_rate)
        if not 0.0 <= rate <= 1.0:
            details["error"] = "summary resonance rate outside [0, 1]"
            return GateCheck("phi_resonance_artifacts", "failed", details)

    if z_score is not None:
        details["statistical_signal_present"] = _safe_float(z_score) >= 3.0
    if p_value is not None:
        details["p_value_reported"] = str(p_value)

    return GateCheck("phi_resonance_artifacts", "passed", details)


async def _solve_once(target: int, nonce_start: int, nonce_end: int) -> int | None:
    from pythia_mining.dodecahedral_solver import DodecahedralQuantumSolver

    solver = DodecahedralQuantumSolver(configured_capacity_ehs=0.1)
    await solver.configure_search(
        target=target, nonce_ranges=[(nonce_start, nonce_end)]
    )
    return await solver.solve(max_iterations=20, timeout=5.0)


def check_deterministic_search(
    target: int, nonce_start: int, nonce_end: int
) -> GateCheck:
    details = {"target": target, "nonce_start": nonce_start, "nonce_end": nonce_end}
    try:
        first = asyncio.run(_solve_once(target, nonce_start, nonce_end))
        second = asyncio.run(_solve_once(target, nonce_start, nonce_end))
    except Exception as exc:  # pragma: no cover - failure packet should preserve detail
        details["error"] = repr(exc)
        return GateCheck("deterministic_search", "failed", details)

    details["first_nonce"] = first
    details["second_nonce"] = second
    if first is None or second is None:
        details["error"] = "solver returned no nonce"
        return GateCheck("deterministic_search", "failed", details)
    if first != second:
        details["error"] = "same target/range produced different nonces"
        return GateCheck("deterministic_search", "failed", details)
    if first < nonce_start or first > nonce_end:
        details["error"] = "solver nonce outside requested range"
        return GateCheck("deterministic_search", "failed", details)

    return GateCheck("deterministic_search", "passed", details)


def _extract_accepted_share_count(payload: Any) -> int:
    if isinstance(payload, dict):
        total = 0
        for key, value in payload.items():
            lowered = key.lower()
            if lowered in {"accepted", "accepted_shares", "shares_accepted"}:
                total = max(total, _safe_int(value))
            else:
                total = max(total, _extract_accepted_share_count(value))
        return total
    if isinstance(payload, list):
        return max((_extract_accepted_share_count(item) for item in payload), default=0)
    return 0


def check_accepted_share_artifacts(command_room_dir: Path, required: bool) -> GateCheck:
    details: dict[str, Any] = {
        "command_room_dir": str(command_room_dir),
        "required": required,
        "files_checked": [],
        "max_accepted_shares_seen": 0,
    }
    if not command_room_dir.exists():
        details["error"] = "command-room directory not found"
        return GateCheck(
            "accepted_share_evidence", "failed" if required else "warning", details
        )

    for path in sorted(command_room_dir.rglob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        accepted = _extract_accepted_share_count(payload)
        details["files_checked"].append(str(path))
        details["max_accepted_shares_seen"] = max(
            int(details["max_accepted_shares_seen"]), accepted
        )

    if int(details["max_accepted_shares_seen"]) > 0:
        return GateCheck("accepted_share_evidence", "passed", details)

    details["error"] = "no accepted-share evidence found"
    return GateCheck(
        "accepted_share_evidence", "failed" if required else "warning", details
    )


def write_report(report: FundingGateReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = output_dir / f"funding_engine_deployment_gate_{report.mode}_{stamp}.json"
    payload = asdict(report)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="HYBA_FULLSTACK funding-engine deployment gate"
    )
    parser.add_argument("--phi-dir", default="artifacts/phi_resonance_100blocks")
    parser.add_argument(
        "--command-room-dir", default="HYBA_FULLSTACK_COMMAND_ROOM_20260612"
    )
    parser.add_argument("--output-dir", default="artifacts/funding_engine")
    parser.add_argument("--target", type=int, default=0x1D00FFFF)
    parser.add_argument("--nonce-start", type=int, default=0)
    parser.add_argument("--nonce-end", type=int, default=4095)
    parser.add_argument("--require-accepted-share", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = [
        check_phi_resonance_artifacts(ROOT / args.phi_dir),
        check_deterministic_search(args.target, args.nonce_start, args.nonce_end),
        check_accepted_share_artifacts(
            ROOT / args.command_room_dir, args.require_accepted_share
        ),
    ]

    hard_failures = [check for check in checks if check.status == "failed"]
    warnings = [check for check in checks if check.status == "warning"]
    status = "failed" if hard_failures else "warning" if warnings else "passed"

    next_actions: list[str] = []
    if status != "passed":
        if any(
            check.name == "accepted_share_evidence"
            for check in hard_failures + warnings
        ):
            next_actions.append(
                "Capture pool-side accepted-share evidence before releasing MD offers."
            )
        if any(check.name == "phi_resonance_artifacts" for check in hard_failures):
            next_actions.append(
                "Run scripts/collect_100_blocks.py and preserve artifacts/phi_resonance_100blocks CSV/JSON artefacts."
            )
        if any(check.name == "deterministic_search" for check in hard_failures):
            next_actions.append(
                "Do not deploy until deterministic search repeatability is restored."
            )
    else:
        next_actions.append(
            "Funding-engine gate passed; proceed according to signed command-room approval."
        )

    report = FundingGateReport(
        status=status,
        generated_at_utc=_utc_now(),
        repository="hybaanalytics1/HYBA_FULLSTACK",
        mode="accepted-share-required" if args.require_accepted_share else "pre-share",
        checks=checks,
        next_actions=next_actions,
        environment={
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "env": _redact_env(),
        },
    )
    output_path = write_report(report, ROOT / args.output_dir)
    print(json.dumps(asdict(report), indent=2))
    print(f"\nEvidence packet written: {output_path}")
    return 0 if status == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
