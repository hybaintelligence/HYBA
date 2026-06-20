#!/usr/bin/env python3
"""
QaaS Production Hardening Validation Script

Demonstrates that critical security controls are in place:
1. Privilege escalation prevention (extra='forbid')
2. Entitlement matrix enforcement
3. Metadata trust boundary
4. Fair work-unit estimation with operation weights

Run: python3 scripts/validate_qaas_hardening.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pydantic import ValidationError
from fastapi import HTTPException

from hyba_genesis_api.api.quantum_as_a_service import (
    CustomerProvisionFaultTolerantComputerRequest,
    _validate_customer_entitlement,
    _estimated_work_units,
)


def test_privilege_escalation_prevention():
    """Verify customer cannot inject admin_privileged field."""
    print("🔒 TEST 1: Privilege Escalation Prevention")
    
    try:
        # Attempt to inject admin_privileged
        request = CustomerProvisionFaultTolerantComputerRequest(
            name="attacker",
            tier="developer",
            isolation="single_tenant",
            admin_privileged=True,  # Should be rejected
        )
        print("  ❌ FAILED: admin_privileged was not rejected!")
        return False
    except ValidationError as e:
        if "admin_privileged" in str(e) or "extra" in str(e).lower():
            print("  ✅ PASSED: admin_privileged field rejected")
            return True
        else:
            print(f"  ❌ FAILED: Wrong error: {e}")
            return False


def test_entitlement_matrix():
    """Verify entitlement enforcement for all tiers."""
    print("\n🎫 TEST 2: Entitlement Matrix Enforcement")
    
    tests = [
        # (principal, requested_tier, requested_isolation, should_succeed)
        ({"tier": "developer", "metadata": {}}, "developer", "single_tenant", True),
        ({"tier": "developer", "metadata": {}}, "production", "single_tenant", False),
        ({"tier": "production", "metadata": {}}, "production", "dedicated_control_plane", True),
        ({"tier": "production", "metadata": {}}, "enterprise", "sovereign_isolated", False),
        ({"tier": "enterprise", "metadata": {"sovereign_enabled": False}}, "enterprise", "sovereign_isolated", False),
        ({"tier": "enterprise", "metadata": {"sovereign_enabled": True}}, "enterprise", "sovereign_isolated", True),
    ]
    
    passed = 0
    for principal, tier, isolation, should_succeed in tests:
        try:
            _validate_customer_entitlement(principal, tier, isolation)
            result = True
        except HTTPException:
            result = False
        
        if result == should_succeed:
            print(f"  ✅ {principal['tier']} → {tier}/{isolation}: {'allowed' if should_succeed else 'denied'}")
            passed += 1
        else:
            print(f"  ❌ {principal['tier']} → {tier}/{isolation}: expected {'allow' if should_succeed else 'deny'}, got {'allow' if result else 'deny'}")
    
    print(f"  {passed}/{len(tests)} entitlement tests passed")
    return passed == len(tests)


def test_metadata_trust_boundary():
    """Verify sovereign entitlement comes from principal, not request."""
    print("\n🛡️  TEST 3: Metadata Trust Boundary")
    
    # Principal says no sovereign access
    principal = {
        "tier": "enterprise",
        "metadata": {"sovereign_enabled": False}
    }
    
    try:
        # Even if request claims sovereign, principal metadata decides
        _validate_customer_entitlement(principal, "enterprise", "sovereign_isolated")
        print("  ❌ FAILED: Sovereign access granted despite principal metadata=False")
        return False
    except HTTPException:
        print("  ✅ PASSED: Sovereign denied based on principal metadata (not request)")
        return True


def test_work_unit_fairness():
    """Verify work-unit estimation includes all cost dimensions."""
    print("\n⚖️  TEST 4: Work-Unit Estimate Fairness")
    
    # Light operation
    light = _estimated_work_units(
        operation="state_vector_summary",
        circuit_depth=100,
        logical_qubits=[0, 1, 2],
        shots=100,
        code_distance=7,
    )
    
    # Heavy operation (same params, different operation)
    heavy = _estimated_work_units(
        operation="substrate_orchestration",
        circuit_depth=100,
        logical_qubits=[0, 1, 2],
        shots=100,
        code_distance=7,
    )
    
    # Deep circuit
    deep = _estimated_work_units(
        operation="surface_code_cycle",
        circuit_depth=1000,
        logical_qubits=[0, 1, 2],
        shots=100,
        code_distance=7,
    )
    
    # Many qubits
    wide = _estimated_work_units(
        operation="surface_code_cycle",
        circuit_depth=100,
        logical_qubits=list(range(20)),
        shots=100,
        code_distance=7,
    )
    
    # High code distance
    high_d = _estimated_work_units(
        operation="surface_code_cycle",
        circuit_depth=100,
        logical_qubits=[0, 1, 2],
        shots=100,
        code_distance=15,
    )
    
    checks = [
        (heavy > light, f"Heavy operation ({heavy}) > light operation ({light})"),
        (deep > light, f"Deep circuit ({deep}) > baseline ({light})"),
        (wide > light, f"Wide circuit ({wide}) > baseline ({light})"),
        (high_d > light, f"High code distance ({high_d}) > baseline ({light})"),
    ]
    
    passed = 0
    for check, desc in checks:
        if check:
            print(f"  ✅ {desc}")
            passed += 1
        else:
            print(f"  ❌ {desc}")
    
    print(f"  {passed}/{len(checks)} fairness checks passed")
    return passed == len(checks)


def main():
    print("=" * 70)
    print("QaaS Production Hardening Validation")
    print("=" * 70)
    
    results = []
    
    results.append(("Privilege Escalation Prevention", test_privilege_escalation_prevention()))
    results.append(("Entitlement Matrix Enforcement", test_entitlement_matrix()))
    results.append(("Metadata Trust Boundary", test_metadata_trust_boundary()))
    results.append(("Work-Unit Estimate Fairness", test_work_unit_fairness()))
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 All critical security controls validated!")
        print("\n📋 Next Steps:")
        print("  1. Run full test suite: pytest tests/test_quantum_as_a_service_production_hardening.py")
        print("  2. Validate admin route separation")
        print("  3. Load test concurrent execution")
        print("  4. Implement billing rollback semantics")
        return 0
    else:
        print("\n⚠️  Some security controls failed validation!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
