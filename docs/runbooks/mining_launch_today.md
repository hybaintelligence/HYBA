# HYBA Mining Launch Runbook

This runbook converts the existing HYBA/PULVINI mining contracts into a safe launch sequence for pool-based mining.

## 1. Configure secrets outside Git

Copy `config/mining.pools.example.env` into your secret manager, deployment platform, or an untracked local `.env` file.

Never commit real pool usernames, payout addresses, worker names, passwords, or API keys unless a pool explicitly treats the value as a non-secret worker placeholder.

Set `HYBA_SECRET_MANAGER_URI` to the URI of your secret manager service so that the application can fetch pool credentials and JWT secrets from a secure store.

## 2. Required production flags

```bash
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_LIVE_SHARE_APPROVAL_ID='<approved-launch-ticket-or-change-id>'
export HYBA_ENABLE_MINING_AUTOCONNECT=true
export HYBA_ENABLE_AUDIT_LOGGING=true
```

Production mode intentionally blocks simulated jobs and fixture credentials. Enabling live Stratum and live share submission instructs the Stratum client to establish real network connections and submit accepted shares to pools. Audit logging should remain enabled for compliance and incident investigation.

## 3. Deterministic declared hashrate

Set the configured HYBA/PULVINI capacity estimate at or below the 1 EH/s governance cap:

```bash
export HYBA_QUANTUM_CAPACITY_EHS='1.0'
export HYBA_PULVINI_HASHRATE_CAP_EHS='1.0'
```

This is the deterministic capacity contract used by dashboards and orchestration. It should be treated as configured capacity, not pool-measured telemetry. Values above `1.0` EH/s must fail production validation and API request validation.

## 4. Configure pools

Supported pool IDs:

- `VIABTC`
- `NICEHASH`
- `BRAIINS`
- `CKPOOL`

Each enabled Stratum V2 pool uses this pattern:

```bash
export HYBA_POOL_<POOL_ID>_URL='stratum2+ssl://...'
export HYBA_POOL_<POOL_ID>_USERNAME='<secret-managed-user-or-wallet-worker>'
export HYBA_POOL_<POOL_ID>_PASSWORD='<secret-managed-password-or-worker-placeholder>'
export HYBA_POOL_<POOL_ID>_STRATUM_VERSION='2'
```

Primary launch profile:

```bash
export HYBA_POOL_VIABTC_URL='stratum2+ssl://btc.viabtc.com:443'
export HYBA_POOL_VIABTC_USERNAME='PYTHIA.001'
export HYBA_POOL_VIABTC_PASSWORD='123'
export HYBA_POOL_VIABTC_STRATUM_VERSION='2'
```

## 5. Pre-flight checks

Run the backend workflow tests:

```bash
python -m unittest tests.test_backend_workflows
```

Run the production operations and Stratum launch validation tests:

```bash
python -m unittest tests.test_production_operations
```

Run the Pulvini cap and nonce-compression property tests:

```bash
python -m pytest tests/test_pulvini_hashrate_cap_property.py tests/test_pulvini_nonce_compression.py tests/test_property_based_backend.py -q
```

Run the production math primitive tests:

```bash
python -m pytest tests/test_production_math_primitives.py
```

Run the Phi block analyser math tests:

```bash
python -m pytest tests/test_phi_block_analyser_math.py
```

Run the production environment validator against the exact deployment environment:

```bash
python scripts/validate_production_env.py
```

## 6. Operational expectations

Before live mining, confirm:

1. Pool credentials authenticate.
2. At least one pool reaches `AUTHENTICATED` or `SETUP_CONNECTION_SUCCESS_V2` state.
3. Simulated jobs are rejected in production.
4. Local share validation runs before accounting.
5. All-pools-offline state alerts and backs off instead of spinning.
6. Configured hashrate is shown as configured estimate, not measured telemetry.
7. Configured hashrate never exceeds the 1 EH/s Pulvini cap.

## 7. Day-one pool strategy

Suggested launch posture:

1. Start with ViaBTC as the primary production pool and all others configured as fallback.
2. Confirm successful Stratum V2 `SetupConnection` flow.
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

- credentials are secret-managed or deliberately approved as pool worker placeholders;
- production fixtures are blocked;
- live Stratum, live share submission, autoconnect, and audit logging are enabled;
- tests pass;
- the production environment validator passes;
- at least one real pool authenticates;
- local share validation is active;
- monitoring is live;
- the configured hashrate is capped at 1 EH/s.

If any of these fails, enter `REVIEW_REQUIRED` and do not run unattended.

## Autonomy Circuit-Breaker Reset Path

The autonomy circuit breaker gates only autonomous optimisation hooks and reflexive cycles. It must not gate exact SHA-256d local verification, verifier firewall checks, or live share submission paths. When the breaker is open, `UnifiedMiningEngine.search()` still proceeds to the nonce search after the autonomous-hook block.

Automatic reset:

- The breaker closes automatically after `HYBA_AUTONOMY_CIRCUIT_BREAKER_COOLDOWN_SECONDS` elapses.
- The default cooldown is 60 seconds and is parsed with the same safe numeric fallback used by the rest of `AutonomousConfig`.
- On the next `is_circuit_open()` check after cooldown expiry, the controller clears the open-until timestamp and resets consecutive failures.

Manual reset:

```bash
PYTHONPATH=python_backend python scripts/autonomous_mining_operator_control.py reset-circuit \
  --reason "operator reviewed hook failure and cleared remediation"
```

Manual reset clears the circuit-open timestamp and consecutive failure count and writes an operator audit entry. Use it only after confirming the failed autonomous hook is remediated; if the underlying failure persists, the breaker will reopen after the configured failure threshold.
