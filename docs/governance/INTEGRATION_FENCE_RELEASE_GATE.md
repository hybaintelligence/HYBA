# Integration Fence Release Gate

## Purpose

The Integration Fence is a named release gate that verifies the complete system path from frontend through backend to runtime pool handshake and mining flow. No release candidate is valid unless this gate passes.

## What It Tests

The integration fence comprises 25 deterministic, locally-executable tests organized in three proof layers:

### Layer 1: Frontend/Backend Contract Tests (14/14)
- **Response shape contracts** (4 tests)
  - Health readiness endpoint payload shape
  - Mining status endpoint payload shape
  - Mining job search endpoint payload shape
  - Mining job search parameter acceptance
  
- **Route representation contracts** (10 tests)
  - All public backend routes represented in frontend API client
  - Routes tested: `/organism/executive`, `/organism`, `/organism/regeneration`, `/v4/metabolism`, `/v1/streaming`, `/security/*` (6 routes)

**Purpose:** Proves TypeScript client expectations align with FastAPI runtime responses at schema level. Catches response shape drift, missing fields, parameter mismatches.

### Layer 2: Pool Handshake Contract Tests (5/5)
- Stratum v1 subscribe/authorize state machine with deterministic fake sessions
- Extranonce metadata hydration (extranonce1, extranonce2_size)
- Difficulty event propagation to job context
- Job creation with full handshake metadata
- Stale job marking on clean job notification

**Purpose:** Proves Stratum protocol state machine transitions correctly. Catches pool handshake corruption, lost metadata, incorrect state flags.

### Layer 3: True E2E System Path Tests (6/6)
- **Dashboard bootstrap sequence** (2 tests)
  - Initial health check → readiness check → mining status → job search
  - Optional job search without `job_id` parameter (proves no 422 regression)

- **Mining runtime flow** (4 tests)
  - Pool job → UnifiedMiner._next_job() → engine.search() → candidate handling
  - Local reject never calls guarded submit
  - Guarded accept records feedback and increments accepted counter
  - Guarded reject records feedback without faking acceptance
  - Production mode without live session stops before search (no fabricated telemetry)

**Purpose:** Proves the entire system path moves through state transitions correctly. Catches integration failures where components pass individually but the flow breaks.

## Running the Gate

### Quick Run
```bash
npm run test:integration-fence
```

### Explicit Run
```bash
cd /path/to/HYBA_FULLSTACK
PYTHONPATH=python_backend python -m pytest \
  tests/test_frontend_backend_contracts.py \
  tests/test_pool_handshake_contract.py \
  tests/test_frontend_backend_e2e.py \
  tests/test_runtime_e2e_flow.py \
  -v --tb=short
```

Expected output: **25 passed**

## Release Policy

**No release candidate is valid unless `npm run test:integration-fence` passes.**

- All 25 tests must pass
- Tests run with deterministic fake seams (zero real network, zero credentials)
- Tests are reproducible locally on any developer machine
- Failures indicate integration drift, not environmental issues

## When Integration Fence Fails

If the gate fails, the failure falls into one of three categories:

1. **Layer 1 Failure (Contract shape mismatch)**
   - Backend response shape changed but frontend client didn't
   - Frontend client changed but backend didn't
   - Action: Audit the contract test, fix the mismatch, update both sides

2. **Layer 2 Failure (Pool handshake state)**
   - Stratum subscription/authorization path broken
   - Metadata not hydrated correctly
   - Action: Review StratumClient state transitions, check fake pool seams

3. **Layer 3 Failure (System path)**
   - Dashboard bootstrap sequence broken
   - Mining runtime flow doesn't advance state correctly
   - Guard rejecting incorrectly
   - Action: Trace the flow through UnifiedMiner and engine, check feedback path

## Design Principles

- **Deterministic:** Uses fake pool/engine seams, no real network
- **Auditable:** All tests explicitly state what they prove
- **Reproducible:** Passes locally before any CI/CD involvement
- **Scoped:** Tests system integration paths, not individual components
- **Fast:** Entire suite runs in <1 second

## Distinction from Unit and Property Tests

- **Unit tests** prove individual functions work correctly
- **Property tests** prove behavior holds over a range of inputs
- **Contract tests** prove two components agree on the interface between them
- **E2E tests** prove the system path actually moves through state transitions
- **Integration fence** combines contract + handshake + E2E into one named gate

## Related Gates

- `npm run prod:check` — Production-oriented audit/build/test gate
- `npm run test:all` — Unit tests + property tests + bridge tests
- `npm run test:backend` — All Python unit tests
- `npm run test:property:frontend` — Frontend property tests

The integration fence is distinct from these: it verifies the system moves through complete paths, not just component behavior.
