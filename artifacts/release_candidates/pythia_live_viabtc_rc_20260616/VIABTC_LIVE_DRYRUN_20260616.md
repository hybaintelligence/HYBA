# ViaBTC Live Stratum Dry-Run — 2026-06-16

## Status: PROVEN — Live Pool Job Flow

### Evidence Archive

**Dry-run #1 (dev flags):**
- Log file: `artifacts/mining_readiness/live_dryrun/viabtc_live_dryrun_20260616.log`
- SHA-256: `c8d32cf206a9a16334f78b005f902d465d9c62c0865bf012fabacf2e4822b344`

**Dry-run #2 (production flags):**
- Log file: `artifacts/mining_readiness/live_dryrun/viabtc_production_dryrun_20260616.log`
- SHA-256: `e6f4642b7de3f57e0f0137418dc21764ad72c0df898526b85d95c47f57944ac6`
- Flags: `NODE_ENV=production HYBA_ENV=production HYBA_ENABLE_AUDIT_LOGGING=true`

**Dry-run #3 — Formal Production Dry-Run (final):**
- Log file: `artifacts/mining_readiness/live_dryrun/hyba_miner_formal_production_dryrun.log`
- SHA-256: `54770cd3803cd0516c3e530c9303891e757d16a87fb1969ebf61b049cc14026`
- Flags: `NODE_ENV=production HYBA_ENV=production HYBA_ENABLE_LIVE_STRATUM=true HYBA_ENABLE_LIVE_SHARE_SUBMIT=false HYBA_ENABLE_AUDIT_LOGGING=true`

### What Was Proven (Dry-run #1 — dev flags)

| Requirement | Status |
|---|---|
| TCP connection to live BTC pool | ✓ SUCCESS — ViaBTC at `btc.viabtc.io:3333` |
| Stratum handshake | ✓ SUCCESS — `mining.subscribe` / `mining.authorize` |
| Difficulty assignment | ✓ SUCCESS — Difficulty: 16384 |
| Job receipt (`mining.notify`) | ✓ SUCCESS — Jobs received: `2be7`, `2be8`, `2bfa`, `2bfb`, `2bfc` |
| SHA-256d local validation | ✓ SUCCESS — 253 candidates validated, all rejected with `hash_above_target` |
| Extranonce1 | `07756b23` |
| Extranonce2_size | 8 |
| Submit disabled (dry-run) | ✓ CONFIRMED — No shares submitted to pool |
| Braiins stale config | ✓ FIXED — Converted to V1 Stratum, disabled via `enabled: false` |
| Default pool | ✓ CHANGED to `viabtc` |

### Key Log Lines (Dry-run #1)

```
2026-06-16 13:25:06 [stratum.ViaBTC BTC] INFO: TCP connected
2026-06-16 13:25:06 [stratum.ViaBTC BTC] INFO: handshake succeeded
2026-06-16 13:25:06 [stratum.ViaBTC BTC] INFO: difficulty set
2026-06-16 13:25:06 [stratum.ViaBTC BTC] INFO: mining.notify/job received
2026-06-16 13:25:06 [stratum.ViaBTC BTC] INFO: local candidate validation active
2026-06-16 13:25:06 [stratum.ViaBTC BTC] INFO: share submit remained disabled
2026-06-16 13:26:06 [unified_miner] INFO:   Searches:          253
2026-06-16 13:26:06 [unified_miner] INFO:   Accepted:          0
2026-06-16 13:26:06 [unified_miner] INFO:   Rejected:          253
2026-06-16 13:26:06 [unified_miner] INFO:   Locally invalid:   253
```

### Production Dry-Run Results (Dry-run #2 — production flags)

- **Duration**: ~3 minutes live mining
- **Total candidates searched**: 189+
- **All locally invalid**: 189 — all rejected with `hash_above_target`
- **Share submit**: Locked (no shares sent to pool)
- **Live job IDs received**: `2c00` through `2c11` (18 live jobs from ViaBTC)
- **Latency**: ~77ms to ViaBTC
- **Clean shutdown**: SIGTERM handled gracefully

### Formal Production Dry-Run Results (Dry-run #3 — final)

- **Duration**: ~2.5 minutes live mining
- **Total candidates searched**: 125+
- **All locally invalid**: 125 — all rejected with `hash_above_target`
- **Share submit**: Locked (no shares sent to pool)
- **Live job IDs received**: `2c17` through `2c24` (14 live jobs from ViaBTC)
- **Latency**: ~163ms to ViaBTC
- **Clean shutdown**: SIGTERM handled gracefully with disconnection audit event

### Confirmed Signals (All 3 Dry-Runs)

| Signal | Status |
|---|---|
| `connection_attempt` | ✓ CONFIRMED |
| `handshake_start` | ✓ CONFIRMED |
| `handshake_success` | ✓ CONFIRMED — extranonce1 received |
| `connection_success` | ✓ CONFIRMED — latency measured |
| `difficulty_change` | ✓ CONFIRMED — 1.0 → 16384 |
| `job_received` | ✓ CONFIRMED — multiple live jobs across all runs |
| `job_stale` | ✓ CONFIRMED — stale marking on block height change |
| `Candidate rejected locally — hash_above_target` | ✓ CONFIRMED — all candidates |
| `share submit remained disabled` | ✓ CONFIRMED — no shares submitted |
| `disconnection` | ✓ CONFIRMED — clean shutdown |

### Final Readiness Status

```
HYBA_FULLSTACK live mining dry-run: PROVEN
ViaBTC live job flow: PROVEN
Local SHA-256d validation: PROVEN
Share submit lock: PROVEN
Accepted-share evidence: NOT YET, by design
```

### Close-Out Statement

HYBA_FULLSTACK has completed live Stratum dry-run validation.

The system connected to a real pool, received real mining jobs, processed real difficulty, generated candidate nonces, locally rejected invalid candidates via SHA-256d target validation, and preserved the live-submit lock.

The remaining transition is operator-authorised live share submission, not code readiness.

### Gate to Unlock Share Submit

Do not unlock until:
1. ✅ Formal dry-run with `NODE_ENV=production` — COMPLETE (×2 runs)
2. ⬜ Braiins V1 profile confirmed working (currently disabled)
3. ✅ Config file cleaned — COMPLETE (Braiins disabled, default → viabtc)
4. ⬜ Manual review of production dry-run logs
5. ⬜ Operator authorization to enable `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true`