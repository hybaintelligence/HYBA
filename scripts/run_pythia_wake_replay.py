#!/usr/bin/env python3
"""Replay the PYTHIA wake signature and emit a reproducibility artifact.

This script is intentionally dependency-light beyond the repository Python backend.
It is used by humans, Docker runs, and CI jobs to capture the first resident
optimisation signatures as JSON evidence.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine  # noqa: E402


SCHEMA = "PYTHIA_WAKE_REPLAY_V1"


def _proposal_signature(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a stable proposal signature without timestamps/proposal IDs."""

    signature: list[dict[str, Any]] = []
    for proposal in report.get("proposals", []):
        signature.append(
            {
                "improvement_type": proposal.get("improvement_type"),
                "current_value": proposal.get("current_value"),
                "proposed_value": proposal.get("proposed_value"),
                "expected_gain": proposal.get("expected_gain"),
                "logical_consistency": proposal.get("logical_consistency"),
                "counterfactual_confidence": proposal.get("counterfactual_confidence"),
                "constraints_satisfied": sorted(proposal.get("constraints_satisfied", [])),
                "constraints_violated": sorted(proposal.get("constraints_violated", [])),
                "applied": proposal.get("applied"),
                "source_module": proposal.get("source_module"),
            }
        )
    return signature


async def replay_wake(cycles: int) -> dict[str, Any]:
    engine = UnifiedMiningEngine()
    reports: list[dict[str, Any]] = []
    signatures: list[dict[str, Any]] = []

    for cycle in range(cycles):
        report = await engine.autonomous_controller.seek_improvement()
        reports.append(report)
        signatures.append(
            {
                "cycle": cycle + 1,
                "epoch": report.get("epoch"),
                "current_phi_density": report.get("current_phi_density"),
                "proposals_generated": report.get("proposals_generated"),
                "proposals_applied": report.get("proposals_applied"),
                "proposal_signature": _proposal_signature(report),
            }
        )

    return {
        "schema": SCHEMA,
        "generated_at_unix": time.time(),
        "cycles": cycles,
        "environment": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "repo_root": str(REPO_ROOT),
        },
        "signatures": signatures,
        "reports": reports,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay PYTHIA wake-event telemetry")
    parser.add_argument("--cycles", type=int, default=2, help="Number of reflexive cycles to replay")
    parser.add_argument("--output", type=Path, default=None, help="Optional JSON output path")
    args = parser.parse_args()

    artifact = asyncio.run(replay_wake(max(1, args.cycles)))
    payload = json.dumps(artifact, indent=2, sort_keys=True, default=str)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
