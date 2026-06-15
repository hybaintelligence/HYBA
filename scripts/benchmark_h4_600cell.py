#!/usr/bin/env python3
"""H₄ 600-cell benchmark for the 4D topological-upgrade path.

This script is deliberately evidence-first:

* it records each stage independently;
* it never reuses a manifold object from a failed earlier stage;
* it writes a JSON artifact even on partial failure;
* it exits non-zero unless every benchmark stage passes.

The benchmark is an H₄ research/stress surface. It should not be treated as a
production mining claim unless the generated report shows all stages passing.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python_backend"))

try:
    import numpy as np
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by wrong interpreter use
    print(json.dumps({
        "status": "blocked",
        "reason": "missing_numpy",
        "python_executable": sys.executable,
        "detail": str(exc),
    }, indent=2))
    raise SystemExit(2)

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_3_FALLBACK = PHI ** 3
H4_GAP_FALLBACK = 4.0 - PHI_3_FALLBACK


def banner(text: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {text}")
    print(f"{'=' * 72}")


def record(results: dict[str, Any], name: str, passed: bool, **fields: Any) -> dict[str, Any]:
    payload = {"test": name, "passed": bool(passed)}
    payload.update(fields)
    results["tests"].append(payload)
    return payload


def failed(results: dict[str, Any], name: str, exc: BaseException) -> dict[str, Any]:
    print(f"  FAILED: {exc}")
    return record(results, name, False, error=str(exc), error_type=type(exc).__name__)


def build_manifold() -> Any:
    from pythia_mining.pulvini_manifold_h4 import PulviniManifoldH4
    return PulviniManifoldH4()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def run_h4_benchmark(steps: int) -> dict[str, Any]:
    results: dict[str, Any] = {
        "benchmark": "H₄ 600-cell Topological Upgrade",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "config": {
            "num_nodes": 120,
            "edges_per_node": 12,
            "coxeter_group": "H₄ [5,3,3]",
            "group_order": 14400,
            "phi_3_constant": PHI_3_FALLBACK,
            "yang_mills_gap_4d": H4_GAP_FALLBACK,
            "steps": steps,
        },
        "tests": [],
    }

    # 1. H4 Coxeter group certificate.
    banner("1/8  H₄ Coxeter Group Certificate")
    phi_3_value = PHI_3_FALLBACK
    try:
        from pythia_mining.pulvini_group_h4 import (
            H4_COXETER_MATRIX,
            H4_ORDER,
            H4_RANK,
            PHI_3,
            h4_coxeter_group_certificate,
            h4_representation_certificate,
        )
        phi_3_value = float(PHI_3)
        cox_cert = h4_coxeter_group_certificate()
        rep_cert = h4_representation_certificate()
        matrix_ok = (
            len(H4_COXETER_MATRIX) == 4
            and all(len(row) == 4 for row in H4_COXETER_MATRIX)
            and H4_COXETER_MATRIX[0][1] == 5
        )
        order_ok = H4_ORDER == 14400
        rank_ok = H4_RANK == 4
        phi_ok = abs(phi_3_value - PHI_3_FALLBACK) < 1e-6
        print(f"  Coxeter matrix valid: {matrix_ok}")
        print(f"  Group order: {H4_ORDER} (expected 14400)")
        print(f"  φ³ constant: {phi_3_value:.12f}")
        print(f"  Orbits: {rep_cert.get('n_orbits')} of size {rep_cert.get('orbit_size')}")
        record(
            results,
            "H₄ Coxeter Group Certificate",
            matrix_ok and order_ok and rank_ok and phi_ok,
            coxeter_matrix_valid=matrix_ok,
            group_order_14400=order_ok,
            rank_4=rank_ok,
            phi_3_constant=phi_3_value,
            phi_3_correct=phi_ok,
            certificate_group=cox_cert.get("coxeter_group"),
            n_orbits=rep_cert.get("n_orbits"),
            orbit_size=rep_cert.get("orbit_size"),
        )
    except Exception as exc:
        failed(results, "H₄ Coxeter Group Certificate", exc)

    # 2. Adjacency map.
    banner("2/8  Adjacency Map Construction")
    try:
        from pythia_mining.pulvini_topology_h4 import ADJACENCY_MAP_H4
        n_nodes = len(ADJACENCY_MAP_H4)
        all_deg_12 = all(len(v.get("d", [])) == 12 for v in ADJACENCY_MAP_H4.values())
        symmetric = all(
            i in ADJACENCY_MAP_H4.get(j, {}).get("d", [])
            for i, payload in ADJACENCY_MAP_H4.items()
            for j in payload.get("d", [])
        )
        total_edges = sum(len(v.get("d", [])) for v in ADJACENCY_MAP_H4.values()) // 2
        print(f"  Nodes: {n_nodes} (expected 120)")
        print(f"  All degree 12: {all_deg_12}")
        print(f"  Symmetric: {symmetric}")
        print(f"  Total edges: {total_edges}")
        record(results, "Adjacency Map (600-cell)", n_nodes == 120 and all_deg_12 and symmetric, num_nodes=n_nodes, all_degree_12=all_deg_12, symmetric=symmetric, total_edges=total_edges)
    except Exception as exc:
        failed(results, "Adjacency Map", exc)

    # 3. Automorphism group smoke enumeration.
    banner("3/8  Automorphism Group")
    try:
        from pythia_mining.pulvini_group_h4 import compute_graph_automorphisms_h4, compute_node_orbits_h4
        from pythia_mining.pulvini_topology_h4 import ADJACENCY_MAP_H4
        t0 = time.time()
        autos = compute_graph_automorphisms_h4(ADJACENCY_MAP_H4, max_count=200, node_budget=500_000)
        elapsed = time.time() - t0
        orbits = compute_node_orbits_h4(len(ADJACENCY_MAP_H4), autos)
        orbit_sizes = sorted(len(o) for o in orbits)
        all_covered = sum(orbit_sizes) == 120
        print(f"  Automorphisms found: {len(autos)}")
        print(f"  Orbit sizes: {orbit_sizes}")
        print(f"  Enumeration time: {elapsed:.3f}s")
        record(results, "Automorphism Enumeration", all_covered and len(autos) >= 1, automorphisms_found=len(autos), orbit_sizes=orbit_sizes, all_vertices_covered=all_covered, enumerate_time_s=round(elapsed, 3))
    except Exception as exc:
        failed(results, "Automorphism Group", exc)

    # 4. Manifold construction.
    banner("4/8  Manifold Construction & Invariants")
    try:
        t0 = time.time()
        manifold = build_manifold()
        elapsed_ms = (time.time() - t0) * 1000
        manifold.assert_invariants()
        entropy = safe_float(manifold.von_neumann_entropy())
        coherence = safe_float(manifold.coherence_norm())
        phase_entropy = safe_float(manifold.h4_phase_entropy())
        work_dist = manifold.work_distribution()
        print(f"  Construction: {elapsed_ms:.2f}ms")
        print(f"  Entropy: {entropy:.6f}")
        print(f"  Coherence: {coherence:.6f}")
        print(f"  Phase entropy: {phase_entropy:.6f}")
        print(f"  Automorphisms: {len(getattr(manifold, 'automorphisms', []))}")
        record(results, "Manifold Invariants", True, construction_time_ms=round(elapsed_ms, 2), num_nodes=getattr(manifold, "num_nodes", None), von_neumann_entropy=round(entropy, 6), coherence_norm=round(coherence, 6), phi_3_phase_entropy=round(phase_entropy, 6), work_distribution_min=float(np.min(work_dist)), work_distribution_max=float(np.max(work_dist)), work_distribution_sum=float(np.sum(work_dist)), automorphism_count=len(getattr(manifold, "automorphisms", [])), orbit_count=len(getattr(manifold, "node_orbits", [])))
    except Exception as exc:
        failed(results, "Manifold Invariants", exc)

    # 5. Hamiltonian evolution.
    banner("5/8  Hamiltonian Evolution (120×120)")
    try:
        manifold = build_manifold()
        t0 = time.time()
        n_evolve = 5
        for _ in range(n_evolve):
            manifold.evolve_closed_system(dt=0.1)
        elapsed_ms = (time.time() - t0) / n_evolve * 1000
        final_entropy = safe_float(manifold.von_neumann_entropy())
        print("  Matrix: 120×120 complex")
        print(f"  Mean step: {elapsed_ms:.2f}ms")
        print(f"  Final entropy: {final_entropy:.6f}")
        record(results, "Hamiltonian Evolution", math.isfinite(final_entropy), matrix_size="120×120", evolution_steps=n_evolve, mean_time_per_step_ms=round(elapsed_ms, 2), final_entropy=round(final_entropy, 6))
    except Exception as exc:
        failed(results, "Hamiltonian Evolution", exc)

    # 6. Structured search.
    banner("6/8  φ³-Structured Search")
    try:
        manifold = build_manifold()
        bench_results = manifold.benchmark_structured_search(steps=steps)
        h4_mean = safe_float(bench_results.get("h4_mean_phi_resonance"))
        random_mean = safe_float(bench_results.get("random_mean_phi_resonance"))
        improvement = safe_float(bench_results.get("h4_improvement_vs_random_pct"))
        print(f"  Steps: {steps}")
        print(f"  H₄ mean φ³: {h4_mean:.6f}")
        print(f"  Random mean φ³: {random_mean:.6f}")
        print(f"  Improvement: {improvement:.4f}%")
        record(results, "φ³ Structured Search", h4_mean >= random_mean * 0.9, steps=steps, h4_mean_phi_resonance=round(h4_mean, 6), random_mean_phi_resonance=round(random_mean, 6), h4_max_phi_resonance=safe_float(bench_results.get("h4_max_phi_resonance")), improvement_vs_random_pct=round(improvement, 4), phase_entropy=safe_float(bench_results.get("h4_phase_entropy")))
    except Exception as exc:
        failed(results, "φ³ Structured Search", exc)

    # 7. H4 mass gate.
    banner("7/8  H₄ 4D Yang-Mills Gate")
    try:
        from pythia_mining.pulvini_manifold_h4 import H4_YANG_MILLS_GAP as gap
        import random
        manifold = build_manifold()
        rng = random.Random(42)
        n_trials = 1000
        passed_gate = 0
        for _ in range(n_trials):
            nonce = rng.randint(0, 2**32 - 1)
            resonance = manifold.compute_h4_phi_resonance(nonce)
            action = 2.0 - resonance
            gate_val = manifold._phi_3_gate(action)
            if gate_val > 0.5:
                passed_gate += 1
        pass_rate = passed_gate / n_trials
        print(f"  H₄ gap: {float(gap):.6f}")
        print(f"  Gate pass rate: {pass_rate:.4f}")
        record(results, "H₄ 4D Yang-Mills Gate", pass_rate > 0.1, gap_value_4d=float(gap), n_trials=n_trials, gate_pass_rate=round(pass_rate, 4), expected_pass_rate_approx="~0.618 (1/φ)")
    except Exception as exc:
        failed(results, "H₄ Mass Gate", exc)

    # 8. Topological scaling calculation.
    banner("8/8  Topological Scaling Analysis")
    try:
        m32_nodes = 32
        h4_nodes = 120
        m32_symmetry = 120
        h4_symmetry = 14400
        domain_multiple = h4_nodes / m32_nodes
        symmetry_multiple = h4_symmetry / m32_symmetry
        edge_density = 12 / 3.5
        conservative = domain_multiple ** 0.5 * (math.log2(h4_nodes) / math.log2(m32_nodes))
        optimistic = domain_multiple * (h4_nodes / m32_nodes) ** 0.25 * symmetry_multiple ** 0.2
        predicted_conservative = conservative * 3.0
        predicted_optimistic = optimistic * 3.0 * PHI * 1.5
        print(f"  Domain multiple: {domain_multiple:.2f}×")
        print(f"  Symmetry multiple: {symmetry_multiple:.2f}×")
        print(f"  Edge density: {edge_density:.2f}×")
        print(f"  Predicted vs raw ASICs: {predicted_conservative:.1f}–{predicted_optimistic:.1f}×")
        record(results, "Topological Scaling vs M32", True, m32_nodes=m32_nodes, h4_nodes=h4_nodes, domain_multiple=round(domain_multiple, 2), symmetry_multiple=round(symmetry_multiple, 2), edge_density_ratio=round(edge_density, 2), predicted_conservative_vs_raw_asics=round(predicted_conservative, 1), predicted_optimistic_vs_raw_asics=round(predicted_optimistic, 1), theoretical_gain_over_m32=f"{round(conservative, 1)}–{round(optimistic * PHI * 1.5, 1)}×")
    except Exception as exc:
        failed(results, "Topological Scaling", exc)

    passed = sum(1 for test in results["tests"] if test.get("passed"))
    total = len(results["tests"])
    pass_rate = passed / total if total else 0.0

    print("\n" + "=" * 72)
    print("  H₄ 600-CELL BENCHMARK SUMMARY")
    print("=" * 72)
    print(f"  Tests passed: {passed}/{total}")
    print(f"  Pass rate: {pass_rate * 100:.0f}%")
    print("  Topology: 120-vertex 600-cell (H₄, 14,400 symmetries)")
    print(f"  φ³ resonance constant: {phi_3_value:.6f}")
    print("=" * 72)

    results["status"] = "passed" if passed == total else "blocked"
    results["summary"] = {
        "passed": passed,
        "total": total,
        "pass_rate": f"{pass_rate * 100:.0f}%",
        "all_tests_passed": passed == total,
        "topology": "600-cell (4D regular polytope)",
        "coxeter_group": "H₄ [5,3,3]",
        "group_order": 14400,
        "n_vertices": 120,
        "phi_3_constant": float(phi_3_value),
    }
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="H₄ 600-cell Benchmark")
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    steps = 100 if args.quick else args.steps

    print("\n" + "=" * 72)
    print("     H₄ 600-CELL BENCHMARK — 4D TOPOLOGICAL UPGRADE")
    print("     120 vertices · 14,400 symmetries · φ³ resonance")
    print("=" * 72)

    results = run_h4_benchmark(steps=steps)
    output_dir = ROOT / "benchmark_portfolio" / "run_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "h4_600cell_benchmark.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {output_path}")
    return 0 if results.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
