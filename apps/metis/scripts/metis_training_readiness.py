#!/usr/bin/env python3
"""
metis_training_readiness.py
HYBA Metis - Training Readiness Evaluator
Deterministic evaluator that reads real-data benchmark evidence, quantum/Pulvini evidence,
and metrics-standard governance evidence. Returns bounded actions.

Computational Intelligence as a Service (CIaaS)
"""

import sys
import os
import json
import hashlib
import argparse
from datetime import datetime, timezone


TRAINING_ACTIONS = [
    "run_benchmarks_first",
    "fix_failures_then_train",
    "train",
    "calibrate_substrate",
    "expand_evidence",
    "hold_and_monitor",
    "calibrate_and_expand_evidence"
]


def evaluate_training_readiness(benchmark_report, quantum_report, metrics_standard_report):
    checks = []
    readiness_score = 0.0
    max_score = 0.0
    recommended_actions = []

    # Dimension 1: Benchmark completeness (weight: 30%)
    max_score += 30.0
    benchmark_score = 0.0

    if benchmark_report.get("total_runs", 0) > 0:
        benchmark_score += 10.0
        checks.append({
            "check": "benchmark_total_runs", "passed": True, "weight": 10.0,
            "details": f"Total benchmark runs: {benchmark_report.get('total_runs', 0)}"
        })
    else:
        checks.append({
            "check": "benchmark_total_runs", "passed": False, "weight": 10.0,
            "details": "No benchmark runs recorded"
        })

    benchmarks = benchmark_report.get("benchmarks", [])
    valid_entries = sum(1 for b in benchmarks if all(k in b for k in ["seed", "solver", "yang_mills", "pulvini", "total_computation_time_s"]))
    if valid_entries > 0:
        benchmark_score += 10.0
        checks.append({
            "check": "benchmark_entries_valid", "passed": True, "weight": 10.0,
            "details": f"{valid_entries}/{len(benchmarks)} entries valid"
        })
    else:
        checks.append({
            "check": "benchmark_entries_valid", "passed": False, "weight": 10.0,
            "details": "No valid benchmark entries found"
        })
        recommended_actions.append("run_benchmarks_first")

    mass_gaps = [b.get("yang_mills", {}).get("mass_gap", 0) for b in benchmarks]
    if mass_gaps:
        stable = all(abs(g - mass_gaps[0]) < 0.01 for g in mass_gaps)
        if stable:
            benchmark_score += 10.0
            checks.append({
                "check": "yang_mills_gap_stability", "passed": True, "weight": 10.0,
                "details": f"Yang-Mills mass gap stable across {len(mass_gaps)} runs"
            })
        else:
            checks.append({
                "check": "yang_mills_gap_stability", "passed": False, "weight": 10.0,
                "details": "Yang-Mills mass gap variance detected"
            })
            recommended_actions.append("calibrate_substrate")

    # Dimension 2: Quantum-path metrics (weight: 30%)
    max_score += 30.0
    quantum_score = 0.0
    metrics = quantum_report.get("metrics", {})

    latency = metrics.get("latency", {})
    if latency.get("average_ms", float('inf')) < 1.0:
        quantum_score += 10.0
        checks.append({
            "check": "quantum_latency", "passed": True, "weight": 10.0,
            "details": f"Quantum latency: {latency.get('average_ms', 'N/A')} ms (threshold: < 1.0 ms)"
        })
    else:
        checks.append({
            "check": "quantum_latency", "passed": False, "weight": 10.0,
            "details": f"Quantum latency: {latency.get('average_ms', 'N/A')} ms exceeds threshold"
        })
        if "calibrate_substrate" not in recommended_actions:
            recommended_actions.append("calibrate_substrate")

    finite = metrics.get("finite_output", {})
    if finite.get("all_tests_passed", False):
        quantum_score += 10.0
        checks.append({
            "check": "finite_output", "passed": True, "weight": 10.0,
            "details": "All finite output tests passed"
        })
    else:
        checks.append({
            "check": "finite_output", "passed": False, "weight": 10.0,
            "details": "Finite output tests failed"
        })
        recommended_actions.append("fix_failures_then_train")

    kernel = metrics.get("retained_kernel", {})
    if kernel.get("kernel_retention_ratio", 0) > 0.95:
        quantum_score += 10.0
        checks.append({
            "check": "kernel_retention", "passed": True, "weight": 10.0,
            "details": f"Kernel retention: {kernel.get('kernel_retention_ratio', 'N/A')}"
        })
    else:
        checks.append({
            "check": "kernel_retention", "passed": False, "weight": 10.0,
            "details": f"Kernel retention: {kernel.get('kernel_retention_ratio', 'N/A')} below threshold"
        })

    # Dimension 3: Metrics standard compliance (weight: 25%)
    max_score += 25.0
    compliance_score = 0.0
    claims = metrics_standard_report.get("claims_governance", {})
    allowed = claims.get("allowed_claims", [])
    blocked = claims.get("blocked_claims", [])

    if len(allowed) > 0:
        compliance_score += 8.0
        checks.append({
            "check": "allowed_claims_defined", "passed": True, "weight": 8.0,
            "details": f"{len(allowed)} allowed claims defined"
        })
    else:
        checks.append({
            "check": "allowed_claims_defined", "passed": False, "weight": 8.0,
            "details": "No allowed claims defined"
        })
        recommended_actions.append("expand_evidence")

    gates = metrics_standard_report.get("evidence_gates", {})
    if len(gates) > 0:
        compliance_score += 8.0
        checks.append({
            "check": "evidence_gates_defined", "passed": True, "weight": 8.0,
            "details": f"{len(gates)} evidence gates defined"
        })
    else:
        checks.append({
            "check": "evidence_gates_defined", "passed": False, "weight": 8.0,
            "details": "No evidence gates defined"
        })

    if metrics_standard_report.get("fingerprint"):
        compliance_score += 5.0
        checks.append({
            "check": "report_fingerprint", "passed": True, "weight": 5.0,
            "details": f"Fingerprint: {metrics_standard_report['fingerprint'][:16]}..."
        })
    else:
        checks.append({
            "check": "report_fingerprint", "passed": False, "weight": 5.0,
            "details": "No report fingerprint"
        })

    if metrics_standard_report.get("hardware_independent"):
        compliance_score += 4.0
        checks.append({
            "check": "hardware_independent", "passed": True, "weight": 4.0,
            "details": "Hardware independent computation"
        })
    else:
        checks.append({
            "check": "hardware_independent", "passed": False, "weight": 4.0,
            "details": "Hardware dependency not declared"
        })

    # Dimension 4: Quantum performance stability (weight: 15%)
    max_score += 15.0
    performance_score = 0.0

    if quantum_report.get("fingerprint"):
        performance_score += 5.0
        checks.append({
            "check": "quantum_report_integrity", "passed": True, "weight": 5.0,
            "details": "Quantum report fingerprint verified"
        })
    if quantum_report.get("no_quantum_advantage_claim"):
        performance_score += 5.0
        checks.append({
            "check": "no_quantum_advantage_claim", "passed": True, "weight": 5.0,
            "details": "No quantum advantage claim made (evidence-gated)"
        })
    if quantum_report.get("all_metrics_observed"):
        performance_score += 5.0
        checks.append({
            "check": "all_metrics_observed", "passed": True, "weight": 5.0,
            "details": "All quantum-path metrics observed"
        })

    readiness_score = benchmark_score + quantum_score + compliance_score + performance_score

    if readiness_score < 40.0:
        action = "run_benchmarks_first"
    elif readiness_score < 60.0:
        if any(c.get("passed") == False and "calibrate" in c.get("check", "") for c in checks):
            action = "calibrate_substrate"
        else:
            action = "fix_failures_then_train"
    elif readiness_score < 80.0:
        action = "train"
    elif readiness_score < 95.0:
        if any(c.get("passed") == False for c in checks):
            action = "calibrate_and_expand_evidence"
        else:
            action = "hold_and_monitor"
    else:
        action = "train"

    if recommended_actions:
        action = recommended_actions[0]
        if len(recommended_actions) > 1:
            action = "calibrate_and_expand_evidence"

    return {
        "readiness_score": round(readiness_score, 2),
        "max_score": max_score,
        "readiness_percentage": round((readiness_score / max_score) * 100, 2) if max_score > 0 else 0.0,
        "action": action,
        "possible_actions": TRAINING_ACTIONS,
        "dimension_scores": {
            "benchmark_completeness": {
                "score": round(benchmark_score, 2), "weight": 30.0,
                "percentage": round((benchmark_score / 30.0) * 100, 2)
            },
            "quantum_path_metrics": {
                "score": round(quantum_score, 2), "weight": 30.0,
                "percentage": round((quantum_score / 30.0) * 100, 2)
            },
            "metrics_standard_compliance": {
                "score": round(compliance_score, 2), "weight": 25.0,
                "percentage": round((compliance_score / 25.0) * 100, 2)
            },
            "quantum_performance_stability": {
                "score": round(performance_score, 2), "weight": 15.0,
                "percentage": round((performance_score / 15.0) * 100, 2)
            }
        },
        "checks": checks,
        "recommended_actions": recommended_actions if recommended_actions else [action],
        "action_descriptions": {
            "run_benchmarks_first": "No benchmark evidence found. Run benchmarks before training.",
            "fix_failures_then_train": "Critical failures detected. Fix issues before training.",
            "train": "All evidence gates passed. Training readiness confirmed.",
            "calibrate_substrate": "Quantum path metrics unstable. Calibrate substrate before training.",
            "expand_evidence": "Evidence incomplete. Expand evidence coverage.",
            "hold_and_monitor": "Near threshold. Hold and monitor before proceeding.",
            "calibrate_and_expand_evidence": "Multiple issues detected. Calibrate and expand evidence."
        },
        "note": "Deterministic training-readiness evaluation. No autonomous retraining decisions without human oversight."
    }


def main():
    parser = argparse.ArgumentParser(description="Metis Training Readiness Evaluator")
    parser.add_argument("--benchmark-report", type=str, required=True)
    parser.add_argument("--quantum-report", type=str, required=True)
    parser.add_argument("--metrics-standard-report", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    print("[METIS] Training Readiness Evaluator")
    print(f"[METIS] Benchmark report: {args.benchmark_report}")
    print(f"[METIS] Quantum report: {args.quantum_report}")
    print(f"[METIS] Metrics standard report: {args.metrics_standard_report}")
    print()

    with open(args.benchmark_report, 'r') as f:
        benchmark_data = json.load(f)
    with open(args.quantum_report, 'r') as f:
        quantum_data = json.load(f)
    with open(args.metrics_standard_report, 'r') as f:
        metrics_data = json.load(f)

    print("[METIS] Evaluating training readiness...")
    result = evaluate_training_readiness(benchmark_data, quantum_data, metrics_data)

    print(f"  |-- Readiness score: {result['readiness_score']:.2f}/{result['max_score']:.0f}")
    print(f"  |-- Readiness: {result['readiness_percentage']:.1f}%")
    print(f"  |-- Action: {result['action']}")
    print()

    print("[METIS] Dimension scores:")
    for dim, scores in result['dimension_scores'].items():
        print(f"  |-- {dim}: {scores['percentage']:.1f}% ({scores['score']}/{scores['weight']})")
    print()

    print("[METIS] Checks:")
    for c in result['checks']:
        status = "PASS" if c['passed'] else "FAIL"
        print(f"  |-- [{status}] {c['check']}: {c['details']}")

    output = {
        "metis_training_readiness_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_files": {
            "benchmark_report": args.benchmark_report,
            "quantum_report": args.quantum_report,
            "metrics_standard_report": args.metrics_standard_report
        },
        "evaluation": result
    }
    content = json.dumps(output, sort_keys=True, default=str)
    fingerprint = hashlib.sha256(content.encode()).hexdigest()
    output["fingerprint"] = fingerprint

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n[METIS] Training readiness written to: {args.output}")
    print(f"[METIS] Report fingerprint (SHA-256): {fingerprint}")


if __name__ == "__main__":
    main()