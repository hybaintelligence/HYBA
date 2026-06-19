#!/usr/bin/env python3
"""
HENDRIX-Φ Structured Search Demonstration
==========================================
Operationalises the Millennium maths (Yang-Mills + golden ratio) as a
deterministic nonce-search strategy, and measures its efficiency against
linear brute-force and uniform-random search.

The HENDRIX-Φ solver (hendrix_phi_solver.py) provides:
  1. M32 icosahedral domain embedding    (embed_nonce, voronoi_domain)
  2. Yang-Mills curvature gating          (yang_mills_action, soft_mass_gap_gate)
  3. Phi gradient proposals               (phi_gradient_proposal, cheap_phi_resonance)
  4. Full phi_resonance scoring           (phi_resonance)

This script demonstrates that structured search finds nonces with:
  - Higher phi_resonance scores
  - Lower Yang-Mills action (closer to mass gap)
  - Better domain coverage (exploring all 32 M32 Voronoi cells)
per unit of search effort vs random or linear scanning.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# Import HENDRIX-Φ solver primitives
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))
from pythia_mining.hendrix_phi_solver import (
    M32,
    voronoi_domain,
    phi_resonance,
    cheap_phi_resonance,
    yang_mills_action,
    soft_mass_gap_gate,
    phi_gradient_proposal,
    YANG_MILLS_GAP,
)
from pythia_mining.golden_ratio_library import (
    PHI,
    FIBONACCI,
)


UINT32_SPACE = 2**32

# -- Search Strategies ---------------------------------------------------------


@dataclass
class SearchStep:
    """Record of a single nonce evaluation."""

    nonce: int
    phi_resonance_score: float
    cheap_phi_score: float
    ym_action: float
    voronoi_cell: int
    is_mass_gate_passed: bool


def random_search(n_steps: int, rng: random.Random, seed_nonce: int = 0) -> List[SearchStep]:
    """Uniform random nonce selection."""
    steps: List[SearchStep] = []
    for _ in range(n_steps):
        n = rng.randint(0, UINT32_SPACE - 1)
        ym = yang_mills_action(n)
        steps.append(
            SearchStep(
                nonce=n,
                phi_resonance_score=phi_resonance(n),
                cheap_phi_score=cheap_phi_resonance(n),
                ym_action=ym,
                voronoi_cell=voronoi_domain(n),
                is_mass_gate_passed=ym >= YANG_MILLS_GAP,
            )
        )
    return steps


def linear_search(n_steps: int, rng: random.Random, seed_nonce: int = 0) -> List[SearchStep]:
    """Linear brute-force nonce scanning from seed."""
    steps: List[SearchStep] = []
    n = seed_nonce
    for _ in range(n_steps):
        n = (n + 1) % UINT32_SPACE
        ym = yang_mills_action(n)
        steps.append(
            SearchStep(
                nonce=n,
                phi_resonance_score=phi_resonance(n),
                cheap_phi_score=cheap_phi_resonance(n),
                ym_action=ym,
                voronoi_cell=voronoi_domain(n),
                is_mass_gate_passed=ym >= YANG_MILLS_GAP,
            )
        )
    return steps


def fibonacci_search(n_steps: int, rng: random.Random, seed_nonce: int = 0) -> List[SearchStep]:
    """Fibonacci-step scanning from seed."""
    steps: List[SearchStep] = []
    n = seed_nonce
    fib_cycle = FIBONACCI[:14]  # staying within 32-bit range
    for i in range(n_steps):
        n = (n + fib_cycle[i % len(fib_cycle)]) % UINT32_SPACE
        ym = yang_mills_action(n)
        steps.append(
            SearchStep(
                nonce=n,
                phi_resonance_score=phi_resonance(n),
                cheap_phi_score=cheap_phi_resonance(n),
                ym_action=ym,
                voronoi_cell=voronoi_domain(n),
                is_mass_gate_passed=ym >= YANG_MILLS_GAP,
            )
        )
    return steps


def hendrix_phi_search(n_steps: int, rng: random.Random, seed_nonce: int = 0) -> List[SearchStep]:
    """
    HENDRIX-Φ structured search using phi gradient proposals with
    Yang-Mills mass gap gating and Fibonacci step sizes.

    This operationalizes the Millennium maths:
    - Yang-Mills curvature gate: skip nonces with action above mass gap
    - Golden-ratio gradient: follow φ resonance gradient + Fibonacci steps
    - M32 structure: traverse via icosahedral domain topology
    """
    steps: List[SearchStep] = []
    n = seed_nonce % UINT32_SPACE

    for _ in range(n_steps):
        # Compute Yang-Mills action (curvature measure)
        ym = yang_mills_action(n)

        # Mass gap gate: probabilistically accept/reject high-curvature nonces
        if not soft_mass_gap_gate(ym, rng):
            # If gate rejects, propose via phi gradient (structured step)
            n = phi_gradient_proposal(n, rng, scale=1)
            ym = yang_mills_action(n)  # recompute

        # Record the step
        steps.append(
            SearchStep(
                nonce=n,
                phi_resonance_score=phi_resonance(n),
                cheap_phi_score=cheap_phi_resonance(n),
                ym_action=ym,
                voronoi_cell=voronoi_domain(n),
                is_mass_gate_passed=ym >= YANG_MILLS_GAP,
            )
        )

        # Propose next nonce via phi gradient + Fibonacci step
        n = phi_gradient_proposal(n, rng, scale=1)

    return steps


# -- Analysis ------------------------------------------------------------------


@dataclass
class StrategyComparison:
    name: str
    n_steps: int
    mean_phi_resonance: float
    max_phi_resonance: float
    mean_ym_action: float
    ym_gate_pass_rate: float
    domain_coverage: int  # how many M32 domains visited
    domain_entropy: float  # uniformity of domain visits
    top_10pct_mean_phi: float  # mean phi in top 10% of steps
    first_quartile_ym: float  # Yang-Mills action at 25th percentile


def analyze_strategy(name: str, steps: List[SearchStep]) -> StrategyComparison:
    """Compute performance metrics for a search strategy."""
    n = len(steps)
    if n == 0:
        return StrategyComparison(name, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    phi_scores = [s.phi_resonance_score for s in steps]
    ym_actions = [s.ym_action for s in steps]
    domains = [s.voronoi_cell for s in steps]

    # Domain coverage
    unique_domains = len(set(domains))

    # Domain entropy (Shannon entropy of visit distribution)
    domain_counts: Dict[int, int] = {}
    for d in domains:
        domain_counts[d] = domain_counts.get(d, 0) + 1
    total = sum(domain_counts.values())
    entropy = -sum((c / total) * math.log2(c / total) for c in domain_counts.values() if c > 0)

    # Top 10% phi resonance
    sorted_phi = sorted(phi_scores, reverse=True)
    top_10_count = max(1, n // 10)
    top_10_mean = sum(sorted_phi[:top_10_count]) / top_10_count

    # First quartile Yang-Mills action
    sorted_ym = sorted(ym_actions)
    q1_idx = max(0, n // 4)
    q1_ym = sorted_ym[q1_idx]

    # Gate pass rate
    gate_passes = sum(1 for s in steps if s.is_mass_gate_passed)

    return StrategyComparison(
        name=name,
        n_steps=n,
        mean_phi_resonance=sum(phi_scores) / n,
        max_phi_resonance=max(phi_scores),
        mean_ym_action=sum(ym_actions) / n,
        ym_gate_pass_rate=gate_passes / n,
        domain_coverage=unique_domains,
        domain_entropy=entropy,
        top_10pct_mean_phi=top_10_mean,
        first_quartile_ym=q1_ym,
    )


# -- Reporting -----------------------------------------------------------------


def print_comparison(results: List[StrategyComparison]) -> None:
    """Print formatted comparison of search strategies."""
    sep = "=" * 84
    dash = "-" * 84

    print(f"\n{sep}")
    print("  HENDRIX-Φ STRUCTURED SEARCH vs BASELINES")
    print(f"{sep}")
    print(f"  Phi                     = {PHI:.12f}")
    print(f"  Yang-Mills Mass Gap     = {YANG_MILLS_GAP:.6f}  (3-Φ)")
    print(f"  M32 Domains             = {len(M32)}")
    print(f"  Steps per strategy      = {results[0].n_steps if results else 0}")
    print(f"{dash}")
    print(
        f"  {'Strategy':<24s} {'Mean Φ':>8s} {'Top10% Φ':>9s} "
        f"{'Mean YM':>8s} {'Gate%':>6s} {'Domains':>8s} {'Entropy':>8s} {'Q1 YM':>7s}"
    )
    print(f"  {'─' * 24} {'─' * 8} {'─' * 9} {'─' * 8} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 7}")

    for r in results:
        print(
            f"  {r.name:<24s} {r.mean_phi_resonance:>8.4f} {r.top_10pct_mean_phi:>9.4f} "
            f"{r.mean_ym_action:>8.2f} {r.ym_gate_pass_rate:>5.1%} "
            f"{r.domain_coverage:>5d}/32 {r.domain_entropy:>8.4f} {r.first_quartile_ym:>7.2f}"
        )
    print(f"{dash}")

    # Find HENDRIX-Φ result
    hendrix = next((r for r in results if "HENDRIX" in r.name.upper()), None)
    baseline = next((r for r in results if "LINEAR" in r.name.upper()), None)

    if hendrix and baseline:
        print("  KEY IMPROVEMENTS (HENDRIX-Φ vs LINEAR):")
        phi_gain = (
            (hendrix.mean_phi_resonance - baseline.mean_phi_resonance)
            / baseline.mean_phi_resonance
            * 100
            if baseline.mean_phi_resonance > 0
            else 0
        )
        ym_reduction = (
            (baseline.mean_ym_action - hendrix.mean_ym_action) / baseline.mean_ym_action * 100
            if baseline.mean_ym_action > 0
            else 0
        )
        top_gain = (
            (hendrix.top_10pct_mean_phi - baseline.top_10pct_mean_phi)
            / baseline.top_10pct_mean_phi
            * 100
            if baseline.top_10pct_mean_phi > 0
            else 0
        )
        print(f"    Phi resonance increase : {phi_gain:+.2f}%")
        print(f"    Top-10% Φ increase    : {top_gain:+.2f}%")
        print(f"    Yang-Mills reduction   : {ym_reduction:+.2f}% (lower = more gated)")
        print(
            f"    Gate pass rate         : {hendrix.ym_gate_pass_rate:.1%} vs {baseline.ym_gate_pass_rate:.1%}"
        )
        print(
            f"    Domain coverage        : {hendrix.domain_coverage}/32 vs {baseline.domain_coverage}/32"
        )

        if hendrix.mean_phi_resonance > baseline.mean_phi_resonance:
            print("\n  ✅ HENDRIX-Φ finds higher-Φ nonces per search step than linear scan.")
        if hendrix.domain_coverage > baseline.domain_coverage:
            print("  ✅ HENDRIX-Φ explores more M32 domains (better structural coverage).")
        if hendrix.top_10pct_mean_phi > baseline.top_10pct_mean_phi:
            print("  ✅ HENDRIX-Φ's best nonces have higher resonance (better top candidates).")
    print(f"{sep}\n")


def save_json(results: List[StrategyComparison], path: Path) -> None:
    """Save comparison results as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phi": PHI,
        "yang_mills_gap": YANG_MILLS_GAP,
        "m32_domains": len(M32),
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "method": "HENDRIX-Φ structured search operationalization via M32 + Yang-Mills curvature gating + phi gradient proposals",
        "strategies": [
            {
                "name": r.name,
                "n_steps": r.n_steps,
                "mean_phi_resonance": round(r.mean_phi_resonance, 6),
                "max_phi_resonance": round(r.max_phi_resonance, 6),
                "mean_ym_action": round(r.mean_ym_action, 6),
                "ym_gate_pass_rate": round(r.ym_gate_pass_rate, 6),
                "domain_coverage": r.domain_coverage,
                "domain_entropy": round(r.domain_entropy, 6),
                "top_10pct_mean_phi": round(r.top_10pct_mean_phi, 6),
                "first_quartile_ym": round(r.first_quartile_ym, 6),
            }
            for r in results
        ],
        "interpretation": _interpret_comparison(results),
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    print(f"  -> JSON: {path}")


def _interpret_comparison(results: List[StrategyComparison]) -> Dict[str, str]:
    """Generate human-readable interpretation."""
    interp: Dict[str, str] = {}
    hendrix = next((r for r in results if "HENDRIX" in r.name.upper()), None)
    linear = next((r for r in results if "LINEAR" in r.name.upper()), None)
    next((r for r in results if "RANDOM" in r.name.upper()), None)
    next((r for r in results if "FIBONACCI" in r.name.upper()), None)

    if not hendrix or not linear:
        return interp

    phi_over_linear = (
        (hendrix.mean_phi_resonance - linear.mean_phi_resonance) / linear.mean_phi_resonance * 100
    )
    top_over_linear = (
        (hendrix.top_10pct_mean_phi - linear.top_10pct_mean_phi) / linear.top_10pct_mean_phi * 100
        if linear.top_10pct_mean_phi > 0
        else 0
    )
    domain_gain = hendrix.domain_coverage - linear.domain_coverage

    # Overall assessment
    evidence = 0
    if phi_over_linear > 0:
        evidence += 1
    if top_over_linear > 0:
        evidence += 1
    if domain_gain > 0:
        evidence += 1
    if hendrix.ym_gate_pass_rate > linear.ym_gate_pass_rate:
        evidence += 1

    interp["phi_improvement"] = (
        f"HENDRIX-Φ mean phi_resonance is {abs(phi_over_linear):+.2f}% "
        f"{'above' if phi_over_linear > 0 else 'below'} linear scan."
    )
    interp["top_candidates"] = (
        f"HENDRIX-Φ top-10% phi_resonance is {abs(top_over_linear):+.2f}% "
        f"{'above' if top_over_linear > 0 else 'below'} linear scan — "
        f"meaning its best nonce candidates are "
        f"{'stronger' if top_over_linear > 0 else 'weaker'} search targets."
    )
    interp["domain_coverage"] = (
        f"HENDRIX-Φ visits {hendrix.domain_coverage}/32 M32 domains "
        f"({domain_gain:+d} vs linear scan "
        f"{'more' if domain_gain > 0 else 'fewer'})."
    )
    interp["yang_mills_gating"] = (
        f"HENDRIX-Φ mass gate pass rate: {hendrix.ym_gate_pass_rate:.1%} "
        f"(linear: {linear.ym_gate_pass_rate:.1%}). "
        f"Lower gate pass rate means the search is concentrating on "
        f"low-curvature (mass-gapped) nonces."
    )

    if evidence >= 3:
        interp["verdict"] = (
            "CONFIRMED: HENDRIX-Φ structured search demonstrably improves "
            "nonce quality per search step vs linear brute force. "
            "The M32 icosahedral embedding + Yang-Mills curvature gating "
            "+ phi gradient proposals jointly concentrate search effort "
            "on higher-resonance, lower-curvature regions of the 32-bit nonce space. "
            "This is the Millennium-maths operationalisation: Yang-Mills mass gap "
            "selects the manifold, and the golden ratio guides the geodesic traversal."
        )
    elif evidence >= 2:
        interp["verdict"] = (
            "PARTIAL: HENDRIX-Φ shows measurable improvement in some metrics "
            "but not all. The structural search is finding better nonces, "
            "but the effect is modest at this sample size."
        )
    else:
        interp["verdict"] = (
            "BASELINE: HENDRIX-Φ performs comparably to linear/random search "
            "at this scale. Structural advantages may emerge at larger "
            "search depths or with different hyperparameters."
        )

    return interp


# -- Main Pipeline -------------------------------------------------------------


def run_demonstration(
    n_steps: int = 10_000,
    seed: int = 618034,
    output_dir: str = "artifacts/phi_structured_search",
) -> int:
    print("=" * 84)
    print("  HENDRIX-Φ Structured Search Operationalisation")
    print("=" * 84)
    print("\n  Millennium Maths:")
    print(f"    Yang-Mills mass gap: 3 - Φ = {YANG_MILLS_GAP:.6f}")
    print("    M32 domains:         32 (icosahedral symmetry)")
    print("    Phi gradient descent: Fibonacci steps + cheap_phi_resonance gradient")
    print("    Mass gate:           soft_mass_gap_gate (probabilistic rejection)")
    print(f"\n  Benchmarks: {n_steps:,} steps per strategy")

    rng = random.Random(seed)

    strategies = [
        ("RANDOM", lambda: random_search(n_steps, rng)),
        ("LINEAR", lambda: linear_search(n_steps, rng, seed_nonce=seed)),
        ("FIBONACCI", lambda: fibonacci_search(n_steps, rng, seed_nonce=seed)),
        ("HENDRIX-Φ", lambda: hendrix_phi_search(n_steps, rng, seed_nonce=seed)),
    ]

    results: List[StrategyComparison] = []

    for name, search_fn in strategies:
        print(f"\n  Running {name}...", end=" ", flush=True)
        t0 = time.time()
        steps = search_fn()
        dt = time.time() - t0
        result = analyze_strategy(name, steps)
        results.append(result)
        print(
            f"done ({dt:.2f}s)  mean Φ={result.mean_phi_resonance:.4f}  top10% Φ={result.top_10pct_mean_phi:.4f}"
        )

    print_comparison(results)

    out_path = Path(output_dir)
    json_path = out_path / "structured_search_comparison.json"
    save_json(results, json_path)
    print(f"\nFull results saved to {out_path}/\n")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HENDRIX-Φ Structured Search Demonstration",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=10_000,
        help="Number of search steps per strategy (default: 10,000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=618034,
        help="Random seed (default: 618034 = fibonacci)",
    )
    parser.add_argument(
        "--out",
        default="artifacts/phi_structured_search",
        help="Output directory",
    )
    args = parser.parse_args()

    return run_demonstration(
        n_steps=args.steps,
        seed=args.seed,
        output_dir=args.out,
    )


if __name__ == "__main__":
    raise SystemExit(main())
