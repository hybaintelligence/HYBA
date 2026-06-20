# HYBA_FULLSTACK Tests

This directory contains the primary test suite for HYBA_FULLSTACK.

## Quick Stats
- **Total Pytest Tests**: 2628
- **Test Directories (Pytest)**:
  - `tests/`: Main test suite
  - `additional_tests/`: Supplementary tests
  - `hyba_intelligence_tests/`: Intelligence layer tests
  - `hyba_quantum_scaling_benchmark_tests/`: Quantum scaling benchmarks
- **Frontend Tests**: 44 files, managed with Vitest/Playwright

## Test Categories
1. **Autonomous Mining** (170+ passing tests)
   - Controller logic
   - Property-based invariants
   - Adversarial/abuse cases
   - Stress/load testing
   - Operator control tests
2. **Fault-Tolerant Quantum**
   - Logical qubit operations
   - Error correction
   - Quantum mining integration
3. **Intelligence Layer**
   - Consciousness engine scaling
   - Mass gap shielding
   - Memory fabric tests
4. **Backend/API**
   - FastAPI endpoint tests
   - Prediction service integration
5. **Quantum Scaling Benchmarks**
   - Performance measurements
   - Scaling characteristics

## Running Tests

### Python Tests (Pytest)
```bash
# All tests
PYTHONPATH=python_backend python -m pytest

# Specific test file
PYTHONPATH=python_backend python -m pytest tests/test_autonomous_mining_controller.py

# Focused autonomy/quantum slice (170 tests)
PYTHONPATH=python_backend python -m pytest \
  tests/test_autonomous_mining_controller.py \
  tests/test_autonomous_mining_stress.py \
  tests/test_autonomous_mining_adversarial.py \
  tests/test_autonomous_mining_properties.py \
  tests/test_autonomous_mining_expanded_property_adversarial.py \
  tests/test_fault_tolerant_quantum.py
```

### Frontend Tests
```bash
npm test
npm run test:frontend
npm run test:e2e  # Playwright
```

## Key Files
- `pyproject.toml`: Pytest configuration (defines `testpaths` and `norecursedirs`)
- `.python-version`: Specifies Python 3.12.7
- `.nvmrc`: Specifies Node 22

## Collection Hygiene
Pytest is configured to ignore:
- Scripts in `scripts/` (no more import-time `SystemExit`)
- Build artifacts, node_modules, etc.

## Expanded Property/Adversarial Tests
The file `tests/test_autonomous_mining_expanded_property_adversarial.py` contains:
- Target bandit invariant tests
- Unknown target fallback behavior
- Low-cardinality metric tests under hostile inputs
- Non-finite pool telemetry resilience
- Circuit breaker degradation bounds
- Persistence round-trip shape
- Hostile operator approval payload normalization
