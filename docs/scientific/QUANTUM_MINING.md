# HYBA Quantum Mining Implementation

This document explains the production-facing quantum mining layer, the mathematical assumptions behind the dodecahedral Grover kernel, how to configure mining search jobs, and how to validate correctness before deployment.

## 1. Mathematical model

The current solver implements a bounded Grover-style amplitude amplification routine over a **20-state dodecahedral basis**. This is NOT an unstructured search over the full 2^32 nonce space — it is a structurally-guided basis selection mechanism that operates on a small symbolic basis and projects results back into nonce ranges.

### Scope clarification

| Parameter | Value | Meaning |
|---|---|---|
| Basis dimension (N) | 20 | Dodecahedron vertices |
| Nonce space | 2^32 | Full uint32 range |
| Marked states (M) | 1 | Target-derived marked index |
| Theoretical optimal steps | floor(π/4 × √(20/1)) = 3 | Grover iterations on basis |
| Nonce projection | Offset % search_space | Basis index → nonce candidate |

The Grover iteration operates **only** on the 20-dimensional dodecahedral basis. The measured basis index is projected into the configured nonce ranges. **No quantum speedup over SHA-256 preimage search is claimed or implied.** The actual hash verification (double-SHA256) is still performed classically.

A scope certificate is available for any configuration via:

```python
from pythia_mining.pulvini_grover_certificate import grover_scope_certificate
cert = grover_scope_certificate(target=target, nonce_ranges=nonce_ranges)
assert not cert.quantum_speedup_claimed
assert cert.deterministic_behavior
```

### Grover search

For an unstructured search space with `N` states and `M` marked states, Grover amplitude amplification reaches its first maximum after approximately:

```text
floor((pi / 4) * sqrt(N / M))
```

For the current dodecahedral basis, `N = 20`. The solver treats the marked state as a deterministic function of the pool target and declared nonce ranges, then projects the measured basis index back into the configured nonce space.

Reference: Lov K. Grover, *A fast quantum mechanical algorithm for database search*, 1996, arXiv:quant-ph/9605043.

### Efficiency comparison

A honest side-by-side comparison shows the true scope:

| Configuration | Theoretical steps | Notes |
|---|---|---|
| Grover on N=20 (this system) | ~3 | Basis selection, not SHA-256 acceleration |
| Grover on N=2^32 (full space) | ~65,535 | Not implemented — requires quantum computer |
| Classical brute force (2^32) | 4,294,967,296 | Full nonce enumeration |

The ~3-step Grover iteration selects **which nonce to try**, not whether it solves the hash. The actual hash verification is classical double-SHA256.

Full efficiency report:
```python
from pythia_mining.pulvini_grover_certificate import grover_efficiency_report
report = grover_efficiency_report()
```

### Caveat for pool operators

The deterministic nonce selection means that for the same pool job (same target and nonce ranges), the solver will produce the **same nonce candidate first**. This is not a bug — it is a design property that makes behavior predictable and auditable. It also means:
- Each new pool job (with different target) produces a different nonce sequence.
- Nonce-space coverage is maintained by the 32-lane partition, not by random sampling.
- The solver's advantage is structured coverage, not brute-force speed.

### Dodecahedral basis (basis selection, not nonce enumeration)

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

### Oracle and diffusion operators (on 20-state basis only)

The Grover loop applies:

```text
O = I - 2|w><w|
D = 2|s><s| - I
G = D·O
```

`O` flips the phase of the marked state. `D` reflects amplitudes about the uniform-superposition mean. Each iteration increases measurement probability of the marked state under finite-precision normalization.

## 2. Production configuration contract

Production mode is enabled when `NODE_ENV=production` or `HYBA_ENV=production`. In production, every enabled pool must be configured through environment variables or injected configuration; development fixture credentials and simulated jobs are blocked.

Minimum production pool configuration for one pool:

```bash
export NODE_ENV=production
export HYBA_POOL_NICEHASH_URL='stratum+ssl://sha256.eu.nicehash.com:33334'
export HYBA_POOL_NICEHASH_USERNAME='<secret-managed-username>'
export HYBA_POOL_NICEHASH_PASSWORD='<secret-managed-password>'
```

Supported pool environment key pattern:

```text
HYBA_POOL_<POOL_ID>_URL
HYBA_POOL_<POOL_ID>_USERNAME
HYBA_POOL_<POOL_ID>_PASSWORD
HYBA_POOL_<POOL_ID>_STRATUM_VERSION
```

Current pool IDs are `NICEHASH`, `VIABTC`, `BRAIINS`, and `CKPOOL`.

Optional capacity estimate:

```bash
export HYBA_QUANTUM_CAPACITY_EHS='<explicit-positive-capacity-estimate>'
```

If `HYBA_QUANTUM_CAPACITY_EHS` is absent, `hashrate_ehs` is reported as `null` with `capacity_source=not_configured`. This prevents dashboards from mistaking static or aspirational values for measured production telemetry.

## 3. Solver configuration contract

The solver must be configured from a real mining job before solving:

```python
await solver.configure_search(target=job.target, nonce_ranges=[(0, 2**32 - 1)])
nonce = await solver.solve(max_iterations=25, timeout=5.0)
```

`target` must be a positive non-zero integer. `nonce_ranges` must be non-empty inclusive uint32 ranges with `start <= end`.

Invalid targets or ranges raise `QuantumSolverConfigurationError` immediately, rather than allowing malformed pool input to leak into the Grover kernel.

## 4. Local proof-of-work validation

Local share accounting must go through `validate_and_record_share()` so counters are backed by Bitcoin-compatible block-header and target validation.

The validation pipeline performs:

1. coinbase assembly from Stratum coinbase parts, extranonce1, and extranonce2
2. double-SHA256 coinbase hash
3. merkle-root reconstruction from the job merkle branch
4. 80-byte block-header construction with Bitcoin byte ordering
5. double-SHA256 block hash
6. compact `nbits` target expansion and effective target comparison

Ordinary losing shares return a rejected `ShareResult`; malformed jobs raise validation errors and are counted as rejected.

## 5. Pool operation and degraded state

`PoolManager.get_best_pool()` probes the active pool and then every configured fallback pool. If all pools fail connection/authentication, it raises `AllPoolsOfflineError`.

Mining loops should catch this exception and enter extended backoff or alerting instead of spinning against disconnected clients:

```python
try:
    active_pool = await pool_manager.get_best_pool()
except AllPoolsOfflineError:
    # enter degraded state, alert, and back off
    ...
```

Pool status includes `connection_state`, `connection_failures`, `last_failure_at`, and share counters for monitoring dashboards.

## 6. Development fixtures

`inject_dev_fixture_target_job()` is a development/test fixture only. It is disabled in production by default.

Do not enable `HYBA_ALLOW_DEV_FIXTURES=true` in production. That flag exists only for controlled diagnostics and must never be used for live share submission.

## 7. Validation and CI

Run the backend tests with:

```bash
python -m unittest tests.test_backend_workflows
```

The production-readiness CI workflow also runs:

- backend unit, integration-smoke, adversarial, and randomized property-style tests
- frontend/server build
- production guardrails proving missing pool configuration is rejected
- production guardrails proving simulated jobs are blocked even when pool config is present

The current suite covers:

- deterministic substrate initialization
- absence of fake capacity telemetry unless capacity is explicitly configured
- configured capacity monotonicity under power scaling
- solver rejection of zero/negative targets and malformed nonce ranges
- randomized property-style checks that solved nonces stay inside configured ranges
- timeout behavior that returns `None` without crashing the mining loop
- all-pools-offline detection
- local share validation before accounting
- Bitcoin-compatible 80-byte block-header construction and compact-target expansion

## 8. Operational guardrails

- Never accept a pool job with `target <= 0`.
- Never run the solver with an empty nonce search space.
- Never report capacity/hashrate unless it is measured or explicitly configured as an estimate.
- Treat `None` from `solve()` as a non-fatal solve failure and proceed with retry/backoff.
- Treat `AllPoolsOfflineError` as a degraded operational state requiring observability signal.
- Keep real pool credentials in secret storage/environment variables. Do not commit production credentials.
- Validate merkle roots and block headers locally before submitting or accounting for shares.
- Keep simulated jobs and dev fixture credentials out of production.

## 9. Remaining production milestones

The code now removes hardcoded production credentials, blocks production fixtures, avoids fake capacity telemetry, validates local proof-of-work, and enforces these rules in CI. Remaining work should focus on live-network integration, not simulation cleanup:

1. Replace deterministic handshake placeholders with real Stratum socket/WebSocket I/O.
2. Parse real `mining.notify`, `mining.set_difficulty`, subscribe, authorize, and submit responses.
3. Add controlled test-pool end-to-end share submission verification.
4. Add deployment-level secret scanning and runtime alerting for degraded pool state.
