# Live Stratum Rollout Runbook

This runbook documents the production-readiness step from deterministic pool configuration to live Stratum v1 connectivity.

## Added modules

- `python_backend/pythia_mining/stratum_protocol.py`
- `python_backend/pythia_mining/pool_profiles.py`
- `python_backend/pythia_mining/stratum_transport.py`
- `python_backend/pythia_mining/live_stratum_session.py`

## What is now production-ready

1. Stratum v1 JSON-RPC messages can be built deterministically:
   - `mining.subscribe`
   - `mining.authorize`
   - `mining.submit`
2. Pool server messages can be parsed and validated:
   - subscribe responses;
   - authorize responses;
   - `mining.notify`;
   - `mining.set_difficulty`.
3. Pool profiles validate URL scheme, host, port, credentials, Stratum version, TLS requirement, and priority.
4. Async line transport supports TCP/TLS connect, send, receive, timeout, and close.
5. `LiveStratumSession` composes profile + protocol + transport into an opt-in live subscribe/authorize session.

## Tests

Run:

```bash
python -m unittest tests.test_stratum_protocol_primitives
python -m unittest tests.test_pool_profile_primitives
python -m unittest tests.test_live_stratum_session
python -m unittest tests.test_backend_workflows
```

## Rollout strategy

Do not immediately replace the existing `PoolManager` handshake. Instead:

1. Run the new protocol/profile/session tests in CI.
2. Configure a single low-risk pool profile through secret-managed env vars.
3. Run a controlled live subscribe/authorize smoke check.
4. Confirm no credentials are logged.
5. Confirm `mining.notify` and `mining.set_difficulty` events parse correctly.
6. Add share submission behind an explicit launch flag.
7. Only then route `PoolManager.connect()` through `LiveStratumSession`.

## Launch flags

Recommended explicit feature flags:

```bash
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
```

Start with live subscribe/authorize and notify parsing only. Enable live share submit only after local validation and pool test account checks pass.

## Operational guardrails

- Never commit real pool credentials.
- Never log passwords or full authorization payloads.
- Treat failed subscribe/authorize as degraded state.
- Treat malformed `mining.notify` as rejected pool message.
- Keep deterministic fixture handshake available only for tests and development.
- Do not enable live share submission until controlled test-pool verification succeeds.
