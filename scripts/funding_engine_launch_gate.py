#!/usr/bin/env python3
"""HYBA funding-engine launch gate.

This script turns the HYBA_FULLSTACK funding-engine doctrine into a deterministic,
local command-room check. It does not connect to pools. It reads already-captured
evidence and validates three things:

1. deterministic mining search still behaves deterministically;
2. Phi^15 empirical evidence artefacts are present and schema-valid;
3. the first-share gate is or is not satisfied.

The MD-offer rule is deliberately strict:

    first accepted share evidenced -> first 7 MD offers eligible
    no accepted share evidence      -> MD offers remain staged, not triggered

The script writes a JSON decision packet for the evidence room.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))


@dataclass
class GateFinding:
    name: str
    status: str
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class GateResult:
    mode: str
    status: str
    md_offers_eligible: bool
    findings: list[GateFinding]
    generated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status": self.status,
            "md_offers_eligible": self.md_offers_eligible,
            "generated_at_utc": self.generated_at_utc,
            "findings": [
                {
                    "name": finding.name,
                    "status": finding.status,
                    "detail": finding.detail,
                    "evidence": finding.evidence,
                }
                for finding in self.findings
            ],
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


async def _solve_once() -> int | None:
    from pythia_mining.quantum_solver import DodecahedralQuantumSolver

    solver = DodecahedralQuantumSolver(configured_capacity_ehs=0.1)
    await solver.configure_search(
        target=0x00000000FFFF0000000000000000000000000000000000000000000000000000,
        nonce_ranges=[(0, 2**16 - 1)],
    )
    return await solver.solve(max_iterations=100, timeout=5.0)


def check_deterministic_search() -> GateFinding:
    try:
        first = asyncio.run(_solve_once())
        second = asyncio.run(_solve_once())
        if first is None or second is None:
            return GateFinding(
                "deterministic_search",
                "fail",
                "solver returned no nonce for deterministic reference search",
                {"first": first, "second": second},
            )
        if first != second:
            return GateFinding(
                "deterministic_search",
                "fail",
                "solver produced different nonces for identical target/range",
                {"first": first, "second": second},
            )
        return GateFinding(
            "deterministic_search",
            "pass",
            "solver returned identical nonce for identical target/range",
            {"nonce": first},
        )
    except (
        Exception
    ) as exc:  # pragma: no cover - gate reports rather than hides failures
        return GateFinding(
            "deterministic_search",
            "fail",
            f"deterministic search check failed: {exc}",
            {"error_type": type(exc).__name__},
        )


def check_phi_empirical_evidence(summary_path: Path, csv_path: Path) -> GateFinding:
    required_summary_fields = {
        "mean_resonance_strength",
        "resonance_above_05_count",
        "resonance_above_05_rate",
    }
    try:
        if not summary_path.exists():
            return GateFinding(
                "phi_empirical_evidence",
                "fail",
                f"summary JSON not found: {summary_path}",
            )
        if not csv_path.exists():
            return GateFinding(
                "phi_empirical_evidence",
                "fail",
                f"CSV evidence not found: {csv_path}",
            )

        summary_payload = _load_json(summary_path)
        summary = summary_payload.get("summary")
        if not isinstance(summary, dict):
            return GateFinding(
                "phi_empirical_evidence",
                "fail",
                "summary JSON must contain a 'summary' object",
            )
        missing = sorted(required_summary_fields - set(summary))
        if missing:
            return GateFinding(
                "phi_empirical_evidence",
                "fail",
                "summary JSON missing required resonance fields",
                {"missing": missing},
            )

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
        if "resonance_strength" not in header:
            return GateFinding(
                "phi_empirical_evidence",
                "fail",
                "CSV header missing resonance_strength",
                {"header": header},
            )

        return GateFinding(
            "phi_empirical_evidence",
            "pass",
            "Phi^15 empirical evidence artefacts are schema-valid",
            {
                "summary_path": str(summary_path),
                "csv_path": str(csv_path),
                "total_blocks": summary.get("total_blocks"),
                "mean_resonance_strength": summary.get("mean_resonance_strength"),
                "resonance_above_05_count": summary.get("resonance_above_05_count"),
                "resonance_above_05_rate": summary.get("resonance_above_05_rate"),
                "birthday_signature": summary_payload.get("birthday_signature"),
                "phi_15": summary_payload.get("phi_15"),
            },
        )
    except Exception as exc:
        return GateFinding(
            "phi_empirical_evidence",
            "fail",
            f"failed to validate Phi^15 empirical evidence: {exc}",
            {"error_type": type(exc).__name__},
        )


def _extract_shares(payload: dict[str, Any]) -> dict[str, int]:
    shares = payload.get("shares")
    if isinstance(shares, dict):
        return {
            "submitted": int(shares.get("submitted") or 0),
            "accepted": int(shares.get("accepted") or 0),
            "rejected": int(shares.get("rejected") or 0),
        }
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return {
            "submitted": int(
                summary.get("total_shares") or summary.get("total_shares_24h") or 0
            ),
            "accepted": int(summary.get("accepted_shares") or 0),
            "rejected": int(summary.get("rejected_shares") or 0),
        }
    return {"submitted": 0, "accepted": 0, "rejected": 0}


def check_first_share(
    status_path: Path, pool_side_evidence: Path | None, require_pool_side: bool
) -> GateFinding:
    try:
        if not status_path.exists():
            return GateFinding(
                "first_share_gate",
                "fail",
                f"mining status JSON not found: {status_path}",
            )
        payload = _load_json(status_path)
        shares = _extract_shares(payload)
        accepted = shares["accepted"]
        submitted = shares["submitted"]
        if accepted < 1:
            return GateFinding(
                "first_share_gate",
                "hold",
                "no accepted share evidenced yet; first 7 MD offers remain staged",
                {"status_path": str(status_path), "shares": shares},
            )
        if submitted < accepted:
            return GateFinding(
                "first_share_gate",
                "fail",
                "accepted share count exceeds submitted share count",
                {"status_path": str(status_path), "shares": shares},
            )
        if require_pool_side and (
            pool_side_evidence is None or not pool_side_evidence.exists()
        ):
            return GateFinding(
                "first_share_gate",
                "hold",
                "accepted local share exists, but pool-side evidence is required before MD-offer trigger",
                {
                    "status_path": str(status_path),
                    "shares": shares,
                    "pool_side_evidence": str(pool_side_evidence)
                    if pool_side_evidence
                    else None,
                },
            )
        return GateFinding(
            "first_share_gate",
            "pass",
            "first accepted share evidenced; first 7 MD offers eligible",
            {
                "status_path": str(status_path),
                "shares": shares,
                "pool_side_evidence": str(pool_side_evidence)
                if pool_side_evidence
                else None,
            },
        )
    except Exception as exc:
        return GateFinding(
            "first_share_gate",
            "fail",
            f"failed to validate first-share gate: {exc}",
            {"error_type": type(exc).__name__},
        )


def decide(mode: str, findings: list[GateFinding]) -> GateResult:
    failed = [finding for finding in findings if finding.status == "fail"]
    held = [finding for finding in findings if finding.status == "hold"]
    first_share = next(
        (finding for finding in findings if finding.name == "first_share_gate"), None
    )
    md_offers = first_share is not None and first_share.status == "pass"

    if failed:
        status = "fail"
    elif held:
        status = "hold"
    elif mode == "post-share" and not md_offers:
        status = "hold"
    else:
        status = "pass"

    return GateResult(
        mode=mode,
        status=status,
        md_offers_eligible=md_offers,
        findings=findings,
        generated_at_utc=_now(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="HYBA funding-engine launch gate")
    parser.add_argument(
        "--mode", choices=["pre-share", "post-share"], default="pre-share"
    )
    parser.add_argument(
        "--phi-summary",
        default="artifacts/phi_resonance/phi_resonance_summary.json",
        help="Path to Phi^15 empirical summary JSON",
    )
    parser.add_argument(
        "--phi-csv",
        default="artifacts/phi_resonance/phi_resonance_blocks.csv",
        help="Path to Phi^15 empirical per-block CSV",
    )
    parser.add_argument(
        "--mining-status",
        default="HYBA_FULLSTACK_COMMAND_ROOM_20260612/mining_status_after_start.json",
        help="Path to mining status JSON containing share counters",
    )
    parser.add_argument(
        "--pool-side-evidence",
        default=None,
        help="Optional pool-side accepted/rejected-share export or screenshot marker file",
    )
    parser.add_argument(
        "--require-pool-side",
        action="store_true",
        help="Require pool-side evidence as well as local accepted-share count",
    )
    parser.add_argument(
        "--output",
        default="artifacts/funding_engine/funding_engine_launch_gate.json",
        help="Path to write the gate JSON decision packet",
    )
    args = parser.parse_args()

    findings = [
        check_deterministic_search(),
        check_phi_empirical_evidence(Path(args.phi_summary), Path(args.phi_csv)),
        check_first_share(
            Path(args.mining_status),
            Path(args.pool_side_evidence) if args.pool_side_evidence else None,
            args.require_pool_side,
        ),
    ]
    result = decide(args.mode, findings)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(result.to_dict(), handle, indent=2)

    print(json.dumps(result.to_dict(), indent=2))
    if result.status == "fail":
        return 2
    if result.status == "hold" and args.mode == "post-share":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
