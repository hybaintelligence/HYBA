# HYBA Quantum, Scaling & Benchmark Test Suite

This test package expands coverage into the **quantum** and **post‑quantum**
components of HYBA FULLSTACK, as well as the golden‑ratio scaling and
benchmark utilities.  It aims to verify deterministic behavior in the
dodecahedral quantum solver, the golden‑ratio accelerated quantum math
functions, and the benchmark helper functions without running the full
1000‑qubit workloads.

## Contents

| File | Purpose |
|---|---|
| `test_dodecahedral_solver.py` | Validates basis generation, nonce range validation, entropy calculations, and hashrate scaling in the dodecahedral quantum solver. |
| `test_phi_accelerated_formalism.py` | Tests golden‑ratio accelerated density matrix operations, folding compression, decoherence suppression, phase modulation, unitary evolution, Grover diffusion, and probability distributions. |
| `test_benchmark_formalism.py` | Checks bond dimension calculations, phi scaling results, trivial mass gap verification, naive state memory estimation, small density matrix benchmarks, and PULVINI compression on small qubits. |

## Running the Tests

From the repository root, ensure the `python_backend` package is on your
`PYTHONPATH` and run:

```bash
PYTHONPATH=python_backend pytest hyba_quantum_scaling_benchmark_tests -q
```

The tests are designed to be lightweight and avoid heavy tensor network
contractions; they focus on boundary conditions, error handling, trace
preservation, normalization, and invariants that must hold across the
quantum and scaling modules.