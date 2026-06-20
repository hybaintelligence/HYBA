#!/usr/bin/env python3
"""Analyze a bounded testnet/live-observed mining validation artifact.

The analyzer is deliberately conservative: it reads only exported runtime evidence,
computes simple acceptance/proposal summaries, and emits a GO/NO_GO verdict without
fabricating missing pool telemetry.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Any


def _load_latest_input(pattern: str) -> tuple[Path, dict[str, Any]]:
    matches = [Path(p) for p in glob.glob(pattern)] if any(ch in pattern for ch in "*?[") else [Path(pattern)]
    existing = [p for p in matches if p.exists()]
    if not existing:
        raise FileNotFoundError(f"no input artifact matched {pattern!r}")
    latest = max(existing, key=lambda p: p.stat().st_mtime)
    return latest, json.loads(latest.read_text(encoding="utf-8"))


def _posterior_means(target_evidence: dict[str, Any]) -> dict[str, float]:
    means: dict[str, float] = {}
    for target, evidence in target_evidence.items():
        accepted = float(evidence.get("accepted", evidence.get("successes", 0)))
        rejected = float(evidence.get("rejected", evidence.get("failures", 0)))
        means[target] = accepted / max(accepted + rejected + 2.0, 1.0)
    return means


def analyze_testnet_run(input_pattern: str, output_file: Path) -> int:
    input_file, data = _load_latest_input(input_pattern)
    pool_responses = list(data.get("pool_responses", data.get("pool_response_history", [])))
    target_evidence = data.get("target_evidence", data.get("target_selection", {}))
    proposals_accepted = int(data.get("proposals_accepted", data.get("accepted_proposals", 0)))
    circuit_breaker_trips = int(data.get("circuit_breaker_trips", data.get("autonomous_circuit_breaker_trips", 0)))

    analysis = {
        "input_file": str(input_file),
        "pool_responses": {
            "total": len(pool_responses),
            "accepted": sum(1 for response in pool_responses if response.get("accepted")),
            "rejected": sum(1 for response in pool_responses if not response.get("accepted")),
        },
        "autonomous_behavior": {
            "reflexive_cycles": int(data.get("reflexive_cycle_count", data.get("epochs", 0))),
            "proposals_generated": int(data.get("proposals_generated", len(data.get("proposals", [])))),
            "proposals_accepted": proposals_accepted,
            "circuit_breaker_trips": circuit_breaker_trips,
        },
        "thompson_sampling": {
            "target_evidence": target_evidence,
            "posterior_means": _posterior_means(target_evidence),
        },
    }
    analysis["readiness_verdict"] = (
        "GO"
        if circuit_breaker_trips == 0 and proposals_accepted > 0 and len(pool_responses) > 10
        else "NO_GO"
    )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(analysis, indent=2, sort_keys=True), encoding="utf-8")
    print(f"✅ Analysis complete: {analysis['readiness_verdict']}")
    print(f"   Pool responses: {analysis['pool_responses']['total']}")
    print(f"   Proposals accepted: {analysis['autonomous_behavior']['proposals_accepted']}")
    return 0 if analysis["readiness_verdict"] == "GO" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", help="Input JSON artifact or glob")
    parser.add_argument("output", nargs="?", type=Path, help="Output analysis JSON")
    parser.add_argument("--input", dest="input_flag", help="Input JSON artifact or glob")
    parser.add_argument("--output", dest="output_flag", type=Path, help="Output analysis JSON")
    args = parser.parse_args()
    input_pattern = args.input_flag or args.input
    output_file = args.output_flag or args.output
    if not input_pattern or output_file is None:
        parser.error("input and output are required")
    return analyze_testnet_run(input_pattern, output_file)


if __name__ == "__main__":
    sys.exit(main())
