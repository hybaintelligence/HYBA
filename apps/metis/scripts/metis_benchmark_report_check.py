#!/usr/bin/env python3
"""
metis_benchmark_report_check.py
HYBA Metis - Benchmark Report Check
Validates a benchmark evidence artifact against the Metis Metrics Standard.

Computational Intelligence as a Service (CIaaS)
"""

import sys
import os
import json
import hashlib
import argparse
from datetime import datetime, timezone


REQUIRED_FIELDS = [
    "metis_benchmark_version",
    "timestamp",
    "total_runs",
    "seeds",
    "benchmarks",
    "substrate",
    "hardware_independent"
]

REQUIRED_BENCHMARK_FIELDS = [
    "seed",
    "timestamp",
    "solver",
    "yang_mills",
    "pulvini",
    "quantum_advantage",
    "total_computation_time_s"
]

REQUIRED_SOLVER_FIELDS = [
    "nonce",
    "entropy",
    "computation_time_s",
    "solver_type",
    "state_dimension"
]

REQUIRED_YANG_MILLS_FIELDS = [
    "mass_gap",
    "spectral_gap_ratio",
    "dimension",
    "symmetry_group",
    "substrate"
]

THRESHOLDS = {
    "max_solver_time_s": 1.0,
    "min_entropy": 3.0,
    "max_entropy": 5.5,
    "yang_mills_gap_tolerance": 0.06,
    "phi_resonance_floor": 0.0594,
    "mass_gap_tolerance": 0.06
}


def validate_file_exists(path: str) -> dict:
    """Check if file exists and is readable."""
    result = {
        "check": "file_exists",
        "path": path,
        "passed": False,
        "details": ""
    }
    if not os.path.exists(path):
        result["details"] = f"File not found: {path}"
        return result
    if not os.path.isfile(path):
        result["details"] = f"Path is not a file: {path}"
        return result
    if os.path.getsize(path) == 0:
        result["details"] = f"File is empty: {path}"
        return result
    result["passed"] = True
    result["details"] = f"File exists ({os.path.getsize(path)} bytes)"
    return result


def validate_json_format(data: dict) -> dict:
    """Validate that the data is properly formatted JSON."""
    result = {"check": "json_format", "passed": False, "missing_fields": [], "details": ""}
    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        result["missing_fields"] = missing
        result["details"] = f"Missing required fields: {missing}"
        return result
    result["passed"] = True
    result["details"] = f"All {len(REQUIRED_FIELDS)} required fields present"
    return result


def validate_benchmarks(data: dict) -> dict:
    """Validate each benchmark entry."""
    result = {
        "check": "benchmark_entries",
        "passed": False, "total_entries": 0, "valid_entries": 0, "errors": [], "details": ""
    }
    benchmarks = data.get("benchmarks", [])
    result["total_entries"] = len(benchmarks)
    for i, b in enumerate(benchmarks):
        entry_errors = []
        missing = [f for f in REQUIRED_BENCHMARK_FIELDS if f not in b]
        if missing:
            entry_errors.append(f"Entry {i}: missing fields {missing}")
        if "solver" in b:
            solver_missing = [f for f in REQUIRED_SOLVER_FIELDS if f not in b["solver"]]
            if solver_missing:
                entry_errors.append(f"Entry {i} solver: missing fields {solver_missing}")
            entropy = b["solver"].get("entropy", 0)
            if entropy < THRESHOLDS["min_entropy"] or entropy > THRESHOLDS["max_entropy"]:
                entry_errors.append(
                    f"Entry {i} solver: entropy {entropy} outside bounds "
                    f"({THRESHOLDS['min_entropy']} - {THRESHOLDS['max_entropy']})"
                )
        if "yang_mills" in b:
            ym_missing = [f for f in REQUIRED_YANG_MILLS_FIELDS if f not in b["yang_mills"]]
            if ym_missing:
                entry_errors.append(f"Entry {i} yang_mills: missing fields {ym_missing}")
            mass_gap = b["yang_mills"].get("mass_gap", 0)
            # Mass gap can range from near-0 to the phi_resonance_floor depending on spectral decomposition
            # The mass gap is the MINIMUM non-zero eigenvalue of the Laplace-Beltrami operator
            gap_diff = abs(mass_gap - THRESHOLDS["phi_resonance_floor"])
            if gap_diff > THRESHOLDS["mass_gap_tolerance"]:
                entry_errors.append(
                    f"Entry {i} yang_mills: mass gap {mass_gap} deviates from "
                    f"reference {THRESHOLDS['phi_resonance_floor']} by {gap_diff}"
                )
        if entry_errors:
            result["errors"].extend(entry_errors)
        else:
            result["valid_entries"] += 1
    result["passed"] = result["valid_entries"] == result["total_entries"]
    result["details"] = f"{result['valid_entries']}/{result['total_entries']} entries valid"
    return result


def validate_substrate_agnostic(data: dict) -> dict:
    """Validate that the evidence claims substrate independence."""
    result = {"check": "substrate_agnostic", "passed": False, "details": ""}
    substrate = data.get("substrate", "")
    hw_independent = data.get("hardware_independent", False)
    if substrate == "mathematical_pure":
        result["details"] = f"Substrate: {substrate} - pure mathematical computation"
    else:
        result["details"] = f"Substrate: {substrate} - not marked as mathematical pure"
    if hw_independent:
        result["details"] += ", hardware independent"
    result["passed"] = substrate == "mathematical_pure" and hw_independent
    return result


def compute_fingerprint(data: dict) -> str:
    content = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Metis Benchmark Report Check")
    parser.add_argument("input", type=str, help="Path to benchmark JSON file")
    parser.add_argument("--output", type=str, required=True, help="Output file path")
    args = parser.parse_args()

    print("[METIS] Benchmark Report Check")
    print(f"[METIS] Validating: {args.input}")
    print()

    checks = []
    all_passed = True

    print("[METIS] Check 1/5: File exists...")
    check1 = validate_file_exists(args.input)
    checks.append(check1)
    print(f"  +-- {'PASS' if check1['passed'] else 'FAIL'}: {check1['details']}")
    if not check1["passed"]:
        all_passed = False

    if check1["passed"]:
        with open(args.input, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"  +-- FAIL: Invalid JSON: {e}")
                all_passed = False
                data = {}

        print("[METIS] Check 2/5: JSON format...")
        check2 = validate_json_format(data)
        checks.append(check2)
        print(f"  +-- {'PASS' if check2['passed'] else 'FAIL'}: {check2['details']}")
        if not check2["passed"]:
            all_passed = False

        print("[METIS] Check 3/5: Benchmark entries...")
        check3 = validate_benchmarks(data)
        checks.append(check3)
        print(f"  +-- {'PASS' if check3['passed'] else 'FAIL'}: {check3['details']}")
        if not check3["passed"]:
            all_passed = False
            for err in check3.get("errors", []):
                print(f"     |-- {err}")

        print("[METIS] Check 4/5: Substrate agnostic...")
        check4 = validate_substrate_agnostic(data)
        checks.append(check4)
        print(f"  +-- {'PASS' if check4['passed'] else 'FAIL'}: {check4['details']}")
        if not check4["passed"]:
            all_passed = False

    fingerprint = compute_fingerprint(data) if check1.get("passed") else "N/A"
    print(f"[METIS] Check 5/5: Fingerprint -> {fingerprint}")
    checks.append({"check": "fingerprint", "fingerprint": fingerprint, "algorithm": "SHA-256"})

    print()
    print(f"[METIS] Overall: {'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'}")

    output = {
        "metis_report_check_version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_file": args.input,
        "all_checks_passed": all_passed,
        "checks": checks,
        "fingerprint": fingerprint,
        "note": "Report check validates evidence structure, not quantum advantage claims"
    }

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n[METIS] Report check written to: {args.output}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())