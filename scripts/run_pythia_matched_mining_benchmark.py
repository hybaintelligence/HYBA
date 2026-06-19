#!/usr/bin/env python3
"""Run an offline matched PYTHIA mining benchmark.

This script performs no network I/O and never submits to a pool. It creates a
replay-safe 76-byte header prefix, builds PYTHIA's structure guidance packet,
compares sequential baseline traversal against PYTHIA structured traversal under
one target and one nonce budget, then writes a sealed JSON report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pythia_mining.pythia_matched_mining_benchmark import (
    ReplayBlockTemplate,
    baseline_nonce_order,
    build_guidance_from_structure,
    pythia_structured_nonce_order,
    run_matched_mining_benchmark,
    synthetic_header_prefix,
    target_from_best_nonce,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=int, default=4096, help="Matched nonce candidate budget")
    parser.add_argument("--height", type=int, default=840_321, help="Replay block height context")
    parser.add_argument(
        "--difficulty", type=float, default=88_000_000_000_000.0, help="Replay difficulty context"
    )
    parser.add_argument(
        "--seed", default="hyba-pythia-matched-replay", help="Deterministic header seed"
    )
    parser.add_argument(
        "--mode", choices=["baseline-best", "pythia-window"], default="pythia-window"
    )
    parser.add_argument(
        "--output", default="artifacts/pythia_mining_benchmark/latest/benchmark_report.json"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.budget < 1:
        raise SystemExit("--budget must be positive")

    target_hex = "00000000000000000002b0000000000000000000000000000000000000000000"
    guidance = build_guidance_from_structure(
        block_height=args.height,
        difficulty=args.difficulty,
        target_hex=target_hex,
        dodecahedral_domain_score=0.97,
        icosahedral_face_score=0.94,
        mass_gap_valley_score=0.86,
        entanglement_spectrum_score=0.84,
        sector_coverage=0.91,
        golden_angle_alignment=0.72,
        phi15_rate=0.23,
    )
    prefix = synthetic_header_prefix(args.seed)

    if args.mode == "pythia-window":
        pythia_order = pythia_structured_nonce_order(guidance, args.budget)
        target, target_nonce, target_hash = target_from_best_nonce(
            template_prefix_hex=prefix,
            nonces=pythia_order[: max(1, min(64, args.budget))],
            block_height=args.height,
            difficulty=args.difficulty,
            template_id=f"{args.mode}:{args.seed}",
        )
    else:
        target, target_nonce, target_hash = target_from_best_nonce(
            template_prefix_hex=prefix,
            nonces=baseline_nonce_order(args.budget),
            block_height=args.height,
            difficulty=args.difficulty,
            template_id=f"{args.mode}:{args.seed}",
        )

    template = ReplayBlockTemplate(
        header_prefix_hex=prefix,
        target=target,
        block_height=args.height,
        difficulty=args.difficulty,
        template_id=f"{args.mode}:{args.seed}",
    )
    report = run_matched_mining_benchmark(
        template=template,
        guidance=guidance,
        candidate_budget=args.budget,
    )
    payload = report.to_payload()
    payload["controlled_target"] = {
        "nonce": target_nonce,
        "hash": target_hash,
        "mode": args.mode,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "report_hash": report.report_hash,
                "interpretation": report.interpretation,
                "candidate_budget_advantage": report.candidate_budget_advantage,
                "best_hash_improvement_ratio": report.best_hash_improvement_ratio,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
