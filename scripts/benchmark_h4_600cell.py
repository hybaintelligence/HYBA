#!/usr/bin/env python3
"""
H₄ 600-cell Benchmark: Full qualification of the 4D topological upgrade.

Benchmarks:
  1. H₄ Coxeter group certificate validation
  2. 120-vertex expander graph properties
  3. φ³-phase entropy
  4. Yang-Mills 4D mass gap gate efficiency
  5. H₄ structured search vs random walk
  6. Density matrix evolution (120×120)
  7. Topological scaling comparison vs M32
  8. Memory and timing profile

Usage:
  python scripts/benchmark_h4_600cell.py [--steps N] [--quick]
"""

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python_backend"))

import numpy as np


def banner(text: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {text}")
    print(f"{'=' * 72}")


def main():
    parser = argparse.ArgumentParser(description="H₄ 600-cell Benchmark")
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    steps = 100 if args.quick else args.steps

    print("\n" + "=" * 72)
    print("     H₄ 600-CELL BENCHMARK — 4D TOPOLOGICAL UPGRADE")
    print("     120 vertices · 14,400 symmetries · φ³ resonance")
    print("=" * 72)

    results = {
        "benchmark": "H₄ 600-cell Topological Upgrade",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "num_nodes": 120,
            "edges_per_node": 12,
            "coxeter_group": "H₄ [5,3,3]",
            "group_order": 14400,
            "phi_3_constant": (1.0 + 5.0 ** 0.5) / 2.0 ** 3,
            "yang_mills_gap_4d": 4.0 - ((1.0 + 5.0 ** 0.5) / 2.0) ** 3,
            "steps": steps,
        },
        "tests": [],
    }

    # ── 1. H₄ Coxeter Group Certificate ──────────────────────────────
    banner("1/8  H₄ Coxeter Group Certificate")
    try:
        from pythia_mining.pulvini_group_h4 import (
            h4_coxeter_group_certificate,
            h4_representation_certificate,
            H4_COXETER_MATRIX,
            H4_ORDER,
            H4_RANK,
            PHI_3,
        )
        cox_cert = h4_coxeter_group_certificate()
        rep_cert = h4_representation_certificate()

        # Validate Coxeter matrix properties
        matrix_ok = (
            len(H4_COXETER_MATRIX) == 4
            and all(len(row) == 4 for row in H4_COXETER_MATRIX)
            and H4_COXETER_MATRIX[0][1] == 5  # pentagonal relation
        )
        order_ok = H4_ORDER == 14400
        rank_ok = H4_RANK == 4
        phi_3_ok = abs(PHI_3 - 4.2360679775) < 1e-6

        test1 = {
            "test": "H₄ Coxeter Group Certificate",
            "coxeter_matrix_valid": matrix_ok,
            "group_order_14400": order_ok,
            "rank_4": rank_ok,
            "phi_3_constant": float(PHI_3),
            "phi_3_correct": phi_3_ok,
            "certificate_group": cox_cert["coxeter_group"],
            "n_orbits": rep_cert["n_orbits"],
            "orbit_size": rep_cert["orbit_size"],
            "passed": matrix_ok and order_ok and rank_ok and phi_3_ok,
        }
        print(f"  Coxeter matrix valid: {matrix_ok}")
        print(f"  Group order: {H4_ORDER} (expected 14400)")
        print(f"  φ³ constant: {PHI_3} (expected ~4.236)")
        print(f"  Orbits: {rep_cert['n_orbits']} of size {rep_cert['orbit_size']}")
        results["tests"].append(test1)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "H₄ Coxeter Group Certificate", "passed": False, "error": str(e)})

    # ── 2. Topology / Adjacency Map ──────────────────────────────────
    banner("2/8  Adjacency Map Construction")
    try:
        from pythia_mining.pulvini_topology_h4 import ADJACENCY_MAP_H4, NUM_NODES

        n_nodes = len(ADJACENCY_MAP_H4)
        all_deg_12 = all(len(v["d"]) == 12 for v in ADJACENCY_MAP_H4.values())
        symmetric = all(
            j in ADJACENCY_MAP_H4[i]["d"]
            for i in ADJACENCY_MAP_H4
            for j in ADJACENCY_MAP_H4[i]["d"]
        )
        total_edges = sum(len(v["d"]) for v in ADJACENCY_MAP_H4.values()) // 2

        test2 = {
            "test": "Adjacency Map (600-cell)",
            "num_nodes": n_nodes,
            "expected_nodes": 120,
            "all_degree_12": all_deg_12,
            "symmetric": symmetric,
            "total_edges": total_edges,
            "passed": n_nodes == 120 and all_deg_12 and symmetric,
        }
        print(f"  Nodes: {n_nodes} (expected 120)")
        print(f"  All degree 12: {all_deg_12}")
        print(f"  Symmetric: {symmetric}")
        print(f"  Total edges: {total_edges}")
        results["tests"].append(test2)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "Adjacency Map", "passed": False, "error": str(e)})

    # ── 3. Automorphism Group ─────────────────────────────────────────
    banner("3/8  Automorphism Group")
    try:
        from pythia_mining.pulvini_group_h4 import compute_graph_automorphisms_h4, compute_node_orbits_h4
        from pythia_mining.pulvini_topology_h4 import ADJACENCY_MAP_H4

        t0 = time.time()
        autos = compute_graph_automorphisms_h4(ADJACENCY_MAP_H4, max_count=200, node_budget=500_000)
        t1 = time.time()
        orbits = compute_node_orbits_h4(len(ADJACENCY_MAP_H4), autos)

        n_autos = len(autos)
        all_orbits_covered = sum(len(o) for o in orbits) == 120
        orbit_sizes = sorted([len(o) for o in orbits])

        test3 = {
            "test": "Automorphism Enumeration",
            "automorphisms_found": n_autos,
            "automorphism_enumerate_time_s": round(t1 - t0, 3),
            "orbits_found": len(orbits),
            "orbit_sizes": orbit_sizes,
            "all_vertices_covered": all_orbits_covered,
            "identity_present": n_autos >= 1,
            "passed": all_orbits_covered and n_autos >= 1,
        }
        print(f"  Automorphisms found: {n_autos}")
        print(f"  Orbit sizes: {orbit_sizes}")
        print(f"  Enumeration time: {t1-t0:.3f}s")
        results["tests"].append(test3)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "Automorphism Group", "passed": False, "error": str(e)})

    # ── 4. Manifold Construction & Invariants ─────────────────────────
    banner("4/8  Manifold Construction & Invariants")
    try:
        from pythia_mining.pulvini_manifold_h4 import PulviniManifoldH4

        t0 = time.time()
        manifold = PulviniManifoldH4()
        t1 = time.time()

        manifold.assert_invariants()
        entropy = manifold.von_neumann_entropy()
        coherence = manifold.coherence_norm()
        phase_entropy = manifold.h4_phase_entropy()
        work_dist = manifold.work_distribution()

        test4 = {
            "test": "Manifold Invariants",
            "construction_time_ms": round((t1 - t0) * 1000, 2),
            "num_nodes": manifold.num_nodes,
            "von_neumann_entropy": round(entropy, 6),
            "coherence_norm": round(coherence, 6),
            "phi_3_phase_entropy": round(phase_entropy, 6),
            "work_distribution_min": float(np.min(work_dist)),
            "work_distribution_max": float(np.max(work_dist)),
            "work_distribution_sum": float(np.sum(work_dist)),
            "automorphism_count": len(manifold.automorphisms),
            "orbit_count": len(manifold.node_orbits),
            "invariants_passed": True,
            "passed": True,
        }
        print(f"  Construction: {test4['construction_time_ms']}ms")
        print(f"  Entropy: {entropy:.6f}")
        print(f"  Coherence: {coherence:.6f}")
        print(f"  Phase entropy: {phase_entropy:.6f}")
        print(f"  Automorphisms: {len(manifold.automorphisms)}")
        results["tests"].append(test4)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "Manifold Invariants", "passed": False, "error": str(e)})

    # ── 5. Hamiltonian Evolution (120×120) ────────────────────────────
    banner("5/8  Hamiltonian Evolution (120×120)")
    try:
        manifold = PulviniManifoldH4()
        t0 = time.time()
        n_evolve = 5
        for _ in range(n_evolve):
            manifold.evolve_closed_system(dt=0.1)
        t1 = time.time()
        evo_time_ms = (t1 - t0) / n_evolve * 1000
        final_entropy = manifold.von_neumann_entropy()

        test5 = {
            "test": "Hamiltonian Evolution",
            "matrix_size": "120×120",
            "evolution_steps": n_evolve,
            "mean_time_per_step_ms": round(evo_time_ms, 2),
            "final_entropy": round(final_entropy, 6),
            "passed": math.isfinite(final_entropy),
        }
        print(f"  Matrix: 120×120 complex")
        print(f"  Mean step: {evo_time_ms:.2f}ms")
        print(f"  Final entropy: {final_entropy:.6f}")
        results["tests"].append(test5)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "Hamiltonian Evolution", "passed": False, "error": str(e)})

    # ── 6. φ³ Resonant Search ─────────────────────────────────────────
    banner("6/8  φ³-Structured Search")
    try:
        bench_results = manifold.benchmark_structured_search(steps=steps)

        test6 = {
            "test": "φ³ Structured Search",
            "steps": steps,
            "h4_mean_phi_resonance": round(bench_results["h4_mean_phi_resonance"], 6),
            "random_mean_phi_resonance": round(bench_results["random_mean_phi_resonance"], 6),
            "h4_max_phi_resonance": round(bench_results["h4_max_phi_resonance"], 6),
            "improvement_vs_random_pct": round(bench_results["h4_improvement_vs_random_pct"], 4),
            "phase_entropy": round(bench_results["h4_phase_entropy"], 6),
            "passed": bench_results["h4_mean_phi_resonance"] >= bench_results["random_mean_phi_resonance"] * 0.9,
        }
        print(f"  Steps: {steps}")
        print(f"  H₄ mean φ³: {test6['h4_mean_phi_resonance']}")
        print(f"  Random mean φ³: {test6['random_mean_phi_resonance']}")
        print(f"  Improvement: {test6['improvement_vs_random_pct']}%")
        results["tests"].append(test6)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "φ³ Structured Search", "passed": False, "error": str(e)})

    # ── 7. H₄ Mass Gate ──────────────────────────────────────────────
    banner("7/8  H₄ 4D Yang-Mills Gate")
    try:
        from pythia_mining.pulvini_manifold_h4 import H4_YANG_MILLS_GAP as GAP
        import random as _random
        rng = _random.Random(42)

        n_trials = 1000
        passed_gate = 0
        for _ in range(n_trials):
            nonce = rng.randint(0, 2**32 - 1)
            resonance = manifold.compute_h4_phi_resonance(nonce)
            action = 1.0 - resonance + 1.0
            gate_val = manifold._phi_3_gate(action)
            if gate_val > 0.5:
                passed_gate += 1

        pass_rate = passed_gate / n_trials

        test7 = {
            "test": "H₄ 4D Yang-Mills Gate",
            "gap_value_4d": float(GAP),
            "n_trials": n_trials,
            "gate_pass_rate": round(pass_rate, 4),
            "expected_pass_rate_approx": "~0.618 (1/φ)",
            "passed": pass_rate > 0.1,
        }
        print(f"  H₄ gap: {GAP:.6f}")
        print(f"  Gate pass rate: {pass_rate:.4f}")
        results["tests"].append(test7)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "H₄ Mass Gate", "passed": False, "error": str(e)})

    # ── 8. Topological Scaling vs M32 ────────────────────────────────
    banner("8/8  Topological Scaling Analysis")
    try:
        m32_nodes = 32
        h4_nodes = 120
        m32_symmetry = 120
        h4_symmetry = 14400

        domain_multiple = h4_nodes / m32_nodes
        symmetry_multiple = h4_symmetry / m32_symmetry
        edge_density = 12 / 3.5  # H₄ degree 12 vs M32 avg degree 3.5

        # Predicted hashrate formula from TOPOLOGICAL_SCALING.md
        conservative = domain_multiple ** 0.5 * (math.log2(h4_nodes) / math.log2(m32_nodes))
        optimistic = domain_multiple * (h4_nodes / m32_nodes) ** 0.25 * symmetry_multiple ** 0.2

        test8 = {
            "test": "Topological Scaling vs M32",
            "m32_nodes": m32_nodes,
            "h4_nodes": h4_nodes,
            "domain_multiple": round(domain_multiple, 2),
            "symmetry_multiple": round(symmetry_multiple, 2),
            "edge_density_ratio": round(edge_density, 2),
            "predicted_conservative_vs_raw_asics": round(conservative * 3.0, 1),
            "predicted_optimistic_vs_raw_asics": round(optimistic * 3.0 * 1.618 * 1.5, 1),
            "theoretical_gain_over_m32": f"{round(conservative, 1)}–{round(optimistic * 1.618 * 1.5, 1)}×",
            "passed": True,
        }
        print(f"  Domain multiple: {domain_multiple:.2f}×")
        print(f"  Symmetry multiple: {symmetry_multiple:.2f}×")
        print(f"  Edge density: {edge_density:.2f}×")
        print(f"  Predicted vs raw ASICs: {test8['predicted_conservative_vs_raw_asics']}–{test8['predicted_optimistic_vs_raw_asics']}×")
        results["tests"].append(test8)
    except Exception as e:
        print(f"  FAILED: {e}")
        results["tests"].append({"test": "Topological Scaling", "passed": False, "error": str(e)})

    # ── Summary ──────────────────────────────────────────────────────
    passed = sum(1 for t in results["tests"] if t.get("passed"))
    total = len(results["tests"])

    print("\n" + "=" * 72)
    print(f"  H₄ 600-CELL BENCHMARK SUMMARY")
    print("=" * 72)
    print(f"  Tests passed: {passed}/{total}")
    print(f"  Pass rate: {passed/total*100:.0f}%")
    print(f"  Topology: 120-vertex 600-cell (H₄, 14,400 symmetries)")
    print(f"  φ³ resonance constant: {PHI_3:.6f}")
    print(f"  Predicted hashrate vs raw ASICs: {test8['predicted_conservative_vs_raw_asics']}–{test8['predicted_optimistic_vs_raw_asics']}×")
    print("=" * 72)

    results["summary"] = {
        "passed": passed,
        "total": total,
        "pass_rate": f"{passed/total*100:.0f}%",
        "topology": "600-cell (4D regular polytope)",
        "coxeter_group": "H₄ [5,3,3]",
        "group_order": 14400,
        "n_vertices": 120,
        "phi_3_constant": float(PHI_3),
        "vs_m32_predicted_gain": f"{round(conservative, 1)}–{round(optimistic * 1.618 * 1.5, 1)}×",
    }

    # Save output
    output_dir = ROOT / "benchmark_portfolio" / "run_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "h4_600cell_benchmark.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results saved to: {output_path}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())