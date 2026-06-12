# HYBA_FULLSTACK Five-Minute Mining Session Analysis — 2026-06-12

Status: evidence review
Owner: HYBA Group / Company
Scope: HYBA_FULLSTACK command-room mining artefacts committed under `HYBA_FULLSTACK_COMMAND_ROOM_20260612/`

## Decision

The committed command-room artefacts support the following conclusion:

```text
HYBA_FULLSTACK successfully executed a controlled live-Stratum connection rehearsal against the Braiins profile for approximately five minutes, with production bridge/backend readiness intact, MIDAS state transitions valid, no invalid transitions recorded, and no share/revenue claim emitted.
```

The artefacts do **not** yet support an accepted-share, stable-hashrate, revenue, payroll, or office-cost reliance claim.

## Evidence reviewed

- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/bridge_health.txt`
- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/backend_readiness.txt`
- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/audit_log_tail.txt`
- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/mining_status_before_start.json`
- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/mining_status_after_start.json`
- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/pools_status.json`
- `HYBA_FULLSTACK_COMMAND_ROOM_20260612/treasury_boundary_note.md`
- `start_mining_session.py` as the session capture procedure in force for the original artefacts

## What the evidence proves

### 1. Production bridge was live

`bridge_health.txt` records the HYBA Secure Bridge as `status=ok`, version `2.1.0`, and `backendReachable=true`.

### 2. Backend substrate was ready

`backend_readiness.txt` records backend `status=ready`, with the substrate marked ready and five subsystem initialisation records:

- `pulvini_reconstruction_kernel`
- `hilbert_space_warm_start`
- `phi_floor_coherence`
- `pythia_consensus_monitors`
- `mining_engine_optimization_sync`

The same readiness payload records `pythia.available=false`, so the conclusion is backend/substrate readiness, not full Pythia runtime availability.

### 3. Runtime was production mode with autoconnect disabled

`audit_log_tail.txt` records the bridge in production mode and autoconnect disabled. This supports the boundary that mining required explicit MIDAS/operator connection rather than silent startup.

### 4. Braiins live-Stratum profile was active for the five-minute window

Both `mining_status_before_start.json` and `mining_status_after_start.json` record:

- `active=true`
- `daemon_running=true`
- `pool_id=braiins`
- `stratum_version=2`
- `hashrate_ehs=0.1`
- `capacity_source=configured_capped`
- `system_health=HEALTHY`
- `telemetry_source=live_api`
- connection timestamp `2026-06-12T20:55:19.004074`

The first status timestamp is `2026-06-12T20:55:36.177972`; the second is `2026-06-12T21:00:36.948231`, giving an observed evidence window of approximately five minutes.

### 5. MIDAS state machine behaved correctly

The status snapshots record:

- current MIDAS state: `running`
- canonical path: `idle -> starting -> running -> stopping -> stopped`
- transition count: `2`
- invalid transitions: `0`
- completed requests: `2`

This proves controlled start transition integrity for the captured window.

### 6. Pool summary matches single active pool posture

`pools_status.json` records five pool profiles and exactly one active pool: Braiins. It also records configured CKPool and NiceHash profiles as disconnected, ViaBTC and generic StratumV2 as not configured, and global acceptance rate `0.0`.

## What the evidence does not prove

The evidence does **not** prove:

- accepted shares;
- pool-side accepted-share confirmation;
- revenue generation;
- stable sustained hashrate beyond the captured window;
- profitability;
- payroll or office-cost coverage;
- safe autoconnect;
- readiness for unattended live-share submission.

The share counters remained:

```json
{"submitted": 0, "accepted": 0, "rejected": 0}
```

That is good for treasury discipline, but it means no revenue claim may be made from this session.

## Evidence inconsistency

The file named `mining_status_before_start.json` is not a true inactive pre-start snapshot. It records `active=true`, `daemon_running=true`, and `midas.state=running`. It should be treated as an early-in-session snapshot, not as proof of inactive pre-connect state.

The original `start_mining_session.py` captured this file after pool configuration and before its explicit connect call, but the committed contents show an already-active state. This could mean:

1. mining was already connected before the script captured the file;
2. a prior command-room action had already connected the Braiins profile;
3. the endpoint state persisted from an earlier connection;
4. the capture procedure was run after an already-started session.

The conclusion is not that the session is invalid. The conclusion is that the evidence label was inaccurate.

## Security finding

The original `start_mining_session.py` embedded operator and pool credentials. That is not acceptable for a production command-room helper.

A hardened replacement has now been committed. The new runner:

- requires operator and pool credentials from environment variables;
- captures true pre-config status;
- captures post-config, post-connect, per-minute, final, and post-disconnect snapshots;
- redacts obvious secret-bearing fields;
- preserves share counters separately from connection evidence.

## Readiness impact

This session upgrades HYBA_FULLSTACK from `controlled production startup readiness` to:

```text
controlled live-Stratum connection rehearsal completed
```

It does not upgrade the system to:

```text
accepted-share revenue ready
```

## Required next evidence capture

Run the hardened session helper with production secrets injected externally:

```bash
set HYBA_OPERATOR_USERNAME=<operator>
set HYBA_OPERATOR_PASSWORD=<secret>
set HYBA_POOL_ID=braiins
set HYBA_POOL_URL=<pool-url>
set HYBA_POOL_USERNAME=<worker>
set HYBA_POOL_PASSWORD=<secret>
set HYBA_SESSION_MINUTES=5
python start_mining_session.py
```

Expected new evidence files:

- `bridge_health_pre_session.json`
- `backend_readiness_pre_session.json`
- `operator_login_summary.json`
- `mining_status_00_pre_config.json`
- `pool_config_response.json`
- `mining_status_01_post_config_pre_connect.json`
- `pool_connect_response.json`
- `mining_status_02_post_connect.json`
- `mining_status_minute_01.json` through `mining_status_minute_05.json`
- `mining_session_minute_summary.json`
- `mining_status_03_final_before_disconnect.json`
- `pools_status.json`
- `pool_disconnect_response.json`
- `mining_status_04_post_disconnect.json`

## Go-forward decision

Approved:

- continue command-room live-Stratum rehearsals;
- capture cleaner pre/post session artefacts;
- prepare signed live-share approval packet;
- obtain pool-dashboard screenshots/exports.

Not approved yet:

- revenue reliance;
- accepted-share claims;
- stable-hashrate claims;
- payroll reliance;
- office-cost reliance;
- unattended autoconnect;
- live-share submission without signed legal/treasury/security/operator approval.

## Final status label

```text
HYBA_FULLSTACK completed a controlled five-minute live-Stratum connection rehearsal. The system maintained production bridge/backend readiness, valid MIDAS transitions, and zero invalid state transitions. Share counters remained zero, so the session is connection-readiness evidence, not revenue evidence.
```
