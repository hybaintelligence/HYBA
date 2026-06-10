# HYBA Quantum Mining Implementation

This document explains the production-facing quantum mining layer, the mathematical assumptions behind the dodecahedral Grover kernel, how to configure mining search jobs, and how to validate correctness before deployment.

## 1. Mathematical model

The current solver implements a bounded Grover-style amplitude amplification routine over a 20-state dodecahedral basis.

### Grover search

For an unstructured search space with `N` states and `M` marked states, Grover amplitude amplification reaches its first maximum after approximately:

```text
floor((pi / 4) * sqrt(N / M))
```

For the current dodecahedral basis, `N = 20`. The solver treats the marked state as a deterministic function of the pool target and declared nonce ranges, then projects the measured basis index back into the configured nonce space.

Reference: Lov K. Grover, *A fast quantum mechanical algorithm for database search*, 1996, arXiv:quant-ph/9605043.

### Dodecahedral basis

The dodecahedral basis uses the 20 vertices of a regular dodecahedron:

```text
(±1, ±1, ±1)
(0, ±1/Φ, ±Φ)
(±1/Φ, ±Φ, 0)
(±Φ, 0, ±1/Φ)
```

where `Φ = (1 + sqrt(5)) / 2` is the golden ratio. Each vertex is normalized and assigned a deterministic phase:

```text
exp(i * 2π * k * Φ)
```

This keeps the representation deterministic and auditable while retaining dodecahedral symmetry in the complex state vector.

### Oracle and diffusion operators

The Grover loop applies:

```text
O = I - 2|w><w|
D = 2|s><s| - I
G = D·O
```

`O` flips the phase of the marked state. `D` reflects amplitudes about the uniform-superposition mean. Each iteration increases measurement probability of the marked state under finite-precision normalization.

## 2. Configuration contract

The solver must be configured before production use:

```python
await solver.configure_search(target=job.target, nonce_ranges=[(0, 2**32 - 1)])
nonce = await solver.solve(max_iterations=25, timeout=5.0)
```

`target` must be a positive non-zero integer. `nonce_ranges` must be non-empty inclusive uint32 ranges with `start <= end`.

Invalid targets or ranges raise `QuantumSolverConfigurationError` immediately, rather than allowing malformed pool input to leak into the Grover kernel.

## 3. Pool operation and degraded state

`PoolManager.get_best_pool()` probes the active pool and then every configured fallback pool. If all pools fail connection/authentication, it raises `AllPoolsOfflineError`.

Mining loops should catch this exception and enter extended backoff or alerting instead of spinning against disconnected clients:

```python
try:
    active_pool = await pool_manager.get_best_pool()
except AllPoolsOfflineError:
    # enter degraded state, alert, and back off
    ...
```

Pool status now includes `connection_state`, `connection_failures`, and `last_failure_at` for monitoring dashboards.

## 4. Validation and tests

Run the backend tests with:

```bash
python -m unittest tests.test_backend_workflows
```

The current suite covers:

- deterministic substrate initialization
- hashrate monotonicity under power scaling
- solver rejection of zero/negative targets and malformed nonce ranges
- randomized property-style checks that solved nonces stay inside configured ranges
- timeout behavior that returns `None` without crashing the mining loop
- all-pools-offline detection
- mining integration smoke path: pool connection, simulated job, solver configuration, solve, and share accounting

## 5. Operational guardrails

- Never accept a pool job with `target <= 0`.
- Never run the solver with an empty nonce search space.
- Treat `None` from `solve()` as a non-fatal solve failure and proceed with retry/backoff.
- Treat `AllPoolsOfflineError` as a degraded operational state requiring observability signal.
- Keep real pool credentials in secret storage/environment variables. Do not commit production credentials.
- For production pool submission, add full double-SHA256 block-header validation and merkle-root construction before submitting shares.

## 6. Remaining critical production work

The solver hardening in this change addresses validation, numerical safety, offline-pool detection, documentation, and tests. The following items remain separate production milestones:

1. Full Bitcoin-compatible double-SHA256 block header validation.
2. Merkle branch reconstruction from actual Stratum job payloads.
3. Credential externalization for all pool usernames/passwords.
4. End-to-end share submission verification against a controlled test pool.
5. CI enforcement for unit, integration, property-style, lint, and type-check jobs.
