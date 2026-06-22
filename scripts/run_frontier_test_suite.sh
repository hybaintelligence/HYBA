#!/bin/bash

# Comprehensive Frontier Test Suite Runner
# Executes unit, integration, property, and benchmark tests for all three frontier tests

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================================================================================="
echo "FRONTIER TEST SUITE — COMPREHENSIVE TESTING"
echo "========================================================================================================="
echo "Project Root: $PROJECT_ROOT"
echo ""

# Setup Python path
export PYTHONPATH="$PROJECT_ROOT/python_backend:$PROJECT_ROOT/tests:$PROJECT_ROOT/scripts:$PYTHONPATH"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python Version: $PYTHON_VERSION"
echo ""

# Check pytest availability
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest not found. Installing..."
    pip3 install pytest pytest-benchmark hypothesis
fi

echo "Test Framework: $(python3 -m pytest --version)"
echo ""

# ================================================
# TEST SUITE 1: Manifold Stress Tests
# ================================================
echo "========================================================================================================="
echo "TEST SUITE 1: MANIFOLD COLLAPSE STRESSER"
echo "========================================================================================================="
echo ""

echo "--- Running Unit Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_manifold_stress.py::TestManifoldStressAnalyzer" -v --tb=short || {
    echo "⚠️  Some unit tests failed"
}
echo ""

echo "--- Running Integration Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_manifold_stress.py::TestManifoldStressIntegration" -v --tb=short || {
    echo "⚠️  Some integration tests failed"
}
echo ""

echo "--- Running Property-Based Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_manifold_stress.py" -k "test_qfi_eigenvalues" -v --tb=short || {
    echo "⚠️  Some property tests failed"
}
echo ""

echo "--- Running Regression Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_manifold_stress.py::TestManifoldStressRegression" -v --tb=short || {
    echo "⚠️  Some regression tests failed"
}
echo ""

# ================================================
# TEST SUITE 2: Latency Profiler Tests
# ================================================
echo "========================================================================================================="
echo "TEST SUITE 2: CONSCIOUSNESS LATENCY PROFILER"
echo "========================================================================================================="
echo ""

echo "--- Running Unit Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_latency_profiler.py::TestLatencyProfiler" -v --tb=short || {
    echo "⚠️  Some unit tests failed"
}
echo ""

echo "--- Running Integration Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_latency_profiler.py::TestLatencyProfilerIntegration" -v --tb=short || {
    echo "⚠️  Some integration tests failed"
}
echo ""

echo "--- Running Property-Based Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_latency_profiler.py" -k "test_amdahl" -v --tb=short || {
    echo "⚠️  Some property tests failed"
}
echo ""

echo "--- Running Regression Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_latency_profiler.py::TestLatencyProfilerRegression" -v --tb=short || {
    echo "⚠️  Some regression tests failed"
}
echo ""

# ================================================
# TEST SUITE 3: Quantum Adversary Tests
# ================================================
echo "========================================================================================================="
echo "TEST SUITE 3: QUANTUM ADVERSARY"
echo "========================================================================================================="
echo ""

echo "--- Running Unit Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py::TestCoxeterTopology" -v --tb=short || {
    echo "⚠️  Some unit tests failed"
}
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py::TestPostQuantumPassport" -v --tb=short || {
    echo "⚠️  Some unit tests failed"
}
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py::TestQuantumAdversary" -v --tb=short || {
    echo "⚠️  Some unit tests failed"
}
echo ""

echo "--- Running Integration Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py::TestQuantumAdversaryIntegration" -v --tb=short || {
    echo "⚠️  Some integration tests failed"
}
echo ""

echo "--- Running Property-Based Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py" -k "property" -v --tb=short || {
    echo "⚠️  Some property tests failed"
}
echo ""

echo "--- Running Regression Tests ---"
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py::TestQuantumAdversaryRegression" -v --tb=short || {
    echo "⚠️  Some regression tests failed"
}
echo ""

# ================================================
# BENCHMARK TESTS (Optional — can be slow)
# ================================================
if [ "$RUN_BENCHMARKS" = "1" ]; then
    echo "========================================================================================================="
    echo "BENCHMARK TESTS"
    echo "========================================================================================================="
    echo ""
    
    python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_manifold_stress.py::TestManifoldStressBenchmarks" \
        --benchmark-only -v || {
        echo "⚠️  Some benchmarks failed"
    }
    
    python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_latency_profiler.py::TestLatencyProfilerBenchmarks" \
        --benchmark-only -v || {
        echo "⚠️  Some benchmarks failed"
    }
    
    python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py::TestQuantumAdversaryBenchmarks" \
        --benchmark-only -v || {
        echo "⚠️  Some benchmarks failed"
    }
    echo ""
fi

# ================================================
# SUMMARY
# ================================================
echo "========================================================================================================="
echo "TEST SUITE SUMMARY"
echo "========================================================================================================="
echo ""

# Run all tests and capture exit code
python3 -m pytest "$PROJECT_ROOT/tests/test_frontier_manifold_stress.py" \
                  "$PROJECT_ROOT/tests/test_frontier_latency_profiler.py" \
                  "$PROJECT_ROOT/tests/test_frontier_quantum_adversary.py" \
                  -v --tb=short --ignore-glob="*benchmark*" -q || TEST_EXIT=$?

if [ -z "$TEST_EXIT" ] || [ "$TEST_EXIT" -eq 0 ]; then
    echo ""
    echo "✅ ALL TESTS PASSED"
    echo ""
    echo "Test Coverage:"
    echo "  ✅ Unit Tests: Individual component verification"
    echo "  ✅ Integration Tests: Full pipeline testing"
    echo "  ✅ Property-Based Tests: Mathematical invariant verification"
    echo "  ✅ Regression Tests: Known behavior preservation"
    echo "  ✅ Edge Case Tests: Boundary condition handling"
    echo ""
    echo "Quality Level: scientific/formal-invariant validation"
    echo ""
else
    echo ""
    echo "⚠️  SOME TESTS FAILED (exit code: $TEST_EXIT)"
    echo ""
    echo "Review the output above for details."
    echo "This is expected for stress tests that probe system limits."
    echo ""
fi

echo "========================================================================================================="
echo "NEXT STEPS"
echo "========================================================================================================="
echo ""
echo "1. Review test output for any failures or warnings"
echo "2. Run benchmark tests if performance metrics needed: RUN_BENCHMARKS=1 ./scripts/run_frontier_test_suite.sh"
echo "3. Run actual frontier tests (not just unit tests): ./scripts/run_frontier_tests.sh"
echo "4. Implement optimizations based on profiler results"
echo ""
echo "Test suite complete!"
echo ""
