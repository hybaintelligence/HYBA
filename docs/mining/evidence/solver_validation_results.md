# Solver Validation Results

**Date:** 2026-06-20  
**Status:** PARTIALLY VALIDATED — NumPy blocker resolved, benchmarks pass  
**Claim tier impact:** Mining remains `HYPOTHETICAL`; no promotion to `PROTOTYPE_VALIDATED` is made.

## NumPy Blocker Resolution

The NumPy environment blocker has been resolved on the local development machine:

| Check | Result | Interpretation |
| --- | --- | --- |
| `python -c "import numpy; print(numpy.__version__)"` | `2.4.6` | NumPy installed via pip under pyenv Python 3.12.7 on Darwin arm64 |
| `pip install numpy` | Success (downloaded numpy-2.4.6-cp312-cp312-macosx_14_0_arm64.whl) | Package index accessible from this environment |
| `PYTHONPATH=python_backend python -m pytest tests/test_mining_capability_benchmarks.py -v -s` | All benchmarks pass | Capability suite fully functional |

## Benchmark Results

### Capability Benchmark Suite (7 benchmarks)
```
✅ HENDRIX-Φ solver throughput: 49,197.84 nonces/sec (baseline: 30,000, ratio: 1.640x)
✅ M32 embedding throughput: 31,701,579.09 nonces/sec (baseline: 50,000, ratio: 634.03x)
✅ φ-resonance mean score: 0.7854 [0,1] (baseline: 0.5, ratio: 1.571x) ±0.1190 over 50,000 samples
✅ φ-resonance score std dev: 0.1190 [0,1] (baseline: 0.15, ratio: 0.793x)
✅ φ-resonance top 1% threshold: 0.9463 [0,1] (baseline: 0.85, ratio: 1.113x)
✅ Yang-Mills gate pass rate: 0.4011 fraction (baseline: 0.4011, ratio: 1.000x)
✅ Stratum message serialization throughput: 228,806.77 msgs/sec (baseline: 5,000, ratio: 45.76x)
```

### φ-Search vs Random (7 tests)
```
✅ φ-ordering reaches valid nonce no later than sequential on regtest
✅ φ-ordering finds high-resonance nonce faster than sequential
✅ φ-ordering is a complete permutation (no candidates dropped)
✅ Voronoi domain assignment is deterministic over uint32 range
✅ φ-gradient proposal stays within uint32 bounds
✅ Solver respects configured nonce range during search
✅ Search is deterministic for same (target, range)
```

### Autonomous Mining Agent (2 tests)
```
✅ PYTHIA autonomous lifecycle submits verified share
✅ PYTHIA autonomous plan is structured (not Grover)
```

## Key Performance Metrics

| Metric | Value | Interpretation |
|--------|-------|---------------|
| HENDRIX-Φ solver throughput | 49,198 nonces/sec | 1.64x baseline (30K) — healthy |
| φ-resonance mean score | 0.7854 | Well-distributed across [0,1] |
| φ-resonance std dev | 0.1190 | Meaningful variation in scores |
| Top 1% φ-resonance threshold | 0.9463 | High-scoring nonces are identifiable |
| Yang-Mills gate pass rate | 0.4011 | Gate is active, not degenerate |
| Stratum throughput | 228,807 msgs/sec | 45.76x baseline — excellent |

## Claim Boundary

Despite successful benchmark validation, the following remain unvalidated:

- ❌ No real/testnet header fixture for double-SHA-256 validation
- ❌ No actual double-SHA-256 nonce loop (benchmarks use synthetic targets)
- ❌ No pool-side accepted-share evidence
- ❌ No ASIC-efficiency comparison
- ❌ No hashrate measurement on real hardware
- ❌ No revenue or sovereign mining claim

**Mining tier remains `HYPOTHETICAL`** until the above are addressed.

## Reproduction

To reproduce these results:

```bash
# Prerequisites: Python 3.12+, NumPy, pytest
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"

# Install dependencies
pip install numpy pytest pytest-asyncio hypothesis

# Run capability benchmarks
PYTHONPATH=python_backend python -m pytest tests/test_mining_capability_benchmarks.py -v -s

# Run φ-search vs random tests
PYTHONPATH=python_backend python -m pytest tests/test_gap_phi_search_vs_random.py -v -s

# Run autonomous mining agent tests
PYTHONPATH=python_backend python -m pytest tests/test_pythia_autonomous_mining_agent.py -v -s