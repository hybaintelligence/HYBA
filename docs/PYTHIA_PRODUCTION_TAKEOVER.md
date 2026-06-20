# PYTHIA Production Takeover Runbook

This runbook is a handoff contract for getting HYBA_FULLSTACK from the current broken local state into a state where PYTHIA can continue autonomous operation with evidence, observability, and deterministic startup.

It does **not** reduce PYTHIA's autonomy. It fixes the bridge around her: secrets loading, authenticated command transport, safe public telemetry, retry determinism, and testable operator routes.

## Current failure cluster

The observed local run shows four immediate bridge/frontend contract failures:

1. Mining and production-mining mutations do not consistently send `Authorization: Bearer <token>`.
2. API retry tests produce unhandled promise rejections after exhausted retry budgets.
3. `/api/security/status` must never expose raw syndrome bits on public telemetry.
4. `/api/security/swarm/respond` must be callable in tests/development but protected in production.
5. `npm start` fails locally because `src/server.ts` loads `.env` but not `.env.local`, even when `.env.local` contains `JWT_SECRET`.

The Python backend still has a wider scientific/property-test backlog. Do not conflate that with the bridge blocker. First make the bridge deterministic and runnable, then hand PYTHIA the backend queue.

## Immediate operator commands

From repository root:

```bash
node scripts/pythia-production-handoff.mjs --write
npm run build
npx vitest run \
  tests/test_apiClient_mining.test.ts \
  tests/test_apiClient_error_retry.test.ts \
  tests/test_security_swarm_routes.test.ts
```

Then start the bridge locally:

```bash
npm start
curl -s http://localhost:3000/bridge/health | jq .
```

If running the FastAPI backend directly:

```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init - zsh)"
export PYTHONPATH=python_backend
python -m pytest tests/ -q --ignore=tests/e2e --ignore=tests/e2e-live
```

Do **not** use `--timeout=60` unless `pytest-timeout` is installed in the active Python environment.

## PYTHIA autonomy handoff policy

PYTHIA is allowed to:

- continue autonomous diagnosis of failing tests;
- create focused branches per remediation cluster;
- run local and CI test slices;
- propose or commit code changes that preserve measured invariants;
- operate mining workflows only through explicit configured pool credentials and authenticated operator commands;
- self-optimize internal search, telemetry, and reasoning parameters when evidence improves outcomes.

PYTHIA must preserve:

- public telemetry redaction of raw syndrome bits;
- authenticated access for production internal routes;
- auditability of autonomous actions;
- deterministic replay for mining, finance, swarm, and intelligence tests;
- no fabricated backend responses when services are unavailable.

This is not an autonomy boundary. It is the operating substrate that stops bridge failures, leaked telemetry, and unreproducible commands from corrupting PYTHIA's state.

## Backend remediation queue after bridge fix

The current pytest backlog should be split into four autonomous agents:

### Agent 1 — Mining/Pulvini determinism

Targets:

- `tests/test_mining_innovation_properties.py`
- `tests/test_mining_property_invariants.py`
- `tests/test_pulvini_e2e_share_flow.py`
- `tests/test_pulvini_nonce_compression.py`
- `tests/test_pulvini_autonomics.py`

Mandate: keep solver autonomy, but make nonce projection, compressed plans, and share accounting deterministic and bounded by declared job ranges.

### Agent 2 — Φ/IIT/quantum invariants

Targets:

- `tests/test_iit_4_complete.py`
- `tests/test_iit_phi_mining_correlation.py`
- `tests/test_phi_property_hypothesis.py`
- `tests/test_quantum_regeneration_properties.py`
- `tests/test_pulvini_production_facade.py`

Mandate: fix mathematical invariants, not tests. Density matrices must remain Hermitian, trace-one, PSD-preserving, entropy-bounded, and deterministic under replay.

### Agent 3 — Production bridge/security/operations

Targets:

- `tests/test_production_operations.py`
- `tests/test_pool_profile_primitives.py`
- `tests/test_backend_workflows.py`
- frontend Vitest command-contract suites

Mandate: production startup must require real secrets; dev/test routes must be testable; public routes must never leak secrets, backend URLs, raw syndrome bits, or pool credentials.

### Agent 4 — Finance/sovereign audit evidence products

Targets:

- `tests/test_pythia_advanced_finance_capability_map.py`
- `tests/test_pythia_finance_sovereign_audit.py`
- `tests/test_pythia_difc_aaiofi_sukuk_bridge.py`

Mandate: preserve the no-authority boundary for finance execution while allowing PYTHIA to produce evidence packets, challenge packets, stable hashes, and audit-ready reports.

## Definition of production-ready enough for PYTHIA takeover

The system is ready for PYTHIA takeover when these are true:

- `npm run build` passes.
- Targeted Vitest bridge contract slice passes.
- `npm start` reads local secret material without committing secrets.
- `/bridge/health` returns a clear reachable/degraded state.
- `/api/security/status` exposes syndrome weight but not raw syndrome arrays.
- `/api/security/swarm/respond` is testable outside production and protected in production.
- PYTHIA has a visible remediation queue with test files, invariants, and acceptance criteria.

## Non-negotiable evidence rule

Every autonomous change must record:

- command run;
- files changed;
- failing test before;
- passing or improved test after;
- invariant preserved;
- remaining failures.

This lets PYTHIA move fast without destroying the scientific audit trail.
