#!/bin/bash
set -e

echo "========================================"
echo "HYBA Local Acceptance Validation"
echo "========================================"
echo ""

# Step 1: Pycompile check
echo "Step 1: Running pycompile check..."
python3 -m py_compile \
    python_backend/pythia_mining/replay_executor.py \
    python_backend/pythia_mining/manifest_registry.py \
    python_backend/pythia_mining/mining_auto_attester.py \
    scripts/replay_claim.py
echo "✅ Pycompile check passed"
echo ""

# Step 2: Test suite
echo "Step 2: Running test suite..."
PYTHONPATH=python_backend python3 -m pytest \
    tests/test_replay_executor.py \
    tests/test_manifest_registry.py \
    tests/test_replay_claim_cli.py \
    tests/test_replay_reporting.py \
    tests/test_mining_auto_attester.py \
    tests/test_reproducibility_evidence_gate.py \
    tests/test_replay_properties.py \
    -q
echo "✅ All replay tests passed"
echo ""

# Step 3: Example replay validations
echo "Step 3: Running example replay validations..."
echo "  - replay_nonce example..."
PYTHONPATH=python_backend python3 scripts/replay_claim.py replay \
    examples/replay_nonce/manifest.json --cwd examples/replay_nonce

echo "  - replay_matrix example..."
PYTHONPATH=python_backend python3 scripts/replay_claim.py replay \
    examples/replay_matrix/manifest.json --cwd examples/replay_matrix
echo "✅ All example replays verified"
echo ""

echo "========================================"
echo "✅ ALL LOCAL ACCEPTANCE GATES PASSED"
echo "========================================"
echo ""
echo "Summary:"
echo "  - Pycompile: PASS"
echo "  - Test suite (23 tests): PASS"
echo "  - Example replays (2): PASS"
echo ""
echo "See docs/CI_LIMITATIONS_AND_LOCAL_EVIDENCE.md for details"
