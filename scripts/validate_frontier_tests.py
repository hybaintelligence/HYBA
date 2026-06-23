#!/usr/bin/env python3
"""
Frontier Tests Validation Script

Verifies that all three frontier tests can be imported and have correct structure.
Does NOT run the full tests (which take 15-30 minutes), but validates:
- Import paths are correct
- Required dependencies exist
- Class/function signatures are valid
- Basic instantiation works
"""

import sys
from pathlib import Path

# Add python_backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "python_backend"))


def validate_imports():
    """Validate all required imports."""
    print("🔍 Validating imports...")

    try:
        import numpy as np

        print(f"  ✅ NumPy {np.__version__}")
    except ImportError as e:
        print(f"  ❌ NumPy import failed: {e}")
        return False

    try:
        from pythia_mining.consciousness_engine import (
            ConsciousnessEngine,
            ConsciousnessConfig,
        )

        print(f"  ✅ ConsciousnessEngine")
    except ImportError as e:
        print(f"  ❌ ConsciousnessEngine import failed: {e}")
        return False

    try:
        from pythia_mining.pulvini_manifold import PulviniManifold

        print(f"  ✅ PulviniManifold")
    except ImportError as e:
        print(f"  ❌ PulviniManifold import failed: {e}")
        return False

    try:
        from pythia_mining.pulvini_bures import bures_certificate, density_state

        print(f"  ✅ Bures certificate")
    except ImportError as e:
        print(f"  ❌ Bures certificate import failed: {e}")
        return False

    try:
        from pythia_mining.phi_folding import PhiFoldingOperator

        print(f"  ✅ PhiFoldingOperator")
    except ImportError as e:
        print(f"  ❌ PhiFoldingOperator import failed: {e}")
        return False

    try:
        from pythia_mining.pulvini_topology import CoxeterTopology

        print(f"  ✅ CoxeterTopology")
    except ImportError as e:
        print(f"  ❌ CoxeterTopology import failed: {e}")
        return False

    try:
        from pythia_mining.pulvini_certificates import PostQuantumPassport

        print(f"  ✅ PostQuantumPassport")
    except ImportError as e:
        print(f"  ❌ PostQuantumPassport import failed: {e}")
        return False

    return True


def validate_manifold_stress():
    """Validate manifold stress test structure."""
    print("\n🔍 Validating Manifold Stress Test...")

    try:
        # Import test module components
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from frontier_manifold_stress import ManifoldStressAnalyzer

        # Basic instantiation
        analyzer = ManifoldStressAnalyzer(phi_threshold=0.5)
        print(f"  ✅ ManifoldStressAnalyzer instantiation")

        # Check methods exist
        assert hasattr(analyzer, "compute_fisher_information_matrix")
        assert hasattr(analyzer, "compute_ricci_scalar")
        assert hasattr(analyzer, "compute_geometric_stability")
        print(f"  ✅ Required methods present")

        return True

    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        return False


def validate_latency_profiler():
    """Validate latency profiler structure."""
    print("\n🔍 Validating Latency Profiler...")

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
        from profile_consciousness_latency import LatencyProfiler

        # Basic instantiation
        profiler = LatencyProfiler(num_samples=10)
        print(f"  ✅ LatencyProfiler instantiation")

        # Check methods exist
        assert hasattr(profiler, "profile_phi_measurement_loop")
        assert hasattr(profiler, "analyze_bottlenecks")
        assert hasattr(profiler, "classify_bottleneck_type")
        assert hasattr(profiler, "compute_amdahl_speedup")
        print(f"  ✅ Required methods present")

        # Test Amdahl's Law calculation
        speedup = profiler.compute_amdahl_speedup(
            bottleneck_fraction=0.5, speedup_factor=10
        )
        assert 1.0 < speedup < 10.0, f"Amdahl speedup sanity check failed: {speedup}"
        print(f"  ✅ Amdahl's Law computation correct")

        return True

    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        return False


def validate_quantum_adversary():
    """Validate quantum adversary test structure."""
    print("\n🔍 Validating Quantum Adversary...")

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "tests"))
        from frontier_quantum_adversary import QuantumAdversary, PassportDefender
        from pythia_mining.pulvini_topology import CoxeterTopology
        from pythia_mining.pulvini_certificates import PostQuantumPassport

        # Create topology
        topology = CoxeterTopology(group_type="A5", dimension=32)
        print(f"  ✅ CoxeterTopology creation")

        # Create passport
        passport = PostQuantumPassport(topology=topology)
        print(f"  ✅ PostQuantumPassport creation")

        # Create adversary
        adversary = QuantumAdversary(topology, seed=42)
        print(f"  ✅ QuantumAdversary instantiation")

        # Create defender
        defender = PassportDefender(passport)
        print(f"  ✅ PassportDefender instantiation")

        # Check methods exist
        assert hasattr(adversary, "inject_symmetry_breaking_noise")
        assert hasattr(defender, "detect_symmetry_violation")
        assert hasattr(defender, "attempt_bures_gradient_repair")
        print(f"  ✅ Required methods present")

        return True

    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        return False


def validate_supporting_modules():
    """Validate new supporting modules."""
    print("\n🔍 Validating Supporting Modules...")

    try:
        from pythia_mining.pulvini_topology import CoxeterTopology

        # Test topology creation
        topology = CoxeterTopology(group_type="A5", dimension=32)
        order = topology.get_group_order()
        assert order == 120, f"Expected order 120, got {order}"
        print(f"  ✅ CoxeterTopology group order correct (120)")

        # Test canonical map
        canonical_map = topology.get_canonical_map()
        assert canonical_map.shape == (
            32,
            3,
        ), f"Expected shape (32, 3), got {canonical_map.shape}"
        print(f"  ✅ Canonical map shape correct")

        # Test orbits
        orbits = topology.compute_node_orbits()
        assert len(orbits) > 0, "No orbits computed"
        print(f"  ✅ Orbit computation works ({len(orbits)} orbits)")

        return True

    except Exception as e:
        print(f"  ❌ Validation failed: {e}")
        return False


def main():
    """Run all validations."""
    print("=" * 80)
    print("FRONTIER TESTS VALIDATION")
    print("=" * 80)
    print()

    results = []

    # Import validation
    results.append(("Imports", validate_imports()))

    # Module validations
    results.append(("Supporting Modules", validate_supporting_modules()))
    results.append(("Manifold Stress Test", validate_manifold_stress()))
    results.append(("Latency Profiler", validate_latency_profiler()))
    results.append(("Quantum Adversary", validate_quantum_adversary()))

    # Summary
    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {name:<30} {status}")

    all_passed = all(success for _, success in results)

    if all_passed:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("\nFrontier tests are ready to run:")
        print("  ./scripts/run_frontier_tests.sh")
        return 0
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print("\nPlease fix the errors above before running frontier tests.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
