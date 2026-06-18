# HYBA Live Mining — RUN NOW (20 Minutes)

## TL;DR — Copy/Paste These Commands

### Terminal 1 (Backend)
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm run backend:start
```
Wait for: `INFO: Uvicorn running on http://127.0.0.1:3001`

### Terminal 2 (Frontend)
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm run dev
```
Wait for: `VITE v8 ready on http://localhost:3000`

### Terminal 3 (Live Mining — 20 Minutes)
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
bash scripts/START_LIVE_MINING_20MIN.sh
```

Watch the live log stream. When it says "20-MINUTE SESSION COMPLETE", the run is done.

---

## What You'll See

### In Terminal 3 (Mining):

```
╔════════════════════════════════════════════════════════════════╗
║       HYBA LIVE MINING — 20 MIN SHARE ACCEPTANCE TEST          ║
║             ViaBTC + Braiins Dual Pool Session                 ║
╚════════════════════════════════════════════════════════════════╝

✓ Live Stratum I/O:        ENABLED
✓ Live share submit:       ENABLED
✓ Pool config:             config/mining_pools_live.json

📡 Pool Configuration:
  Default pool: viabtc
  ✓ ACTIVE [DEFAULT] ViaBTC BTC
    → stratum+tcp://btc.viabtc.io:3333
    → PYTHIA.001
  ✓ ACTIVE              Braiins Pool
    → stratum+tcp://stratum.braiins.com:3333
    → PYTHAGORAS

✓ Backend API reachable at http://127.0.0.1:3001
```

Then:

```
╔════════════════════════════════════════════════════════════════╗
║                  LIVE MINING SESSION ACTIVE                    ║
╠════════════════════════════════════════════════════════════════╣
║  Start time:       17:52:43                                    ║
║  Duration:         20 minutes                                  ║
║  Pools:            ViaBTC (primary) + Braiins (fallback)       ║
║  Live Stratum:     ENABLED (real pool I/O)                    ║
║  Share submit:     ENABLED (real share submission)            ║
║  Logs:             /tmp/hyba_live_miner_20min.log             ║
║                                                                ║
║  📊 Watching for accepted shares...                            ║
║     (Share acceptance shows as 'Share accepted' in logs)       ║
║     (Pool rejections show as 'Share rejected' in logs)         ║
║                                                                ║
║  Press Ctrl+C to stop early                                   ║
╚════════════════════════════════════════════════════════════════╝
```

Then **live log stream** (real-time output from miner):

```
Connected to ViaBTC pool
Mining difficulty updated: 8388608
Job acquired: job_id=abc123, target=00000000FFFF0000...
Search batch 1: 100k nonces tested
Search batch 2: 100k nonces tested
...
Share submitted: nonce=0x12345678, target_met=true
Share accepted from pool
MINING STATISTICS: 1250 searches, 3 accepted, 1 rejected
```

After 20 minutes:

```
╔════════════════════════════════════════════════════════════════╗
║                   20-MINUTE SESSION COMPLETE                   ║
╠════════════════════════════════════════════════════════════════╣
║  End time:         17:52:43                                    ║
║  Mining Summary:                                               ║
╚════════════════════════════════════════════════════════════════╝

📊 Session Statistics:
────────────────────────────────────────────────────────────────
MINING STATISTICS: 1250 searches, 5 accepted, 2 rejected
Connected to ViaBTC pool
Difficulty updated to: 8388608
────────────────────────────────────────────────────────────────

✓ Miner process 12345 terminated
✓ Session complete. Ready for inspection.
```

---

## What's Actually Happening (System in Action)

### Frontend (localhost:3000)
- Dashboard loads
- Shows health status
- Displays mining jobs
- Real-time connection state

### Backend (localhost:3001)
- REST API serving pool config
- Health/readiness endpoints
- Mining job search
- Statistics collection

### Mining Runtime (Python background process)
- Connects to ViaBTC (real Stratum I/O)
- Subscribes to mining jobs
- Authorizes worker (PYTHIA.001)
- Receives difficulty updates
- Runs structured nonce search
- Submits real shares to pool
- Records accepted/rejected feedback
- Logs everything to `/tmp/hyba_live_miner_20min.log`

---

## Before You Start

### Checklist (< 2 minutes)

```bash
# 1. Verify configuration is set
python3 scripts/configure_live_mining.py --show-config

# 2. Check backend can start
npm run backend:check

# 3. Verify integration fence still passing
npm run test:integration-fence
```

Expected output for all three:
- ✓ Configuration shows ViaBTC (primary) + Braiins (fallback)
- ✓ Backend import OK
- ✓ 25 passed

---

## During the Run (20 minutes)

### What to Watch For

**Good signs:**
- "Connected to ViaBTC pool" — Pool connection successful
- "Job acquired" — Mining job received
- "Share submitted" — Share went to pool
- "Share accepted from pool" — Pool accepted the share ✓

**Warning signs (but normal):**
- "Share rejected" — Pool rejected (difficulty/duplicate)
- "Connection dropped" — Will auto-failover to Braiins
- "Timeout waiting for job" — Pool slow, retrying

**Bad signs (stop immediately):**
- "ERROR" or "Exception" — Something broke
- "No pools enabled" — Configuration issue
- "Authentication failed" — Pool credentials wrong

---

## After the Run (< 1 minute)

### Verify System Health

```bash
# Check that integration fence still passes
npm run test:integration-fence

# Should see:
# ======================== 25 passed in 0.69s ========================
```

### Review Session Metrics

```bash
# Show final statistics
tail -30 /tmp/hyba_live_miner_20min.log

# Count shares by type
grep "Share accepted" /tmp/hyba_live_miner_20min.log | wc -l
grep "Share rejected" /tmp/hyba_live_miner_20min.log | wc -l
```

---

## Troubleshooting

### "npm: command not found"
- You're not in the right directory
- Solution: `cd /Users/demouser/Desktop/HYBA_FULLSTACK`

### Backend won't start
- Port 3001 already in use
- Solution: `lsof -i :3001` then `kill -9 <PID>`

### Mining script says "Backend not reachable"
- Backend not running in Terminal 1
- Solution: Start Terminal 1, wait for "Uvicorn running" message

### "Share rejected" repeatedly
- Pool credentials might be wrong
- Solution: Check `config/mining_pools_live.json`

### Script exits early
- Check `/tmp/hyba_live_miner_20min.log` for errors
- Solution: Review the error, fix, and run again

---

## What This Proves

After a successful 20-minute run:

✓ **Frontend/Backend Integration** — Dashboard loads and communicates  
✓ **Pool Connectivity** — Real Stratum protocol connection works  
✓ **Mining Flow** — Job acquisition → search → submission works  
✓ **Share Handling** — Pool accept/reject feedback loops correctly  
✓ **Guard Logic** — Shares validated before submission  
✓ **Error Handling** — Connection failures handled gracefully  
✓ **System Path** — Entire end-to-end flow works in production mode  

This is your full system in action. Not components. Not mocks. Real pool I/O.

---

## Ready?

Open 3 terminals and paste these commands:

**Terminal 1:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK && npm run backend:start
```

**Terminal 2:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK && npm run dev
```

**Terminal 3:**
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK && bash scripts/START_LIVE_MINING_20MIN.sh
```

Watch it go. 20 minutes. System in action.
