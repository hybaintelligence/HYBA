#!/usr/bin/env python3
"""
Comprehensive validation script for HYBA PQMC reproducibility.

This script runs all validation checks to ensure reproducibility of published results.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

# Set reproducibility seed
np.random.seed(42)


class ValidationResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.details = []
        self.metrics = {}

    def add_detail(self, detail: str):
        self.details.append(detail)

    def add_metric(self, key: str, value: float):
        self.metrics[key] = value

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "details": self.details,
            "metrics": self.metrics,
        }


def validate_fault_tolerance_formula() -> ValidationResult:
    """Validate the logical error rate suppression formula."""
    result = ValidationResult("Fault Tolerance Formula Validation")

    try:
        from pythia_mining.fault_tolerant_quantum_core import FaultTolerantQuantumCore

        # Test 1: Formula agreement with documented equation
        result.add_detail("Testing formula agreement...")
        core = FaultTolerantQuantumCore(code_distance=7, physical_error_rate=0.001)
        expected_p_logical = 50 * (core.p_phys ** ((core.d + 1) / 2))
        actual_p_logical = core.p_logical

        tolerance = 1e-10
        if abs(actual_p_logical - expected_p_logical) < tolerance:
            result.add_detail("✓ Formula matches documented equation")
            result.add_metric("formula_error", abs(actual_p_logical - expected_p_logical))
        else:
            result.add_detail(f"✗ Formula mismatch: {actual_p_logical} vs {expected_p_logical}")
            return result

        # Test 2: Monotonic decrease with code distance
        result.add_detail("Testing monotonic decrease with code distance...")
        p_phys = 0.001
        distances = [5, 7, 9, 11]
        p_logicals = []
        for d in distances:
            core = FaultTolerantQuantumCore(code_distance=d, physical_error_rate=p_phys)
            p_logicals.append(core.p_logical)

        is_monotonic = all(p_logicals[i] > p_logicals[i+1] for i in range(len(p_logicals)-1))
        if is_monotonic:
            result.add_detail("✓ Logical error rate decreases monotonically with code distance")
            result.add_metric("monotonic_decrease", 1.0)
        else:
            result.add_detail("✗ Non-monotonic behavior detected")
            return result

        # Test 3: Monotonic increase with physical error rate
        result.add_detail("Testing monotonic increase with physical error rate...")
        d = 7
        p_phys_values = [0.0001, 0.001, 0.01, 0.1]
        p_logicals = []
        for p_phys in p_phys_values:
            core = FaultTolerantQuantumCore(code_distance=d, physical_error_rate=p_phys)
            p_logicals.append(core.p_logical)

        is_monotonic = all(p_logicals[i] < p_logicals[i+1] for i in range(len(p_logicals)-1))
        if is_monotonic:
            result.add_detail("✓ Logical error rate increases monotonically with physical error rate")
            result.add_metric("monotonic_increase", 1.0)
        else:
            result.add_detail("✗ Non-monotonic behavior detected")
            return result

        # Test 4: Saturation at threshold
        result.add_detail("Testing saturation at model threshold (0.0109)...")
        d = 7
        p_phys_high = 0.5  # Well above threshold
        core = FaultTolerantQuantumCore(code_distance=d, physical_error_rate=p_phys_high)
        if core.p_logical >= 0.99:
            result.add_detail("✓ Logical error rate saturates near 1.0 above threshold")
            result.add_metric("saturation_value", core.p_logical)
        else:
            result.add_detail(f"✗ Expected saturation near 1.0, got {core.p_logical}")
            return result

        result.passed = True
        result.add_detail("All fault tolerance formula validations passed")

    except Exception as e:
        result.add_detail(f"✗ Exception: {str(e)}")
        import traceback
        result.add_detail(traceback.format_exc())

    return result


def validate_quantum_operations() -> ValidationResult:
    """Validate core quantum operations."""
    result = ValidationResult("Quantum Operations Validation")

    try:
        from pythia_mining.fault_tolerant_quantum_core import FaultTolerantQuantumCore

        result.add_detail("Testing logical qubit initialization...")
        core = FaultTolerantQuantumCore(code_distance=7, physical_error_rate=0.001)
        core.initialize_logical_qubit("0")
        if len(core.logical_qubits) == 1:
            result.add_detail("✓ Logical qubit initialized correctly")
            result.add_metric("logical_qubits", len(core.logical_qubits))
        else:
            result.add_detail("✗ Logical qubit initialization failed")
            return result

        result.add_detail("Testing syndrome measurement...")
        syndrome = core.measure_syndrome()
        if syndrome is not None and syndrome.shape == (core.d - 1, core.d - 1):
            result.add_detail("✓ Syndrome measurement produces correct shape")
            result.add_metric("syndrome_shape", str(syndrome.shape))
        else:
            result.add_detail("✗ Syndrome measurement failed")
            return result

        result.add_detail("Testing error correction...")
        core.apply_logical_gate("X", 0)
        corrected = core.correct_errors()
        if corrected:
            result.add_detail("✓ Error correction executed")
            result.add_metric("error_correction", 1.0)
        else:
            result.add_detail("✗ Error correction failed")
            return result

        result.passed = True
        result.add_detail("All quantum operation validations passed")

    except Exception as e:
        result.add_detail(f"✗ Exception: {str(e)}")
        import traceback
        result.add_detail(traceback.format_exc())

    return result


def validate_api_endpoints() -> ValidationResult:
    """Validate API endpoints return expected responses."""
    result = ValidationResult("API Endpoint Validation")

    try:
        from fastapi.testclient import TestClient
        from hyba_genesis_api.main import app

        result.add_detail("Testing health endpoint...")
        client = TestClient(app)
        response = client.get("/health")
        if response.status_code == 200:
            result.add_detail("✓ Health endpoint returns 200")
            result.add_metric("health_status", response.status_code)
        else:
            result.add_detail(f"✗ Health endpoint returned {response.status_code}")
            return result

        result.add_detail("Testing substrate endpoint...")
        response = client.get("/api/substrate")
        if response.status_code == 200:
            result.add_detail("✓ Substrate endpoint returns 200")
            result.add_metric("substrate_status", response.status_code)
        else:
            result.add_detail(f"✗ Substrate endpoint returned {response.status_code}")
            return result

        result.passed = True
        result.add_detail("All API endpoint validations passed")

    except Exception as e:
        result.add_detail(f"✗ Exception: {str(e)}")
        import traceback
        result.add_detail(traceback.format_exc())

    return result


def run_all_validations() -> List[ValidationResult]:
    """Run all validation checks."""
    results = []

    print("=" * 60)
    print("HYBA PQMC Reproducibility Validation")
    print("=" * 60)
    print()

    results.append(validate_fault_tolerance_formula())
    print(f"Fault Tolerance Formula: {'✓ PASS' if results[-1].passed else '✗ FAIL'}")

    results.append(validate_quantum_operations())
    print(f"Quantum Operations: {'✓ PASS' if results[-1].passed else '✗ FAIL'}")

    results.append(validate_api_endpoints())
    print(f"API Endpoints: {'✓ PASS' if results[-1].passed else '✗ FAIL'}")

    print()
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate HYBA PQMC reproducibility")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="validation_output/results.json", help="Output file for results")

    args = parser.parse_args()

    # Set seed
    np.random.seed(args.seed)

    # Run validations
    results = run_all_validations()

    # Summary
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"Summary: {passed}/{total} validations passed")

    # Write results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)

    print(f"Results written to {output_path}")

    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
