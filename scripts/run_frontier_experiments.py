#!/usr/bin/env python3
"""Execute all four frontier science experiments.

This script runs the complete frontier experimental suite that tests
fundamental connections between:
1. Number theory (star-discrepancy)
2. Gauge theory (SU(2) topology)
3. Quantum information geometry (Bures metric, QFI)
4. Quantum metrology (measurement precision)

Each experiment is falsifiable with defined breakthrough thresholds.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))

from pythia_mining.frontier_experiment_1_qmc_convergence import (
    run_comparative_benchmark as run_exp1,
    get_experiment_metadata as meta1,
)
from pythia_mining.frontier_experiment_2_qfi_truncation import (
    run_comparative_truncation_benchmark as run_exp2,
    get_experiment_metadata as meta2,
)
from pythia_mining.frontier_experiment_3_topological_correlation import (
    run_comparative_phi_vs_random_topology as run_exp3,
    get_experiment_metadata as meta3,
)
from pythia_mining.frontier_experiment_4_golden_sld import (
    run_golden_sld_correlation_experiment as run_exp4,
    get_experiment_metadata as meta4,
)


def print_section_header(title: str):
    """Print formatted section header."""
    print("\n")
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_experiment_metadata(metadata: dict):
    """Print experiment metadata."""
    print(f"Experiment ID: {metadata['experiment_id']}")
    print(f"Hypothesis: {metadata['hypothesis']}")
    print(f"Falsifiability: {metadata['falsifiability']}")
    print(f"Rejection criterion: {metadata['rejection_criterion']}")
    print(f"Breakthrough threshold: {metadata['breakthrough_threshold']}")
    print()


def run_all_frontier_experiments():
    """Execute all four frontier experiments in sequence."""
    print_section_header("FRONTIER SCIENCE EXPERIMENTAL SUITE")
    print("Ἀνερρίφθω κύβος — The die is cast")
    print("Testing fundamental connections at the boundary of physics")
    print()

    results = {}

    # =========================================================================
    # EXPERIMENT 1: φ-QMC vs MCMC Convergence
    # =========================================================================
    print_section_header("EXPERIMENT 1: φ-QMC vs Standard MCMC Convergence")
    meta = meta1()
    print_experiment_metadata(meta)

    try:
        phi_metrics_1, prng_metrics_1, analysis_1 = run_exp1(
            max_samples=10_000,  # Reasonable for demonstration
            convergence_threshold=0.01,
            vacuum_target=0.5,
        )
        results["experiment_1"] = {
            "status": "completed",
            "analysis": analysis_1,
            "breakthrough": analysis_1["breakthrough_achieved"],
        }
    except Exception as e:
        print(f"⚠️  Experiment 1 failed: {e}")
        results["experiment_1"] = {"status": "failed", "error": str(e)}

    # =========================================================================
    # EXPERIMENT 2: QFI-Preserving MPS Truncation
    # =========================================================================
    print_section_header("EXPERIMENT 2: QFI-Preserving MPS Truncation")
    meta = meta2()
    print_experiment_metadata(meta)

    try:
        qfi_metrics_2, standard_metrics_2, analysis_2 = run_exp2(
            num_sites=15,
            initial_bond=24,
            target_bond=6,
        )
        results["experiment_2"] = {
            "status": "completed",
            "analysis": analysis_2,
            "breakthrough": analysis_2["breakthrough_achieved"],
        }
    except Exception as e:
        print(f"⚠️  Experiment 2 failed: {e}")
        results["experiment_2"] = {"status": "failed", "error": str(e)}

    # =========================================================================
    # EXPERIMENT 3: Topological Charge Correlation
    # =========================================================================
    print_section_header("EXPERIMENT 3: Star-Discrepancy ↔ Topological Charge")
    meta = meta3()
    print_experiment_metadata(meta)

    try:
        phi_analysis_3, random_analysis_3 = run_exp3()
        results["experiment_3"] = {
            "status": "completed",
            "phi_analysis": phi_analysis_3,
            "random_analysis": random_analysis_3,
            "breakthrough": phi_analysis_3["breakthrough_achieved"],
        }
    except Exception as e:
        print(f"⚠️  Experiment 3 failed: {e}")
        results["experiment_3"] = {"status": "failed", "error": str(e)}

    # =========================================================================
    # EXPERIMENT 4: Golden SLD (Discrepancy-QFI)
    # =========================================================================
    print_section_header("EXPERIMENT 4: Golden SLD — Discrepancy-QFI Relationship")
    meta = meta4()
    print_experiment_metadata(meta)

    try:
        points_4, analysis_4 = run_exp4(
            sample_sizes=[100, 500, 1000, 2000, 5000],
        )
        results["experiment_4"] = {
            "status": "completed",
            "analysis": analysis_4,
            "breakthrough": analysis_4["breakthrough_achieved"],
        }
    except Exception as e:
        print(f"⚠️  Experiment 4 failed: {e}")
        results["experiment_4"] = {"status": "failed", "error": str(e)}

    # =========================================================================
    # FINAL SUMMARY
    # =========================================================================
    print_section_header("FRONTIER EXPERIMENTAL SUITE — FINAL SUMMARY")

    completed = sum(1 for r in results.values() if r.get("status") == "completed")
    breakthroughs = sum(1 for r in results.values() if r.get("breakthrough", False))

    print(f"Experiments completed: {completed}/4")
    print(f"Breakthroughs achieved: {breakthroughs}/4")
    print()

    for exp_id, result in results.items():
        status_symbol = "✓" if result.get("status") == "completed" else "✗"
        breakthrough_symbol = "🏆" if result.get("breakthrough", False) else " "
        print(
            f"{status_symbol} {breakthrough_symbol} {exp_id}: {result.get('status', 'unknown')}"
        )

    print()

    if breakthroughs > 0:
        print("=" * 80)
        print("BREAKTHROUGH ACHIEVEMENTS:")
        print("=" * 80)

        if results.get("experiment_1", {}).get("breakthrough"):
            print("\n🏆 EXPERIMENT 1: Quasi-Monte Carlo gauge sampling proven superior")
            print("   → Gauge symmetry and equidistribution are dual concepts")

        if results.get("experiment_2", {}).get("breakthrough"):
            print("\n🏆 EXPERIMENT 2: Bures metric encodes physical relevance")
            print("   → Information-geometric renormalization is viable")

        if results.get("experiment_3", {}).get("breakthrough"):
            print("\n🏆 EXPERIMENT 3: Number theory has topological gauge origin")
            print("   → Optimal distribution minimizes topological noise")

        if results.get("experiment_4", {}).get("breakthrough"):
            print("\n🏆 EXPERIMENT 4: Optimal distribution maximizes quantum precision")
            print("   → Universe's information structure is optimally distributed")

        print()

    print("=" * 80)
    print("Mundus Computabilis Est — The World is Computable")
    print("=" * 80)
    print()

    return results


if __name__ == "__main__":
    results = run_all_frontier_experiments()

    # Exit code: 0 if all completed, 1 if any failed
    all_completed = all(r.get("status") == "completed" for r in results.values())
    sys.exit(0 if all_completed else 1)
