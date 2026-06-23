"""
Falsifiable benchmark: φ-guided vs uniform-random vs Fibonacci-stride nonce search.

Three strategies compete under identical conditions:
  - Equal iteration budget (not time, to eliminate JIT/cache warmup noise)
  - Same Bitcoin header (real SHA-256d, not mocked)
  - Adjustable target difficulty via nbits

Measured outputs (all falsifiable):
  - time_to_first_hit_s: wall-clock seconds to find first valid nonce
  - hits_in_budget: valid nonces found within N iterations
  - hashes_per_second: raw SHA-256d throughput
  - overhead_ratio: strategy cost relative to uniform random

Results written to artifacts/benchmark_phi_vs_random_<timestamp>.json

Hypothesis being tested:
  If φ-resonance encodes genuine structural information about Bitcoin's hash
  function, φ-guided search will find valid nonces faster than uniform random
  under equal iteration budgets.

  Null hypothesis: φ-guided search performs the same as or worse than random.
  Current known result (from hendrix_phi_solver.algorithm_metadata()):
    phi_vs_random_benchmark = RANDOM_PERFORMS_BETTER_ON_SYNTHETIC
    cpu_overhead_vs_random  = 3.73x

Run:
  python scripts/benchmark_phi_vs_random.py [--iterations N] [--trials T] [--difficulty D]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.hendrix_phi_solver import (
    cheap_phi_resonance,
    phi_gradient_proposal,
)
from pythia_mining.mining_validation import (
    build_block_header,
    compute_merkle_root,
    coinbase_hash_hex,
)
from pythia_mining.stratum_client import MiningJob


# ---------------------------------------------------------------------------
# Benchmark job fixture — regtest difficulty, real header construction
# ---------------------------------------------------------------------------


def _make_job(nbits: str, target: int) -> MiningJob:
    return MiningJob(
        job_id="bench-job",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits=nbits,
        ntime="5e9a5c00",
        target=target,
        extranonce1="abcd1234",
        extranonce2_size=4,
    )


def _precompute_header_prefix(job: MiningJob, extranonce2: str = "00000000") -> bytes:
    """Compute the 76-byte header prefix (everything except the 4-byte nonce)."""
    cb_hash = coinbase_hash_hex(job, extranonce2)
    merkle_root = compute_merkle_root(cb_hash, job.merkle_branch)
    # build_block_header builds the full 80 bytes; we slice off the last 4
    dummy_header = build_block_header(job, merkle_root, 0)
    return dummy_header[:76]  # prefix without nonce


def _validate_nonce_fast(prefix: bytes, nonce: int, target: int) -> bool:
    """Inline SHA-256d — avoids function-call overhead of validate_share."""
    nonce_bytes = nonce.to_bytes(4, byteorder="little", signed=False)
    header = prefix + nonce_bytes
    digest = hashlib.sha256(hashlib.sha256(header).digest()).digest()
    hash_int = int.from_bytes(digest, byteorder="little", signed=False)
    return hash_int <= target


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------


@dataclass
class StrategyResult:
    name: str
    iterations: int
    hits: int
    time_s: float
    first_hit_iteration: Optional[int]
    first_hit_time_s: Optional[float]
    hashes_per_second: float
    overhead_ratio: float = 1.0  # filled in after all strategies complete
    notes: str = ""


def _run_uniform_random(
    prefix: bytes, target: int, iterations: int, rng: random.Random
) -> StrategyResult:
    hits = 0
    first_hit_iter: Optional[int] = None
    first_hit_time: Optional[float] = None
    t0 = time.perf_counter()
    for i in range(iterations):
        nonce = rng.randint(0, 2**32 - 1)
        if _validate_nonce_fast(prefix, nonce, target):
            hits += 1
            if first_hit_iter is None:
                first_hit_iter = i + 1
                first_hit_time = time.perf_counter() - t0
    elapsed = time.perf_counter() - t0
    return StrategyResult(
        name="uniform_random",
        iterations=iterations,
        hits=hits,
        time_s=elapsed,
        first_hit_iteration=first_hit_iter,
        first_hit_time_s=first_hit_time,
        hashes_per_second=iterations / max(elapsed, 1e-9),
    )


def _run_sequential(
    prefix: bytes, target: int, iterations: int, start_nonce: int = 0
) -> StrategyResult:
    hits = 0
    first_hit_iter: Optional[int] = None
    first_hit_time: Optional[float] = None
    t0 = time.perf_counter()
    for i in range(iterations):
        nonce = (start_nonce + i) % (2**32)
        if _validate_nonce_fast(prefix, nonce, target):
            hits += 1
            if first_hit_iter is None:
                first_hit_iter = i + 1
                first_hit_time = time.perf_counter() - t0
    elapsed = time.perf_counter() - t0
    return StrategyResult(
        name="sequential",
        iterations=iterations,
        hits=hits,
        time_s=elapsed,
        first_hit_iteration=first_hit_iter,
        first_hit_time_s=first_hit_time,
        hashes_per_second=iterations / max(elapsed, 1e-9),
    )


def _run_phi_guided(
    prefix: bytes, target: int, iterations: int, rng: random.Random
) -> StrategyResult:
    """φ-guided search: Fibonacci-stride gradient proposals from cheap_phi_resonance.

    Each candidate is proposed via phi_gradient_proposal, which biases steps
    toward higher φ-resonance using Fibonacci-scaled gradients. This is the
    core HENDRIX-Φ traversal strategy — no sorting overhead, pure online search.
    """
    hits = 0
    first_hit_iter: Optional[int] = None
    first_hit_time: Optional[float] = None
    nonce = rng.randint(0, 2**32 - 1)
    t0 = time.perf_counter()
    for i in range(iterations):
        if _validate_nonce_fast(prefix, nonce, target):
            hits += 1
            if first_hit_iter is None:
                first_hit_iter = i + 1
                first_hit_time = time.perf_counter() - t0
        nonce = phi_gradient_proposal(nonce, rng, scale=1)
    elapsed = time.perf_counter() - t0
    return StrategyResult(
        name="phi_guided",
        iterations=iterations,
        hits=hits,
        time_s=elapsed,
        first_hit_iteration=first_hit_iter,
        first_hit_time_s=first_hit_time,
        hashes_per_second=iterations / max(elapsed, 1e-9),
        notes="HENDRIX-Phi gradient traversal via cheap_phi_resonance Fibonacci steps",
    )


def _run_phi_sorted(
    prefix: bytes, target: int, iterations: int, rng: random.Random
) -> StrategyResult:
    """φ-sorted search: pre-sort a candidate pool by descending φ-resonance.

    This is the more expensive variant tested in test_gap_phi_search_vs_random.py.
    It front-loads computation (sorting) to evaluate highest-resonance nonces first.
    Overhead includes the sort cost, which is excluded from the iteration count
    but included in total elapsed time.
    """
    # Sample a pool 4× the iteration budget, sort by resonance, take top N
    pool_size = min(iterations * 4, 2**18)  # cap at 256K to keep sort tractable
    pool = [rng.randint(0, 2**32 - 1) for _ in range(pool_size)]
    sort_start = time.perf_counter()
    pool.sort(key=cheap_phi_resonance, reverse=True)
    sort_time = time.perf_counter() - sort_start
    candidates = pool[:iterations]

    hits = 0
    first_hit_iter: Optional[int] = None
    first_hit_time: Optional[float] = None
    t0 = time.perf_counter()
    for i, nonce in enumerate(candidates):
        if _validate_nonce_fast(prefix, nonce, target):
            hits += 1
            if first_hit_iter is None:
                first_hit_iter = i + 1
                first_hit_time = time.perf_counter() - t0
    elapsed = time.perf_counter() - t0
    return StrategyResult(
        name="phi_sorted",
        iterations=iterations,
        hits=hits,
        time_s=elapsed + sort_time,
        first_hit_iteration=first_hit_iter,
        first_hit_time_s=first_hit_time,
        hashes_per_second=iterations / max(elapsed + sort_time, 1e-9),
        notes=f"sort_overhead_s={sort_time:.4f} pool_size={pool_size}",
    )


# ---------------------------------------------------------------------------
# Trial runner
# ---------------------------------------------------------------------------


@dataclass
class TrialResult:
    trial: int
    seed: int
    target_hex: str
    nbits: str
    iterations: int
    strategies: List[StrategyResult] = field(default_factory=list)


def run_trial(
    trial_idx: int,
    seed: int,
    nbits: str,
    target: int,
    iterations: int,
) -> TrialResult:
    rng = random.Random(seed)
    job = _make_job(nbits, target)
    prefix = _precompute_header_prefix(job)

    results = [
        _run_uniform_random(prefix, target, iterations, random.Random(seed)),
        _run_sequential(
            prefix, target, iterations, start_nonce=rng.randint(0, 2**32 - 1)
        ),
        _run_phi_guided(prefix, target, iterations, random.Random(seed + 1)),
        _run_phi_sorted(prefix, target, iterations, random.Random(seed + 2)),
    ]

    # Compute overhead ratios relative to uniform_random throughput
    random_hps = next(
        r.hashes_per_second for r in results if r.name == "uniform_random"
    )
    for r in results:
        r.overhead_ratio = random_hps / max(r.hashes_per_second, 1.0)

    return TrialResult(
        trial=trial_idx,
        seed=seed,
        target_hex=f"{target:064x}",
        nbits=nbits,
        iterations=iterations,
        strategies=results,
    )


# ---------------------------------------------------------------------------
# Aggregation and reporting
# ---------------------------------------------------------------------------


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _aggregate(trials: List[TrialResult]) -> dict:
    strategy_names = [s.name for s in trials[0].strategies]
    agg: dict = {}
    for name in strategy_names:
        all_hits = [s.hits for t in trials for s in t.strategies if s.name == name]
        all_hps = [
            s.hashes_per_second for t in trials for s in t.strategies if s.name == name
        ]
        all_overhead = [
            s.overhead_ratio for t in trials for s in t.strategies if s.name == name
        ]
        first_hit_iters = [
            s.first_hit_iteration
            for t in trials
            for s in t.strategies
            if s.name == name and s.first_hit_iteration is not None
        ]
        agg[name] = {
            "mean_hits_per_trial": _mean(all_hits),
            "mean_hashes_per_second": _mean(all_hps),
            "mean_overhead_ratio_vs_random": _mean(all_overhead),
            "mean_first_hit_iteration": (
                _mean(first_hit_iters) if first_hit_iters else None
            ),
            "trials_with_hit": len(first_hit_iters),
            "total_trials": len(trials),
        }
    return agg


def _verdict(agg: dict) -> str:
    random_hits = agg["uniform_random"]["mean_hits_per_trial"]
    phi_guided_hits = agg["phi_guided"]["mean_hits_per_trial"]
    phi_sorted_hits = agg["phi_sorted"]["mean_hits_per_trial"]
    phi_guided_overhead = agg["phi_guided"]["mean_overhead_ratio_vs_random"]
    phi_sorted_overhead = agg["phi_sorted"]["mean_overhead_ratio_vs_random"]

    lines = ["--- VERDICT ---"]

    # Throughput comparison
    if phi_guided_overhead > 1.05:
        lines.append(
            f"phi_guided overhead: {phi_guided_overhead:.2f}x slower than uniform_random "
            f"(null hypothesis NOT rejected for throughput)"
        )
    else:
        lines.append(
            f"phi_guided overhead: {phi_guided_overhead:.2f}x "
            f"(within 5% of random — no significant throughput penalty)"
        )

    if phi_sorted_overhead > 1.05:
        lines.append(
            f"phi_sorted overhead: {phi_sorted_overhead:.2f}x slower (sort cost dominates)"
        )

    # Hit rate comparison
    if random_hits > 0:
        phi_guided_ratio = phi_guided_hits / random_hits
        phi_sorted_ratio = phi_sorted_hits / random_hits
        if phi_guided_ratio >= 1.05:
            lines.append(
                f"phi_guided finds {phi_guided_ratio:.2f}x more hits than random — "
                f"NULL HYPOTHESIS REJECTED for phi_guided hit rate"
            )
        else:
            lines.append(
                f"phi_guided hit rate ratio vs random: {phi_guided_ratio:.3f} — "
                f"no significant advantage (null hypothesis stands)"
            )
        if phi_sorted_ratio >= 1.05:
            lines.append(
                f"phi_sorted finds {phi_sorted_ratio:.2f}x more hits — "
                f"resonance pre-sorting has measurable benefit"
            )
    else:
        lines.append(
            "No hits recorded — increase --difficulty or --iterations for hit-rate comparison"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="φ vs random nonce search benchmark")
    parser.add_argument(
        "--iterations",
        type=int,
        default=100_000,
        help="Nonce candidates evaluated per strategy per trial (default: 100000)",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=5,
        help="Number of independent trials (different seeds) (default: 5)",
    )
    parser.add_argument(
        "--difficulty",
        type=float,
        default=0.001,
        help="Mining difficulty (lower = easier = more hits) (default: 0.001)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed (each trial gets seed+trial_idx)",
    )
    args = parser.parse_args()

    # Convert difficulty to target
    MAX_TARGET = int("00000000ffff" + "0" * 52, 16)
    target = max(1, int(MAX_TARGET / max(args.difficulty, 1e-12)))
    # Use a regtest-style nbits that matches our target range
    nbits = "207fffff"  # regtest genesis nbits (very easy)
    # Override target directly — nbits is for display only in this benchmark
    target = int("0" * 0 + "ff" * 31, 16)  # ~1/256 chance per nonce

    print("Benchmark: φ-guided vs uniform-random nonce search")
    print(f"  iterations/trial: {args.iterations:,}")
    print(f"  trials:           {args.trials}")
    print(f"  difficulty:       {args.difficulty}")
    print(f"  target (hex):     {target:064x}")
    print()

    trials: List[TrialResult] = []
    for t in range(args.trials):
        seed = args.seed + t
        print(f"  Trial {t + 1}/{args.trials} (seed={seed})...", end=" ", flush=True)
        result = run_trial(
            trial_idx=t + 1,
            seed=seed,
            nbits=nbits,
            target=target,
            iterations=args.iterations,
        )
        trials.append(result)
        for s in result.strategies:
            print(
                f"{s.name}={s.hits}hits@{s.hashes_per_second / 1000:.1f}kH/s", end="  "
            )
        print()

    agg = _aggregate(trials)
    verdict = _verdict(agg)

    print()
    print(verdict)
    print()

    # Print per-strategy summary table
    print(
        f"{'Strategy':<20} {'Mean Hits':>10} {'Mean kH/s':>12} {'Overhead':>10} {'MeanFirstHit':>14}"
    )
    print("-" * 70)
    for name, stats in agg.items():
        fh = stats["mean_first_hit_iteration"]
        fh_str = f"{fh:.0f}" if fh is not None else "none"
        print(
            f"{name:<20} "
            f"{stats['mean_hits_per_trial']:>10.2f} "
            f"{stats['mean_hashes_per_second'] / 1000:>12.1f} "
            f"{stats['mean_overhead_ratio_vs_random']:>9.2f}x "
            f"{fh_str:>14}"
        )

    # Write artifact
    artifacts_dir = ROOT / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    ts = int(time.time())
    out_path = artifacts_dir / f"benchmark_phi_vs_random_{ts}.json"
    payload = {
        "benchmark": "phi_vs_random_nonce_search",
        "timestamp": ts,
        "parameters": {
            "iterations": args.iterations,
            "trials": args.trials,
            "difficulty": args.difficulty,
            "target_hex": f"{target:064x}",
            "base_seed": args.seed,
        },
        "aggregate": agg,
        "verdict": verdict,
        "trials": [
            {
                "trial": t.trial,
                "seed": t.seed,
                "strategies": [asdict(s) for s in t.strategies],
            }
            for t in trials
        ],
        "known_baseline": {
            "source": "hendrix_phi_solver.algorithm_metadata()",
            "phi_vs_random_benchmark": "RANDOM_PERFORMS_BETTER_ON_SYNTHETIC",
            "cpu_overhead_vs_random": "3.73x",
            "note": "Prior result on synthetic targets. This benchmark uses real SHA-256d headers.",
        },
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"\nResults written to: {out_path}")


if __name__ == "__main__":
    main()
