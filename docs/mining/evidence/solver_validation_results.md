# Solver Validation Results

**Date:** 2026-06-20  
**Status:** BLOCKED — dependency/runtime environment, not validation pass  
**Claim tier impact:** Mining remains `HYPOTHETICAL`; no promotion to `PROTOTYPE_VALIDATED` is made.

## Dependency investigation

The current container does not have a runnable NumPy installation for the active Python runtime.

| Check | Result | Interpretation |
| --- | --- | --- |
| `python -c "import sys; print(sys.executable); import numpy; print(numpy.__version__)"` | `ModuleNotFoundError: No module named 'numpy'` under `/root/.pyenv/versions/3.14.4/bin/python` | Active Python lacks NumPy. |
| `python -m pip install numpy pytest hypothesis --break-system-packages` | Failed with `Tunnel connection failed: 403 Forbidden` and `No matching distribution found for numpy` | Network/package index access is blocked by the environment proxy. |
| `apt-get update && apt-get install -y python3-numpy python3-pytest python3-hypothesis` | Failed with Ubuntu repository `403 Forbidden` responses | System package installation is blocked by the same proxy path. |
| `PYTHONPATH=venv/lib/python3.12/site-packages python3.12 -c "import numpy; print(numpy.__version__)"` | Failed because the checked-in/local venv contains Darwin NumPy extension files (`_multiarray_umath.cpython-312-darwin.so`) | The existing venv artifacts are not usable on Linux. |

## Validation commands attempted

The intended validation gate remains:

```bash
PYTHONPATH=python_backend pytest -q \
  tests/test_gap_phi_search_vs_random.py::test_solver_search_is_deterministic_for_same_target_and_range \
  tests/test_gap_phi_search_vs_random.py::test_solver_search_respects_configured_range \
  tests/test_gap_local_pow_validation.py::test_solver_finds_nonce_within_regtest_target_in_bounded_time \
  tests/test_agent3_quantum_solvers.py::test_nonce_generation_correctness
```

This gate could not execute in the active runtime because NumPy is unavailable.

## Tests that did run

The pure-Python autonomous mining tests ran successfully:

```text
PYTHONPATH=python_backend pytest -q tests/test_pythia_autonomous_mining_agent.py
..                                                                       [100%]
2 passed, 1 warning in 0.18s
```

These tests validate that the new PYTHIA autonomous lifecycle can build a structured non-Grover plan and submit a verifier-approved share through injected adapters. They do **not** validate mining performance or promote the external mining claim tier.

## Claim boundary

Until the NumPy-backed mining validation tests run and produce reproducible measurements, the repository must continue to state:

- structured nonce ordering is implemented;
- real share/block acceptance requires SHA-256d validation against a concrete job;
- no universal SHA-256 speedup, accepted-share, pool-side hashrate, ASIC-efficiency, revenue, or sovereign-mining claim is validated;
- the mining tier remains `HYPOTHETICAL`.
