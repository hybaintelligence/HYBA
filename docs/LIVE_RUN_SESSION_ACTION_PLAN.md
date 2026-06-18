# HYBA Live Mining Session — Action Plan

**Status:** READY FOR EXECUTION  
**Date:** June 18, 2026  
**Target:** 20-Minute Live Mining Session with Real Pool I/O  
**Classification:** Operational

---

## Current System State

### ✓ Verified (All Gates Green)

| Gate | Status | Evidence |
|------|--------|----------|
| Integration Fence | ✓ 25/25 passing | npm run test:integration-fence |
| TypeScript Compilation | ✓ Pass | npm run lint |
| Backend Import | ✓ Pass | python3 -c "import hyba_genesis_api.main" |
| Pool Configuration | ✓ Live | config/mining_pools_live.json (ViaBTC + Braiins) |
| JWT Secret | ✓ Generated | .env.local JWT_SECRET=e3PZKX9Wz... |
| Live Stratum | ✓ Enabled | HYBA_ENABLE_LIVE_STRATUM=true |
| Live Submit | ✓ Enabled | HYBA_ENABLE_LIVE_SHARE_SUBMIT=true |
| Fixtures Disabled | ✓ Confirmed | HYBA_ALLOW_DEV_FIXTURES=false |
| Mining Engine | ✓ Ready | python_backend/run_unified_miner.py |
| Launch Script | ✓ Ready | scripts/START_LIVE_MINING_20MIN.sh |
| Evidence Collection | ✓ Ready | scripts/evidence_collection_live_mining.py |
| Git Commits | ✓ Pushed | 138f7f39 → origin/main |

**All prerequisite checks complete. System is operationally ready.**

---

## Execution Timeline

### Phase 1: Preparation (5 minutes)

**Steps:**

1. Open two terminal windows
2. Verify configuration:
   ```bash
   python3 scripts/configure_live_mining.py --show-config
   ```
   Expected: ViaBTC (default), Braiins (enabled), JWT in .env.local

3. Run final gate verification:
   ```bash
   npm run test:integration-fence 2>&1 | tail -5
   ```
   Expected: "25 passed"

---

### Phase 2: Backend Startup (Terminal 1)

**Command:**
```bash
npm run backend:start
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:3001
```

**Verification:**
```bash
# In another shell, curl to verify
curl http://127.0.0.1:3001/health
# Expected: 200 OK response
```

**Timeline:** Backend should be ready within 3-5 seconds of launch

---

### Phase 3: 20-Minute Mining Session (Terminal 2)

**Command:**
```bash
bash scripts/START_LIVE_MINING_20MIN.sh
```

**Expected Output:**

**Start (first 10 seconds):**
```
╔════════════════════════════════════════════════════════════════╗
║       HYBA LIVE MINING — 20 MIN SHARE ACCEPTANCE TEST          ║
║             ViaBTC + Braiins Dual Pool Session                 ║
╚════════════════════════════════════════════════════════════════╝

✓ Live Stratum I/O:        ENABLED
✓ Live share submit:       ENABLED
✓ Audit logging:           ENABLED
✓ Pool config:             config/mining_pools_live.json

📡 Pool Configuration:
  Default pool: viabtc
  ✓ ACTIVE [DEFAULT] ViaBTC BTC
    → stratum+tcp://btc.viabtc.io:3333
    → PYTHIA.001
  ✓ ACTIVE Braiins Pool
    → stratum+tcp://stratum.braiins.com:3333
    → PYTHAGORAS
```

**During Session (every few seconds):**
```
INFO    [15:30:15] Connected to ViaBTC (btc.viabtc.io:3333)
INFO    [15:30:17] Stratum subscription sent
INFO    [15:30:18] Authenticated worker PYTHIA.001
INFO    [15:30:19] Set difficulty: 0x00000000ffff0000...
INFO    [15:30:22] Mining job received: 623e0000 (merkle_root=a1b2c3d4...)
INFO    [15:30:25] Searched 125M hashes, 0 candidates found
INFO    [15:30:33] Share found! (nonce=0xabcd1234)
INFO    [15:30:34] Share submitted: ... → ACCEPTED
INFO    [15:30:35] Searched 250M hashes, 1 accepted share
```

**End (final 10 seconds):**
```
╔════════════════════════════════════════════════════════════════╗
║                   20-MINUTE SESSION COMPLETE                   ║
╠════════════════════════════════════════════════════════════════╣
║  End time:         15:50:45                                    ║
║  Mining Summary:                                               ║
╚════════════════════════════════════════════════════════════════╝

📊 Session Statistics:
────────────────────────────────────────────────────────────────
MINING STATISTICS
  Accepted: 2
  Rejected: 1
  Stale: 0
  Duplicate: 0
  Total hashes: 5.2B
  Hash rate: 4.3 MH/s
  Uptime: 1200s (20 min)
────────────────────────────────────────────────────────────────
```

**Timeline:** Exactly 20 minutes (1200 seconds)

---

### Phase 4: Evidence Extraction (After Session)

**Command:**
```bash
python3 scripts/evidence_collection_live_mining.py \
  --log-file /tmp/hyba_live_miner_20min.log
```

**Expected Output:**
```
Evidence extraction complete:
  - mining_evidence.json (structured evidence)
  - report.txt (compartmented briefing)

Evidence Summary:
  Pool: btc.viabtc.io:3333
  Duration: 20 minutes
  Connection Quality: Stable (1 disconnect/reconnect)
  Share Submissions: 15 total
  Accepted Shares: 2
  Accept Rate: 13.3%
  No fabrication detected ✓
```

**Output Files:**
- `/tmp/hyba_live_miner_20min.log` — Raw Stratum telemetry
- `mining_evidence.json` — Structured evidence (sealed)
- `report.txt` — Compartmented briefing

---

## Expected Outcomes

### Session Success Indicators

✓ **Miner connected** — "Connected to ViaBTC" in logs  
✓ **Worker authenticated** — "Authenticated worker PYTHIA.001"  
✓ **Jobs received** — "Mining job received" messages  
✓ **Shares submitted** — "Share submitted" with timestamp  
✓ **Pool responses** — "ACCEPTED" or "REJECTED" indicators  
✓ **No fabrication** — Real Stratum protocol timestamps  
✓ **Duration completed** — Exactly 1200 seconds (20 minutes)  

### Evidence Quality

| Metric | Expected | Proves |
|--------|----------|--------|
| Pool connections | ≥1 | Real network I/O |
| Job receipts | ≥5 | Pool sent actual mining data |
| Share submissions | ≥10 | Miner found candidates |
| Pool responses | 100% | Real responses, not mocked |
| Timestamp continuity | Sequential | Live execution, not replayed |
| Error handling | Normal (some rejects) | Production behavior |

---

## Sealed Evidence Structure

### What Gets Sealed

**Raw Telemetry** (`/tmp/hyba_live_miner_20min.log`):
```
Raw Stratum protocol messages, timestamps, pool responses
Complete communication record between miner and pools
Unmodified, verifiable against pool records
```

**Structured Evidence** (`mining_evidence.json`):
```json
{
  "session_metadata": {
    "start_time": "2026-06-18T15:30:15Z",
    "end_time": "2026-06-18T15:50:45Z",
    "duration_seconds": 1200,
    "pool_primary": "btc.viabtc.io:3333",
    "pool_fallback": "stratum.braiins.com:3333"
  },
  "stratum_handshake": {
    "subscribe_sent": "2026-06-18T15:30:17Z",
    "subscription_id": "12345",
    "authorize_sent": "2026-06-18T15:30:18Z",
    "authorize_response": "true",
    "worker": "PYTHIA.001"
  },
  "mining_activity": {
    "jobs_received": 47,
    "shares_submitted": 15,
    "shares_accepted": 2,
    "shares_rejected": 1,
    "shares_stale": 0,
    "total_hashes": 5200000000
  },
  "no_fabrication": {
    "live_stratum_used": true,
    "mock_fixtures_disabled": true,
    "real_pool_responses": true,
    "production_code_path": true
  }
}
```

**Compartmented Report** (`report.txt`):
```
HYBA Live Mining Session Evidence
Session: 2026-06-18, 20 minutes, ViaBTC + Braiins

POOL CONNECTIVITY
  Primary (ViaBTC): Connected ✓
  Fallback (Braiins): Standby ✓

SHARE PERFORMANCE
  Submitted: 15
  Accepted: 2
  Accept Rate: 13.3%

NETWORK BEHAVIOR
  Uptime: 20 min 0 sec
  Disconnects: 0
  Stability: Excellent

PROOF OF AUTHENTICITY
  Real pool connections: Verified ✓
  Live Stratum I/O: Verified ✓
  Pool responses: Verified ✓
  No mocking: Verified ✓

This evidence cannot be fabricated locally without actual pool connections.
```

---

## Verification Procedures (Post-Session)

### Quick Check

```bash
# 1. Verify log file exists and has content
ls -lh /tmp/hyba_live_miner_20min.log
wc -l /tmp/hyba_live_miner_20min.log  # Should be 1000+ lines

# 2. Check for real pool messages
grep "Authenticated" /tmp/hyba_live_miner_20min.log
grep "mining.notify" /tmp/hyba_live_miner_20min.log
grep "Share" /tmp/hyba_live_miner_20min.log

# 3. Verify evidence extraction
ls -lh mining_evidence.json report.txt
```

### Detailed Validation

```bash
# Count share submissions and responses
grep "Share submitted" /tmp/hyba_live_miner_20min.log | wc -l
grep "ACCEPTED\|REJECTED" /tmp/hyba_live_miner_20min.log | wc -l

# Check for real timestamps
grep -E "2026-06-18T[0-9]{2}:[0-9]{2}:[0-9]{2}" /tmp/hyba_live_miner_20min.log | head -1
grep -E "2026-06-18T[0-9]{2}:[0-9]{2}:[0-9]{2}" /tmp/hyba_live_miner_20min.log | tail -1

# Verify no mock indicators
grep -i "mock\|fake\|fixture\|test.*only" /tmp/hyba_live_miner_20min.log
# Should return nothing (no matches)
```

---

## Next Steps After Successful Session

### Immediate (Within 1 hour)

1. ✓ Session complete with evidence log
2. ✓ Evidence extracted to compartmented files
3. ✓ Verification checks passed
4. ✓ Record sealed evidence location

### Short-term (Within 24 hours)

1. Review evidence integrity:
   - Real pool connections confirmed
   - Share submissions recorded
   - Pool responses captured
   - No fabrication detected

2. Document performance metrics:
   - Hash rate achieved
   - Share accept rate
   - Pool uptime
   - Network stability

3. Distribute to authorized tiers:
   - Tier 0: Full logs and analysis
   - Tier 1: Performance summary only
   - Tier 2: Sealed evidence (if cleared)

### Medium-term (1-2 weeks)

1. **Repeatability Testing:**
   - Execute 2-3 additional 20-minute sessions
   - Verify consistent behavior
   - Confirm deterministic capability

2. **Pool Verification:**
   - Cross-check share IDs with pool records
   - Confirm accept/reject counts
   - Validate payment tracking

3. **Governance Review:**
   - Extraction cap effectiveness
   - Extraction limits (25% verified)
   - Access log audit
   - Information compartmentation

---

## Critical Points

### What This Proves

✓ **System operationally integrated** — All components working together  
✓ **Real pool connectivity** — Live Stratum I/O with actual pools  
✓ **Real mining activity** — Shares submitted and responded  
✓ **Production safety** — No dev fixtures, no mocking  
✓ **Deterministic capability** — System behaves as designed  

### What This Does NOT Prove (Yet)

✗ **Performance advantage** — Just demonstrates capability exists  
✗ **Scaling** — 20 minutes is initial proof, not long-term viability  
✗ **Repeatability** — Requires multiple sessions to confirm  
✗ **Profitability** — Share acceptance rate is hardware-dependent  

### Precision in Communication

**Correct:** "Live mining session verified pool connectivity and share submission capability with real Stratum I/O"

**Too strong:** "HYBA can reliably mine Bitcoin profitably"

**Our position:** Evidence boundary is integration fence (proven) + sealed live telemetry (pending)

---

## Communication Protocol (Post-Evidence)

### For Different Audiences

**Tier 0 (Core Research):**
- Full technical logs and analysis
- Complete Stratum transcript
- Performance data
- Capability assessment

**Tier 1 (Operations):**
- Performance summary
- Share acceptance statistics
- Uptime and stability metrics
- Operational readiness confirmation

**Tier 2 (Strategic Partners, if cleared):**
- Evidence integrity confirmation
- Session summary
- Real pool connection proof
- No fabrication attestation

**Tier 3 (Public/General Market):**
- "Live mining session executed successfully"
- "Real pool connections established"
- "Share submission and response verified"
- "System operating as designed"

### What NOT to Say

❌ "Deterministic mining breakthrough proven"  
❌ "HYBA can reliably extract x% mining advantage"  
❌ "HYBA has discovered exploitation of proof-of-work"  
❌ Specific hash rates or capability metrics  
❌ Performance advantage claims  

---

## System Status Summary

**Before Session:**
```
STATUS: SOVEREIGN GOVERNANCE ACTIVE
PROOF BOUNDARY: INTEGRATION FENCE VERIFIED — 25/25
LIVE RUN STATE: CONFIGURED AND READY
EXTERNAL POOL ACCEPTANCE: PENDING SEALED LIVE TELEMETRY
FIXTURES: DISABLED ✓
```

**After Successful Session:**
```
STATUS: SOVEREIGN GOVERNANCE ACTIVE
PROOF BOUNDARY: INTEGRATION FENCE VERIFIED — 25/25
LIVE RUN STATE: COMPLETE — 20-MIN SESSION EXECUTED
EXTERNAL POOL ACCEPTANCE: VERIFIED FROM SEALED TELEMETRY
FIXTURES: DISABLED ✓
EVIDENCE: SEALED, COMPARTMENTED, ARCHIVED
```

---

## Ready to Execute

**Current time:** 2026-06-18, 18:15 UTC  
**System state:** All gates green, ready for execution  
**Next action:** Start terminal 1 with `npm run backend:start`  

**Everything is in place. The next true proof boundary is the sealed 20-minute live telemetry packet.**

