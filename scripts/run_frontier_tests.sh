#!/bin/bash

# Frontier Tests Runner Script
# Executes all three frontier tests with proper environment setup

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=================================="
echo "FRONTIER TESTS EXECUTION"
echo "=================================="
echo "Project Root: $PROJECT_ROOT"
echo ""

# Setup Python path
export PYTHONPATH="$PROJECT_ROOT/python_backend:$PYTHONPATH"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python Version: $PYTHON_VERSION"
echo ""

# 1. Manifold Stress Test
echo "=================================="
echo "TEST 1: MANIFOLD COLLAPSE STRESSER"
echo "=================================="
echo "Finding the geometric stability horizon..."
echo ""

python3 "$PROJECT_ROOT/tests/frontier_manifold_stress.py" || {
    echo "⚠️  Manifold stress test failed or encountered limits"
}

echo ""
echo ""

# 2. Latency Profiler
echo "=================================="
echo "TEST 2: CONSCIOUSNESS LATENCY PROFILER"
echo "=================================="
echo "Identifying the 11ms bottleneck..."
echo ""

python3 "$PROJECT_ROOT/scripts/profile_consciousness_latency.py" --dim 32 --iterations 100 || {
    echo "⚠️  Latency profiler failed or encountered issues"
}

echo ""
echo ""

# 3. Quantum Adversary
echo "=================================="
echo "TEST 3: QUANTUM ADVERSARY"
echo "=================================="
echo "Testing post-quantum resilience..."
echo ""

python3 "$PROJECT_ROOT/tests/frontier_quantum_adversary.py" || {
    echo "⚠️  Quantum adversary test failed or encountered issues"
}

echo ""
echo ""
echo "=================================="
echo "FRONTIER TESTS COMPLETE"
echo "=================================="
echo ""
echo "Results summary:"
echo "  - Check console output above for detailed metrics"
echo "  - Manifold stress identifies the critical dimension"
echo "  - Latency profiler shows bottleneck breakdown"
echo "  - Adversary test shows resilience percentage"
echo ""
echo "Next steps:"
echo "  1. Review bottleneck recommendations from profiler"
echo "  2. Implement Metal/MPS acceleration for LINALG"
echo "  3. Enhance repair convergence for adversary resilience"
echo ""
