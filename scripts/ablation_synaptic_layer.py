"""
ablation_synaptic_layer.py

Ablation study: does the Synaptic Persistence Layer actually improve
hit rates, or does it only record patterns without changing outcomes?

Design:
  - Two conditions run over N epochs:
      A (baseline):  pure φ-tiled 32-sector search, no learning
      B (synaptic):  same search, but after each accepted share the
                     successful nonce pattern is reinforced; subsequent
                     nonce selection biases toward high-weight patterns

  - Each epoch: equal iteration budget per solver per condition
  - After each epoch, measure:
      * hits (valid nonces found)
      * first_hit_iteration
      * synaptic state (B only): emergent_pathway_count, mean_weight

  - Falsifiable prediction:
      After sufficient reinforcement epochs, condition B first_hit_iteration
      should decrease as the synaptic layer learns where valid nonces cluster.

  - Null hypothesis:
      Synaptic layer produces no measurable difference in hit rate or
      first_hit_iteration vs baseline after N epochs.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.golden_ratio_library import PHI
from pythia_mining.hendrix_phi_solver import cheap_phi_resonance, voronoi_domain
from pythia_mining.synaptic_persistence_layer import SynapticPersistenceLayer
from pythia_mining.mining_validation import (
    build_block_header,
    compute_merkle_root,
    coinbase_hash_hex,
)
from pythia_mining.stratum_client import MiningJob

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UINT32 = 2**32
N_SOLVERS = 32
SECTOR_SIZE = UINT32 // N_SOLVERS
PHI_STRIDE = int(SECTOR_SIZE / PHI)


# ---------------------------------------------------------------------------
# SHA-256d
# ---------------------------------------------------------------------------


def _make_job(target: int) -> MiningJob:
    return MiningJob(
        job_id="ablation",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="5e9a5c00",
        target=target,
        extranonce1="abcd1234",
        extranonce2_size=4,
    )


def _prefix(job: MiningJob) -> bytes:
    cb = coinbase_hash_hex(job, "00000000")
    root = compute_merkle_root(cb, job.merkle_branch)
    return build_block_header(job, root, 0)[:76]


def _valid(prefix: bytes, nonce: int, target: int) -> bool:
    header = prefix + nonce.to_bytes(4, "little")
    digest = hashlib.sha256(hashlib.sha256(header).digest()).digest()
    return int.from_bytes(digest, "little") <= target


# ---------------------------------------------------------------------------
# Nonce generators
# ---------------------------------------------------------------------------


def _phi_sector_nonces(solver_id: int, step: int, n: int) -> List[int]:
    """Generate n nonces for solver_id at epoch step using φ-stride."""
    start = solver_id * SECTOR_SIZE
    return [start + ((step * n + i) * PHI_STRIDE) % SECTOR_SIZE for i in range(n)]


def _synaptic_biased_nonces(
    solver_id: int,
    step: int,
    n: int,
    synaptic: SynapticPersistenceLayer,
    bias_fraction: float = 0.3,
) -> List[int]:
    """
    Generate n nonces with synaptic bias.

    bias_fraction of candidates are drawn from sectors suggested by
    high-weight emergent pathways. The rest are standard φ-stride.
    This is the mechanism: the synaptic layer influences WHERE we search.
    """
    base = _phi_sector_nonces(solver_id, step, n)
    pathways = synaptic.get_emergent_pathways()
    if not pathways:
        return base  # No pathways yet — identical to baseline

    n_biased = max(1, int(n * bias_fraction))
    biased: List[int] = []

    for pattern_id, weight in pathways[:n_biased]:
        if pattern_id not in synaptic.synaptic_memory:
            continue
        trace = synaptic.synaptic_memory[pattern_id]
        # Search near the successful nonce's sector
        base_nonce = trace.pattern.nonce
        # φ-stride around the successful region
        sector = (base_nonce // SECTOR_SIZE) * SECTOR_SIZE
        candidate = sector + (step * PHI_STRIDE) % SECTOR_SIZE
        biased.append(candidate % UINT32)
        if len(biased) >= n_biased:
            break

    # Pad with standard φ-stride if not enough pathways
    while len(biased) < n_biased:
        biased.append(base[len(biased)])

    return biased + base[n_biased:]


# ---------------------------------------------------------------------------
# Epoch runner
# ---------------------------------------------------------------------------


@dataclass
class EpochResult:
    epoch: int
    condition: str  # "baseline" or "synaptic"
    hits: int
    iterations: int
    first_hit_iteration: Optional[int]
    hashes_per_second: float
    synaptic_pathways: int  # 0 for baseline
    synaptic_mean_weight: float
    synaptic_reinforcements: int


def run_epoch(
    epoch: int,
    condition: str,
    prefix: bytes,
    target: int,
    iters_per_solver: int,
    synaptic: Optional[SynapticPersistenceLayer] = None,
) -> EpochResult:
    hits = 0
    first_hit: Optional[int] = None
    total_iters = 0

    t0 = time.perf_counter()

    for solver_id in range(N_SOLVERS):
        if condition == "synaptic" and synaptic is not None:
            nonces = _synaptic_biased_nonces(
                solver_id, epoch, iters_per_solver, synaptic
            )
        else:
            nonces = _phi_sector_nonces(solver_id, epoch, iters_per_solver)

        for local_i, nonce in enumerate(nonces):
            global_i = solver_id * iters_per_solver + local_i + 1
            if _valid(prefix, nonce, target):
                hits += 1
                if first_hit is None:
                    first_hit = global_i

                # Reinforce in synaptic layer if condition B
                if condition == "synaptic" and synaptic is not None:
                    phi_res = cheap_phi_resonance(nonce)
                    sector = voronoi_domain(nonce)
                    # Use register_or_reinforce for sector-level accumulation
                    synaptic.register_or_reinforce(
                        nonce=nonce,
                        phi_resonance=phi_res,
                        dodecahedral_sector=sector % 32,
                        icosahedral_face=sector % 20,
                        golden_angle_alignment=phi_res,
                    )

            total_iters += 1

    elapsed = time.perf_counter() - t0

    # Apply decay at end of epoch
    if condition == "synaptic" and synaptic is not None:
        synaptic.apply_decay()
        stats = synaptic.get_statistics()
        pathways = stats["emergent_pathway_count"]
        mean_w = stats["average_synaptic_weight"]
        reinforcements = stats["total_reinforcements"]
    else:
        pathways = 0
        mean_w = 0.0
        reinforcements = 0

    return EpochResult(
        epoch=epoch,
        condition=condition,
        hits=hits,
        iterations=total_iters,
        first_hit_iteration=first_hit,
        hashes_per_second=total_iters / max(elapsed, 1e-9),
        synaptic_pathways=pathways,
        synaptic_mean_weight=mean_w,
        synaptic_reinforcements=reinforcements,
    )


# ---------------------------------------------------------------------------
# Ablation runner
# ---------------------------------------------------------------------------


def run_ablation(
    n_epochs: int = 10,
    iters_per_solver: int = 2_000,
    target: Optional[int] = None,
) -> dict:
    if target is None:
        target = int("00" + "ff" * 31, 16)  # ~1/256 hit probability

    job = _make_job(target)
    prefix = _prefix(job)
    synaptic = SynapticPersistenceLayer(
        learning_rate=0.15,
        decay_rate=0.005,  # slow decay so patterns persist across epochs
        synaptic_threshold=0.3,
    )

    baseline_results: List[EpochResult] = []
    synaptic_results: List[EpochResult] = []

    total_iters = N_SOLVERS * iters_per_solver

    print(f"Ablation: {n_epochs} epochs × {total_iters:,} iters/epoch")
    print("Condition A: baseline (no learning)")
    print("Condition B: synaptic Hebbian layer (learning_rate=0.15, decay=0.005)\n")
    print(
        f"{'Epoch':>5}  {'A hits':>7} {'A 1stHit':>9}  {'B hits':>7} {'B 1stHit':>9}  "
        f"{'Pathways':>9} {'MeanW':>7}"
    )
    print("-" * 70)

    for epoch in range(n_epochs):
        a = run_epoch(epoch, "baseline", prefix, target, iters_per_solver)
        b = run_epoch(epoch, "synaptic", prefix, target, iters_per_solver, synaptic)

        baseline_results.append(a)
        synaptic_results.append(b)

        a_fh = f"{a.first_hit_iteration}" if a.first_hit_iteration else "none"
        b_fh = f"{b.first_hit_iteration}" if b.first_hit_iteration else "none"

        print(
            f"{epoch + 1:>5}  {a.hits:>7} {a_fh:>9}  {b.hits:>7} {b_fh:>9}  "
            f"{b.synaptic_pathways:>9} {b.synaptic_mean_weight:>7.4f}"
        )

    # Aggregate
    def _mean(results, attr):
        vals = [getattr(r, attr) for r in results if getattr(r, attr) is not None]
        return sum(vals) / len(vals) if vals else None

    def _mean_fhi(results):
        vals = [
            r.first_hit_iteration for r in results if r.first_hit_iteration is not None
        ]
        return sum(vals) / len(vals) if vals else None

    a_hits = _mean(baseline_results, "hits")
    b_hits = _mean(synaptic_results, "hits")
    a_fhi = _mean_fhi(baseline_results)
    b_fhi = _mean_fhi(synaptic_results)
    a_hps = _mean(baseline_results, "hashes_per_second")
    b_hps = _mean(synaptic_results, "hashes_per_second")

    # Late-epoch comparison (last 30% of epochs — after learning has accumulated)
    cutoff = max(1, int(n_epochs * 0.7))
    a_late_fhi = _mean_fhi(baseline_results[cutoff:])
    b_late_fhi = _mean_fhi(synaptic_results[cutoff:])
    a_late_hits = _mean(baseline_results[cutoff:], "hits")
    b_late_hits = _mean(synaptic_results[cutoff:], "hits")

    final_pathways = synaptic_results[-1].synaptic_pathways
    final_mean_w = synaptic_results[-1].synaptic_mean_weight

    print("\n--- ABLATION RESULTS ---")
    print("\nAll epochs:")
    print(
        f"  Baseline  — mean hits: {a_hits:.1f}  mean first_hit: {f'{a_fhi:.0f}' if a_fhi else 'none'}"
        f"  kH/s: {a_hps / 1000:.0f}"
    )
    print(
        f"  Synaptic  — mean hits: {b_hits:.1f}  mean first_hit: {f'{b_fhi:.0f}' if b_fhi else 'none'}"
        f"  kH/s: {b_hps / 1000:.0f}"
    )

    print(f"\nLate epochs (epoch {cutoff + 1}–{n_epochs}, after learning accumulates):")
    print(
        f"  Baseline  — hits: {a_late_hits:.1f}  first_hit: {f'{a_late_fhi:.0f}' if a_late_fhi else 'none'}"
    )
    print(
        f"  Synaptic  — hits: {b_late_hits:.1f}  first_hit: {f'{b_late_fhi:.0f}' if b_late_fhi else 'none'}"
    )
    print(f"  Emergent pathways: {final_pathways}  mean weight: {final_mean_w:.4f}")

    # Verdict
    print("\n--- VERDICT ---")
    null_rejected = False

    if b_late_fhi and a_late_fhi and b_late_fhi < a_late_fhi * 0.90:
        print("✅ NULL HYPOTHESIS REJECTED (first_hit)")
        print(
            f"   Synaptic first_hit {b_late_fhi:.0f} vs baseline {a_late_fhi:.0f} "
            f"({a_late_fhi / b_late_fhi:.2f}x faster in late epochs)"
        )
        null_rejected = True
    elif b_late_hits and a_late_hits and b_late_hits > a_late_hits * 1.05:
        print("✅ NULL HYPOTHESIS REJECTED (hit rate)")
        print(
            f"   Synaptic hits {b_late_hits:.1f} vs baseline {a_late_hits:.1f} "
            f"in late epochs ({b_late_hits / a_late_hits:.2f}x)"
        )
        null_rejected = True
    else:
        print("❌ NULL HYPOTHESIS STANDS")
        print("   No significant improvement in hit rate or first_hit in late epochs.")
        if final_pathways == 0:
            print(
                "   Synaptic layer formed 0 emergent pathways — "
                "not enough accepted shares to learn from at this difficulty/budget."
            )
            print(
                "   Recommendation: increase iterations or lower difficulty "
                "to generate sufficient reinforcement signal."
            )

    result = {
        "benchmark": "synaptic_layer_ablation",
        "config": {
            "n_epochs": n_epochs,
            "iters_per_solver": iters_per_solver,
            "total_iters_per_epoch": total_iters,
            "target_hex": f"{target:064x}",
            "learning_rate": synaptic.learning_rate,
            "decay_rate": synaptic.decay_rate,
            "synaptic_threshold": synaptic.synaptic_threshold,
        },
        "all_epochs": {
            "baseline_mean_hits": a_hits,
            "synaptic_mean_hits": b_hits,
            "baseline_mean_first_hit": a_fhi,
            "synaptic_mean_first_hit": b_fhi,
        },
        "late_epochs": {
            "cutoff_epoch": cutoff,
            "baseline_hits": a_late_hits,
            "synaptic_hits": b_late_hits,
            "baseline_first_hit": a_late_fhi,
            "synaptic_first_hit": b_late_fhi,
            "final_emergent_pathways": final_pathways,
            "final_mean_weight": final_mean_w,
        },
        "null_hypothesis_rejected": null_rejected,
        "epochs": [
            {
                "epoch": r.epoch + 1,
                "baseline": {
                    "hits": baseline_results[r.epoch].hits,
                    "first_hit": baseline_results[r.epoch].first_hit_iteration,
                },
                "synaptic": {
                    "hits": r.hits,
                    "first_hit": r.first_hit_iteration,
                    "pathways": r.synaptic_pathways,
                    "mean_weight": r.synaptic_mean_weight,
                },
            }
            for r in synaptic_results
        ],
    }

    out = ROOT / "artifacts" / f"ablation_synaptic_{int(time.time())}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    print(f"\nResults → {out}")
    return result


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument(
        "--iterations", type=int, default=2000, help="Iterations per solver per epoch"
    )
    p.add_argument(
        "--difficulty",
        type=float,
        default=None,
        help="Override target difficulty (lower = easier = more hits)",
    )
    args = p.parse_args()

    target = None
    if args.difficulty is not None:
        MAX_T = int("00000000ffff" + "0" * 52, 16)
        target = max(1, int(MAX_T / args.difficulty))

    run_ablation(n_epochs=args.epochs, iters_per_solver=args.iterations, target=target)
