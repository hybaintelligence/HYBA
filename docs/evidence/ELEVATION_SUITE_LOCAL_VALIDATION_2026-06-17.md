# Elevation Suite Local Validation Evidence — 2026-06-17

**BLUF:** local execution of `tests/test_elevation_suite.py` completed with **40 passed, 2 skipped, 0 failed** on macOS/Darwin using Python 3.12.13 and pytest 8.3.4. The two skips are expected conditional skips for SLD checks when the evolved system lands in a pure/trivial state with insufficient off-diagonal coherence.

This is local evidence, not hosted CI evidence. It supports bounded mathematical-runtime invariants only; it does not certify mining revenue, live pool acceptance, SHA-256 acceleration, phenomenal consciousness, Yang-Mills proof, or production economics.

## Command

```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK && \
  .venv/bin/python3 -m pytest tests/test_elevation_suite.py -v --tb=short
```

## Observed result

```text
collected 42 items
40 passed, 2 skipped, 0 failed
```

Skipped tests:

- `tests/test_elevation_suite.py::TestSLDNaturalGradient::test_sld_satisfies_lyapunov_equation`
- `tests/test_elevation_suite.py::TestSLDNaturalGradient::test_sld_is_hermitian`

The skips are admissible because the tests explicitly skip only when the state is pure/trivial or lacks measurable off-diagonal coherence. They should not be counted as failures, but they also should not be counted as non-trivial SLD/Lyapunov proof for that specific local run.

## Certified surfaces

### SU(2) Wilson plaquette action

The suite verifies that:

- `_su2_from_byte` produces 2x2 unitary matrices with determinant magnitude 1;
- links on different Pauli axes are non-commuting;
- `YANG_MILLS_GAP` is consistent with `3 - φ`;
- `phi_resonance` remains bounded in `[0, 1]`;
- the action is deterministic and uint32 wrapping is stable.

Bounded claim: this certifies the implemented SU(2)/plaquette runtime invariants. It is not a proof of the Yang-Mills Millennium problem.

### Van der Corput / φ-LCG discrepancy

The suite verifies that:

- `van_der_corput_discrepancy(1000)` and `(10000)` satisfy the implemented golden-optimal certificate boundary;
- the three-distance theorem check stays within three gap sizes for tested sample sizes;
- empirical discrepancy decreases as N grows;
- the implementation outperforms its Monte Carlo baseline in the tested configuration;
- the theoretical bound formula matches `(1 + 1/φ) / N`.

Bounded claim: this certifies deterministic low-discrepancy behavior for the implemented test cases, not universal optimality across all samplers and all N.

### Exact MPS norm and entanglement spectrum

The suite verifies that:

- `_contract_mps_norm_exact` agrees with `MPS.compute_norm`;
- local unitary operations preserve norm;
- single-site contraction is correct;
- uniform tensor rescaling follows the expected norm scaling law;
- entanglement spectra are non-empty, non-negative, descending, and bounded by bond dimension;
- von Neumann entropy computed from spectra is non-negative.

Bounded claim: this certifies exact MPS norm/spectrum invariants for the implemented tensor-network surface, not arbitrary quantum-system simulation correctness.

### Adaptive compression

The suite verifies that:

- adaptive compression preserves site count;
- output norm remains approximately one;
- bond dimensions respect `base_max_bond`;
- high-entropy bonds retain at least as much dimension as low-entropy bonds in the tested configuration.

Bounded claim: this certifies implemented Φ-weighted adaptive compression behavior for tested MPS configurations.

### SLD natural gradient / QFI

The suite verifies that:

- `bures_gradient_of_collapse_functional` returns required keys;
- gradient norm and QFI trace are non-negative;
- zero-gradient pure/trivial cases are stationary;
- `qgt_norm` equals `bures_gradient_norm`;
- gradient magnitude responds to entropy-gradient magnitude in the tested non-stationary cases.

Bounded claim: this certifies implemented SLD/QFI bookkeeping and stationarity semantics. The two skipped tests show that the local run did not exercise a non-trivial off-diagonal SLD/Lyapunov/Hermitian case.

## Claim boundary

This evidence supports the repository-local Nodus Solutus posture: the claim is admissible because it is tied to source, a local command, and a bounded result.

It does **not** prove:

- that the physical universe is computable;
- guaranteed mining revenue;
- live-pool accepted-share economics;
- SHA-256 quantum acceleration;
- phenomenal consciousness or subjective experience;
- the Yang-Mills Millennium problem;
- legal, treasury, solvency, or regulatory approval.

## Reproduction command for manifest

```bash
.venv/bin/python3 -m pytest tests/test_elevation_suite.py -v --tb=short
```
