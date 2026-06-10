# HYBA Mining Launch Runbook

This runbook converts the existing HYBA/PULVINI mining contracts into a safe launch sequence for pool-based mining.

## 1. Configure secrets outside Git

Copy `config/mining.pools.example.env` into your secret manager, deployment platform, or an untracked local `.env` file.

Never commit real pool usernames, payout addresses, worker names, passwords, or API keys.

## 2. Required production flags

```bash
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
```

Production mode intentionally blocks simulated jobs and fixture credentials.

## 3. Deterministic declared hashrate

Set the configured HYBA/PULVINI capacity estimate:

```bash
export HYBA_QUANTUM_CAPACITY_EHS='<positive numeric value>'
```

This is the deterministic capacity contract used by dashboards and orchestration. It should be treated as configured capacity, not pool-measured telemetry.

## 4. Configure pools

Supported pool IDs:

- `NICEHASH`
- `VIABTC`
- `BRAIINS`
- `CKPOOL`

Each enabled pool uses this pattern:

```bash
export HYBA_POOL_<POOL_ID>_URL='stratum+ssl://...'
export HYBA_POOL_<POOL_ID>_USERNAME='<secret-managed-user-or-wallet-worker>'
export HYBA_POOL_<POOL_ID>_PASSWORD='<secret-managed-password>'
export HYBA_POOL_<POOL_ID>_STRATUM_VERSION='v1'
```

## 5. Pre-flight checks

Run the backend workflow tests:

```bash
python -m unittest tests.test_backend_workflows
```

Run the production math primitive tests:

```bash
python -m pytest tests/test_production_math_primitives.py
```

Run the Phi block analyser math tests:

```bash
python -m pytest tests/test_phi_block_analyser_math.py
```

## 6. Operational expectations

Before live mining, confirm:

1. Pool credentials authenticate.
2. At least one pool reaches `AUTHENTICATED` state.
3. Simulated jobs are rejected in production.
4. Local share validation runs before accounting.
5. All-pools-offline state alerts and backs off instead of spinning.
6. Configured hashrate is shown as configured estimate, not measured telemetry.

## 7. Day-one pool strategy

Suggested launch posture:

1. Start with one pool in production and all others configured as fallback.
2. Confirm successful subscribe/authorize/job flow.
3. Confirm local validation for candidate shares.
4. Enable failover in order: primary, secondary, tertiary, solo fallback.
5. Monitor rejected shares, stale shares, latency, pool failover, and configured-vs-observed capacity.

## 8. What this does not replace

This runbook does not replace:

- ASIC firmware configuration;
- pool account verification;
- payout address verification;
- electricity/cooling checks;
- legal/accounting review;
- deployment secret scanning.

## 9. Launch/no-launch rule

Launch only if:

- credentials are secret-managed;
- production fixtures are blocked;
- tests pass;
- at least one real pool authenticates;
- local share validation is active;
- monitoring is live.

If any of these fails, enter `REVIEW_REQUIRED` and do not run unattended.
