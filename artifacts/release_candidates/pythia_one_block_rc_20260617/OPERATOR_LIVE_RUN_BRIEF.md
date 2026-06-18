# HYBA_FULLSTACK — Operator Live Run Brief

**Status:** READY FOR OPERATOR-AUTHORISED LIVE RUN  
**Release candidate:** `pythia_one_block_rc_20260617`  
**Mission:** one pool-confirmed accepted block, then shutdown  
**Supreme invariant:** blockchain security above HYBA upside

---

## 1. What this system is

HYBA_FULLSTACK is the production operator shell for the PYTHIA/PULVINI mining substrate.

It connects:

```text
AIOptimizer
→ PulviniCompressedQuantumSolver
→ UnifiedMiningEngine.search(job)
→ local SHA-256d target validation
→ StratumClient.submit_validated_share()
→ pool ACK/reject
→ engine feedback / mission memory
```

The mathematical layer guides traversal. Bitcoin and the pool remain the proof boundary.

---

## 2. Live/prod invariants

The live miner is not allowed to be ambiguous.

```text
No live Stratum session → no job
No job → no search
No structured nonce → no submit
Local SHA-256d miss → no pool submit
Live submit disabled → explicit 423 guard
Pool ACK/reject → final external truth
```

Production/live mode never injects development fixture jobs.

Development fixtures are allowed only when all of the following are true:

```text
HYBA_ALLOW_DEV_FIXTURES=true
HYBA_ENV != production
NODE_ENV != production
HYBA_ENABLE_LIVE_STRATUM=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
```

If fixtures are present with production/live flags, execution fails closed.

---

## 3. Evidence packet

Release candidate directory:

```text
artifacts/release_candidates/pythia_one_block_rc_20260617/
```

Core evidence:

```text
MANIFEST.json
mining_production_readiness_live_20260616T183745Z.json
test_output.txt
```

Live dry-run evidence:

```text
artifacts/mining_readiness/live_dryrun/VIABTC_LIVE_DRYRUN_20260616.md
```

Validated signals across dry-runs:

```text
connection_attempt
handshake_start
handshake_success
connection_success
difficulty_change
job_received
job_stale
Candidate rejected locally — hash_above_target
share submit remained disabled
disconnection on SIGTERM
```

Fresh readiness state:

```text
mode: live
status: ready
passed: true
focused mining regressions: 21 passed, 0 skipped
production build: passed
configured pools: VIABTC, NICEHASH, BRAIINS, CKPOOL
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
HYBA_ENABLE_AUDIT_LOGGING=true
```

---

## 4. What to watch during live run

A healthy live run should emit the following sequence:

```text
Runtime mode: HYBA_ENV=production NODE_ENV=production live_stratum=True live_submit=True dev_fixtures_allowed=False
Loaded verified pool profile(s)
connection_success
handshake_success
difficulty_change
job_received
search_active_candidate_generated
local_validation_rejected_before_pool_submit
candidate_locally_valid_submitting_to_pool
pool_accepted_share OR pool_or_submit_guard_rejected_share
PYTHIA MISSION COMPLETE
```

If the system is not progressing, inspect:

```text
Last no-job reason
Last no-search reason
Last no-submit reason
```

These reason states are intentionally exposed. There should be no silent no-op path.

---

## 5. Launch command

Load production credentials first, then:

```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

export PYTHONPATH=python_backend
python python_backend/run_unified_miner.py
```

Required live env state:

```text
NODE_ENV=production
HYBA_ENV=production
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
HYBA_ENABLE_AUDIT_LOGGING=true
HYBA_LIVE_SHARE_APPROVAL_ID=<operator approval id>
HYBA_POOL_CONFIG_PATH=config/mining_pools_live.json
```

---

## 6. Shutdown condition

Mission memory is seeded for:

```text
one pool-confirmed accepted block, then shutdown
```

Accepted shares/blocks are mission memory events. The miner shuts down only after pool-confirmed mission completion, not after local candidate generation.

---

## 7. Claim boundary

HYBA does not claim to change Bitcoin consensus and does not bypass SHA-256d.

HYBA changes the intelligence of traversal before the proof boundary. The system uses substrate-independent tensor/PULVINI/Φ mathematics to propose candidates, then validates through the standard Bitcoin and pool acceptance path.

Record line:

```text
HYBA_FULLSTACK is live-ready because the production miner consumes structured search, refuses fixture-backed live execution, validates locally before submission, records explicit reasons for every blocked state, and leaves final truth to pool ACK/reject.
```
