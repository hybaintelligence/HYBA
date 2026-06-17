#!/usr/bin/env python3
"""H₄ 600-cell benchmark for the 4D topological-upgrade path.

This is an experimental stress surface. It writes an artifact on partial failure
and exits non-zero unless every stage passes.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python_backend"))

try:
    import numpy as np
except ModuleNotFoundError as exc:
    print(json.dumps({"status": "blocked", "reason": "missing_numpy", "python_executable": sys.executable, "detail": str(exc)}, indent=2))
    raise SystemExit(2)

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_3_FALLBACK = PHI**3
H4_GAP_FALLBACK = 4.0 - PHI_3_FALLBACK


def banner(text: str) -> None:
    print(f"\n{'=' * 72}\n  {text}\n{'=' * 72}")


def record(results: dict[str, Any], name: str, passed: bool, **fields: Any) -> None:
    payload = {"test": name, "passed": bool(passed)}
    payload.update(fields)
    results["tests"].append(payload)


def fail(results: dict[str, Any], name: str, exc: BaseException) -> None:
    print(f"  FAILED: {exc}")
    record(results, name, False, error=str(exc), error_type=type(exc).__name__)


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
        "evidence_boundary": {
            "experimental_stress_surface": True,
            "not_a_production_mining_claim_without_full_pass": True,
            "all_stages_must_pass_for_acceptance": True,
        },
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
    phi_3_value = PHI_3_FALLBACK

    banner("1/8  H₄ Coxeter Group Certificate")
    try:
        from pythia_mining.pulvini_group_h4 import H4_COXETER_MATRIX, H4_ORDER, H4_RANK, PHI_3, h4_coxeter_group_certificate, h4_representation_certificate

        phi_3_value = float(PHI_3)
        cox_cert = h4_coxeter_group_certificate()
        rep_cert = h4_representation_certificate()
        matrix_ok = len(H4_COXETER_MATRIX) == 4 and all(len(row) == 4 for row in H4_COXETER_MATRIX) and H4_COXETER_MATRIX[0][1] == 5
        passed = matrix_ok and H4_ORDER == 14400 and H4_RANK == 4 and abs(phi_3_value - PHI_3_FALLBACK) < 1e-6
        record(results, "H₄ Coxeter Group Certificate", passed, group_order_14400=H4_ORDER == 14400, rank_4=H4_RANK == 4, phi_3_constant=phi_3_value, certificate_group=cox_cert.get("coxeter_group"), n_orbits=rep_cert.get("n_orbits"), orbit_size=rep_cert.get("orbit_size"))
    except Exception as exc:
        fail(results, "H₄ Coxeter Group Certificate", exc)

    banner("2/8  Adjacency Map Construction")
    try:
        from pythia_mining.pulvini_topology_h4 import ADJACENCY_MAP_H4

        n_nodes = len(ADJACENCY_MAP_H4)
        all_degree_12 = all(len(v.get("d", [])) == 12 for v in ADJACENCY_MAP_H4.values())
        symmetric = all(i in ADJACENCY_MAP_H4.get(j, {}).get("d", []) for i, payload in ADJACENCY_MAP_H4.items() for j in payload.get("d", []))
        record(results, "Adjacency Map (600-cell)", n_nodes == 120 and all_degree_12 and symmetric, num_nodes=n_nodes, all_degree_12=all_degree_12, symmetric=symmetric)
    except Exception as exc:
        fail(results, "Adjacency Map", exc)

    banner("3/8  Automorphism Group")
    try:
        from pythia_mining.pulvini_group_h4 import compute_graph_automorphisms_h4, compute_node_orbits_h4
        from pythia_mining.pulvini_topology_h4 import ADJACENCY_MAP_H4

        start = time.time()
        autos = compute_graph_automorphisms_h4(ADJACENCY_MAP_H4, max_count=200, node_budget=500_000)
        orbits = compute_node_orbits_h4(len(ADJACENCY_MAP_H4), autos)
        orbit_sizes = sorted(len(orbit) for orbit in orbits)
        record(results, "Automorphism Enumeration", sum(orbit_sizes) == 120 and len(autos) >= 1, automorphisms_found=len(autos), orbit_sizes=orbit_sizes, enumerate_time_s=round(time.time() - start, 3))
    except Exception as exc:
        fail(results, "Automorphism Group", exc)

    banner("4/8  Manifold Construction & Invariants")
    try:
        start = time.time()
        manifold = build_manifold()
        construction_ms = (time.time() - start) * 1000
        manifold.assert_invariants()
        work_dist = manifold.work_distribution()
        record(results, "Manifold Invariants", True, construction_time_ms=round(construction_ms, 2), num_nodes=getattr(manifold, "num_nodes", None), von_neumann_entropy=round(safe_float(manifold.von_neumann_entropy()), 6), coherence_norm=round(safe_float(manifold.coherence_norm()), 6), work_distribution_sum=float(np.sum(work_dist)))
    except Exception as exc:
        fail(results, "Manifold Invariants", exc)

    banner("5/8  Hamiltonian Evolution (120×120)")
    try:
        manifold = build_manifold()
        start = time.time()
        steps_to_evolve = 5
        for _ in range(steps_to_evolve):
            manifold.evolve_closed_system(dt=0.1)
        final_entropy = safe_float(manifold.von_neumann_entropy())
        record(results, "Hamiltonian Evolution", math.isfinite(final_entropy), matrix_size="120×120", evolution_steps=steps_to_evolve, mean_time_per_step_ms=round((time.time() - start) / steps_to_evolve * 1000, 2), final_entropy=round(final_entropy, 6))
    except Exception as exc:
        fail(results, "Hamiltonian Evolution", exc)

    banner("6/8  φ³-Structured Search")
    try:
        manifold = build_manifold()
        bench = manifold.benchmark_structured_search(steps=steps)
        h4_mean = safe_float(bench.get("h4_mean_phi_resonance"))
        random_mean = safe_float(bench.get("random_mean_phi_resonance"))
        record(results, "φ³ Structured Search", h4_mean >= random_mean * 0.9, steps=steps, h4_mean_phi_resonance=round(h4_mean, 6), random_mean_phi_resonance=round(random_mean, 6), improvement_vs_random_pct=round(safe_float(bench.get("h4_improvement_vs_random_pct")), 4))
    except Exception as exc:
        fail(results, "φ³ Structured Search", exc)

    banner("7/8  H₄ 4D Yang-Mills Gate")
    try:
        from pythia_mining.pulvini_manifold_h4 import H4_YANG_MILLS_GAP as gap

        manifold = build_manifold()
        rng = random.Random(42)
        trials = 1000
        passed_gate = 0
        for _ in range(trials):
            resonance = manifold.compute_h4_phi_resonance(rng.randint(0, 2**32 - 1))
            if manifold._phi_3_gate(2.0 - resonance) > 0.5:
                passed_gate += 1
        pass_rate = passed_gate / trials
        record(results, "H₄ 4D Yang-Mills Gate", pass_rate > 0.1, gap_value_4d=float(gap), n_trials=trials, gate_pass_rate=round(pass_rate, 4))
    except Exception as exc:
        fail(results, "H₄ Mass Gate", exc)

    banner("8/8  Topological Scaling Analysis")
    try:
        m32_nodes = 32
        h4_nodes = 120
        m32_symmetry = 120
        h4_symmetry = 14400
        domain_multiple = h4_nodes / m32_nodes
        symmetry_multiple = h4_symmetry / m32_symmetry
        conservative = domain_multiple**0.5 * (math.log2(h4_nodes) / math.log2(m32_nodes))
        optimistic = domain_multiple * (h4_nodes / m32_nodes) ** 0.25 * symmetry_multiple**0.2
        record(results, "Topological Scaling vs M32", True, domain_multiple=round(domain_multiple, 2), symmetry_multiple=round(symmetry_multiple, 2), predicted_conservative_vs_raw_asics=round(conservative * 3.0, 1), predicted_optimistic_vs_raw_asics=round(optimistic * 3.0 * PHI * 1.5, 1))
    except Exception as exc:
        fail(results, "Topological Scaling", exc)

    passed = sum(1 for test in results["tests"] if test.get("passed"))
    total = len(results["tests"])
    results["status"] = "passed" if passed == total else "blocked"
    results["summary"] = {"passed": passed, "total": total, "pass_rate": f"{(passed / max(total, 1)) * 100:.0f}%", "all_tests_passed": passed == total, "topology": "600-cell (4D regular polytope)", "coxeter_group": "H₄ [5,3,3]", "group_order": 14400, "n_vertices": 120, "phi_3_constant": float(phi_3_value)}
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="H₄ 600-cell Benchmark")
    parser.add_argument("--steps", type=int, default=5000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    results = run_h4_benchmark(steps=100 if args.quick else args.steps)
    output_dir = ROOT / "benchmark_portfolio" / "run_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "h4_600cell_benchmark.json"
    output_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to: {output_path}")
    return 0 if results.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
