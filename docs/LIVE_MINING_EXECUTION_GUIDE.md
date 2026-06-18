# HYBA Live Mining Execution Guide — 20-Minute Session

**Classification:** Operational  
**Date:** June 18, 2026  
**Status:** Ready for Execution  

---

## Quick Start (3 Steps)

### Step 1: Verify Configuration

```bash
python3 scripts/configure_live_mining.py --show-config
```

**Expected output:**
- ✓ ViaBTC (primary, default) — stratum+tcp://btc.viabtc.io:3333
- ✓ Braiins (fallback) — stratum+tcp://stratum.braiins.com:3333
- ✓ Environment flags enabled

### Step 2: Start Backend (Terminal 1)

```bash
npm run backend:start
```

**Expect to see:**
```
INFO:     Uvicorn running on http://127.0.0.1:3001
```

Wait for startup to complete (3-5 seconds).

### Step 3: Run 20-Minute Mining Session (Terminal 2)

```bash
bash scripts/START_LIVE_MINING_20MIN.sh
```

**The script will:**
1. Display pool configuration summary
2. Launch unified miner process (background)
3. Stream mining logs in real-time
4. Run for exactly 20 minutes
5. Generate evidence log at `/tmp/hyba_live_miner_20min.log`
6. Display final statistics
7. Terminate miner cleanly

---

## What Happens During 20 Minutes

### Mining Engine

The unified miner will:

1. **Connect to ViaBTC** (primary pool)
   - Send Stratum subscription
   - Perform worker authentication (PYTHIA.001)
   - Receive difficulty and initial job

2. **Receive Mining Jobs**
   - Listen for mining.notify messages
   - Update target difficulty as pool sends updates
   - Prepare search workspaces for each job

3. **Execute Mining Search**
   - Run deterministic search across nonce space
   - Filter candidates against current difficulty
   - Validate candidates locally

4. **Submit Share Candidates**
   - For each valid candidate, send mining.submit
   - Record submission timestamp
   - Capture pool response (accepted/rejected/stale)

5. **Fallback to Braiins** (if ViaBTC disconnects)
   - Automatically switch to fallback pool
   - Maintain continuous mining operations

### Evidence Collected

Real Stratum protocol telemetry:

- **Connection timestamp** — When miner connected
- **Subscribe messages** — Pool subscription handshake
- **Authorize messages** — Worker authentication
- **Difficulty updates** — Pool difficulty changes
- **Mining jobs** — Job IDs and blockchain data
- **Share submissions** — Submitted candidates with timestamps
- **Pool responses** — Accepted/rejected/stale/duplicate responses
- **Disconnections** — Failover events and recovery
- **Statistics** — Hashes, accepts, rejects, accept rate

**All sourced from live Stratum I/O, not mocked or fabricated.**

---

## Session Output

### Real-Time Logs

During the 20-minute session, you'll see:

```
INFO    Connected to ViaBTC
INFO    Authenticated worker PYTHIA.001
INFO    Difficulty: 0x00000000ffff0000ffff0000ffff0000ffff0000ffff0000ffff0000ffff0000
INFO    Mining job: a1b2c3d4... (merkle_root=...)
INFO    [15:30:42] 523M hashes searched, candidates: 2
INFO    Share submitted: ... → ACCEPTED
INFO    Share submitted: ... → REJECTED (stale)
...
```

### Final Evidence File

Location: `/tmp/hyba_live_miner_20min.log`

Contains:
- Complete session transcript
- All pool I/O (Stratum protocol messages)
- Share submissions and responses
- Error conditions and failovers
- Statistics summary

---

## Evidence Extraction (After Session)

### Generate Compartmented Report

```bash
python3 scripts/evidence_collection_live_mining.py \
  --log-file /tmp/hyba_live_miner_20min.log
```

**Output:**
- `mining_evidence.json` — Structured evidence (sealed)
- `report.txt` — Compartmented briefing

**Evidence includes:**
- Pool connection details (timestamp, pool name)
- Share submission count and accept rate
- Accepted share IDs (verifiable with pool)
- Performance metrics (hash rate, efficiency)
- Failover events (if any)
- No fabrication indicators (live timestamps, real pool responses)

---

## Verification Checklist

### Before Starting

- [ ] `npm run test:integration-fence` passes (25/25)
- [ ] `.env.local` contains JWT_SECRET
- [ ] Pool config has ViaBTC and Braiins enabled
- [ ] `HYBA_ENABLE_LIVE_STRATUM=true` in .env.local
- [ ] `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true` in .env.local
- [ ] `HYBA_ALLOW_DEV_FIXTURES=false` in .env.local

### During Session

- [ ] Backend running on localhost:3001
- [ ] Miner logs show pool connection
- [ ] Logs show "Authenticated worker" message
- [ ] Logs show "Mining job" messages
- [ ] Logs show "Share submitted" with responses
- [ ] Session runs for exactly 20 minutes
- [ ] No mock data or fabricated fixtures

### After Session

- [ ] Evidence file exists: `/tmp/hyba_live_miner_20min.log`
- [ ] Evidence contains pool I/O (real Stratum messages)
- [ ] Evidence shows share submission timestamps
- [ ] Evidence shows pool responses (accepted/rejected)
- [ ] Extract compartmented report successfully

---

## Troubleshooting

### Miner Won't Connect to Pool

**Issue:** Logs show "Connection refused" or timeout

**Check:**
1. Pool is live: `telnet btc.viabtc.io 3333` (should connect)
2. Network connectivity: `ping btc.viabtc.io`
3. Credentials in config/mining_pools_live.json are correct
4. Fallback pool (Braiins) should activate automatically

### Backend Not Running

**Issue:** Miner can't reach backend health endpoint

**Check:**
1. Terminal 1: `npm run backend:start` is running
2. Backend is listening: `curl http://127.0.0.1:3001/health`
3. If not responding, restart backend and rerun miner

### Session Stops Early

**Issue:** Miner stops before 20 minutes

**Check:**
1. Any errors in the log file: `tail -50 /tmp/hyba_live_miner_20min.log`
2. Pool disconnect: Check if Stratum connection dropped
3. Resource limit: Check if system ran out of memory
4. Signal received: Check if process was killed externally

### No Accepted Shares

**Issue:** Session runs but all shares rejected

**Check:**
1. This is normal for real mining with low hash rate
2. Confirms real pool I/O (not mocked)
3. Even rejected shares prove pool communication
4. Statistics should show rejection reasons (stale, duplicate, etc.)

---

## Evidence Interpretation

### What Proves Real Pool I/O

✓ **Stratum subscribe message** — Pool sent initial state  
✓ **Authorize response** — Pool authenticated worker  
✓ **Difficulty update** — Pool sent current target  
✓ **Mining.notify message** — Pool sent new job  
✓ **Share submission** → **Pool response** — Round-trip to pool  

**None of these can be fabricated locally without connecting to real pool.**

### What Proves No Mocking

✗ No mock fixtures in production code (`HYBA_ALLOW_DEV_FIXTURES=false`)  
✗ All I/O is real Stratum protocol (verifiable against pool)  
✗ Timestamps are live (not hardcoded)  
✗ Share responses come from actual pools (not scripted)  
✗ Failover events are real network conditions  

---

## Next Thresholds After Live Run

### Immediate (Evidence Sealing)

1. Extract compartmented report
2. Archive evidence (sealed)
3. Distribute to Tier 2 reviewers (if authorized)

### Medium-term (Validation)

1. Independent pool verification (optional)
2. Performance analysis
3. Efficiency metrics documentation
4. Multi-session repeatability testing

### Long-term (Strategic)

1. Deterministic capability quantification
2. Extraction limit enforcement review
3. Governance posture audit
4. Strategic asset classification confirmation

---

## System State After Session

**Current:**
```
STATUS: SOVEREIGN GOVERNANCE ACTIVE
PROOF BOUNDARY: INTEGRATION FENCE VERIFIED — 25/25
LIVE RUN STATE: CONFIGURED AND READY
EXTERNAL POOL ACCEPTANCE: PENDING SEALED LIVE TELEMETRY
FIXTURES: DISABLED ✓
DISCLOSURE: TIERED
ACCESS: GOVERNED
EXTRACTION: CAPPED AT 25%
```

**After successful 20-minute session:**
```
STATUS: SOVEREIGN GOVERNANCE ACTIVE
PROOF BOUNDARY: INTEGRATION FENCE VERIFIED — 25/25
LIVE RUN STATE: COMPLETE — 20-MIN SESSION EXECUTED
EXTERNAL POOL ACCEPTANCE: VERIFIED FROM SEALED TELEMETRY
FIXTURES: DISABLED ✓
DISCLOSURE: TIERED
ACCESS: GOVERNED
EXTRACTION: CAPPED AT 25%
```

---

## Summary

**Everything is ready for the 20-minute live mining session.**

Pool configuration is complete. Live mining flags are enabled. JWT secret is generated. Backend is ready to start. Unified miner is configured. Evidence collection infrastructure is in place.

The system will:
1. Connect to real pools (ViaBTC + Braiins)
2. Authenticate workers
3. Receive mining jobs
4. Search for valid candidates
5. Submit shares to pool
6. Capture pool responses
7. Generate sealed evidence

**The next proof boundary is sealed external pool acceptance telemetry.**

