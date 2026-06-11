# Live Stratum Rollout Runbook

This runbook documents the production-readiness step from deterministic pool configuration to live Stratum v1 connectivity.

## Added modules

- `python_backend/pythia_mining/stratum_protocol.py`
- `python_backend/pythia_mining/pool_profiles.py`
- `python_backend/pythia_mining/stratum_transport.py`
- `python_backend/pythia_mining/live_stratum_session.py`
- `python_backend/pythia_mining/pulvini_overlay.py`

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
6. `PulviniOverlayConcentrator` presents one upstream worker identity while coordinating 32 internal PULVINI nodes.

## Pool-facing identity versus internal topology

The pool sees exactly one worker/session. Internally HYBA uses a 32-node PULVINI dodecahedron/icosahedron overlay:

- nodes `0-19`: dodecahedron worker nodes;
- nodes `20-31`: icosahedron hub nodes;
- graph diameter: 4 hops;
- every node has symmetric neighbour visibility;
- every node receives a deterministic, non-overlapping nonce slice;
- every node receives a deterministic `extranonce2` value for share submission;
- shares are submitted upstream through the concentrator, not directly as 32 pool workers.

This preserves the production invariant: **one pool-visible worker, 32 internally coordinated workers.**

## Job-arrival sequence

When the operator explicitly connects mining and the pool sends a job, the required sequence is:

1. `connect_requested` — operator/MIDAS requested pool connection.
2. `pool_bound` — one pool profile is selected and bound as the active upstream.
3. `subscribed_authorized` — Stratum subscribe/authorize completes.
4. `awaiting_job` — runtime waits for a real `mining.notify`.
5. `job_received` — `mining.notify` is parsed into a `MiningJob`.
6. `work_configured` — PULVINI assigns 32 nonce/extranonce2 lanes.
7. `candidate_evaluated` — a node reports a candidate nonce.
8. `share_submitted` — the concentrator submits the share as the single pool worker.
9. `share_outcome_recorded` — accepted/rejected outcome is recorded against the node, pool, and job.

The runtime status exposes this under `pulvini_overlay.lifecycle`, `pulvini_overlay.nodes`, `pulvini_overlay.assignments`, and `pulvini_overlay.share_ledger`.

## Internal knowledge sharing

Each node can inspect `node_knows(node_id)` from the overlay. That snapshot includes:

- the node's own phase/progress/share counters;
- its current assignment;
- direct neighbour states from the verified geometric graph;
- best-neighbour routing based on observed link latency;
- active job id;
- shared global mining state.

The implementation names this the PULVINI overlay/knowledge mesh. It is the runtime communication contract for the internal 32-node system.

## Tests

Run:

```bash
python -m unittest tests.test_stratum_protocol_primitives
python -m unittest tests.test_pool_profile_primitives
python -m unittest tests.test_live_stratum_session
python -m unittest tests.test_backend_workflows
python -m unittest tests.test_pulvini_overlay
```

## Rollout strategy

Do not immediately replace the existing `PoolManager` handshake. Instead:

1. Run the new protocol/profile/session/overlay tests in CI.
2. Configure a single low-risk pool profile through secret-managed env vars.
3. Run a controlled live subscribe/authorize smoke check.
4. Confirm no credentials are logged.
5. Confirm `mining.notify` and `mining.set_difficulty` events parse correctly.
6. Confirm one pool-visible worker and 32 internal PULVINI assignments in runtime status.
7. Confirm every PULVINI node has a unique nonce range and `extranonce2`.
8. Add share submission behind an explicit launch flag.
9. Only then route `PoolManager.connect()` through `LiveStratumSession` with live share submission enabled.

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
- Do not expose 32 separate worker identities to the pool unless a deliberate future architecture change is approved.
