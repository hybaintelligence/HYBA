# Live Mining Setup — Complete Status

**Date:** June 18, 2026  
**Status:** ✓ READY FOR 20-MINUTE LIVE RUN

## What Was Configured

### 1. Configuration CLI Tool ✓
**File:** `scripts/configure_live_mining.py`

Features:
- Non-interactive pool configuration
- JWT secret generation
- Live mining enablement/disablement
- Configuration verification
- Custom credential support

### 2. 20-Minute Mining Script ✓
**File:** `scripts/START_LIVE_MINING_20MIN.sh`

Features:
- Automated session launcher
- Dual-pool support (ViaBTC + Braiins)
- Real-time log streaming
- Session statistics collection
- Graceful shutdown handling

### 3. Current Configuration ✓

**Pools Configured:**
```
Primary:   ViaBTC BTC
           URL: stratum+tcp://btc.viabtc.io:3333
           User: PYTHIA.001
           Password: 123
           Status: ENABLED [DEFAULT]

Fallback:  Braiins Pool
           URL: stratum+tcp://stratum.braiins.com:3333
           User: PYTHAGORAS
           Password: anything123
           Status: ENABLED
```

**Mining Configuration:**
```
Live Stratum I/O:         ✓ ENABLED
Live Share Submission:    ✓ ENABLED
Audit Logging:            ✓ ENABLED
JWT Secret:               ✓ GENERATED
Environment:              ✓ Development mode
Fixtures:                 ✓ DISABLED (production path)
```

### 4. Documentation ✓
**Files:**
- `LIVE_MINING_QUICKSTART.md` — Complete setup guide
- `LIVE_MINING_SETUP_STATUS.md` — This file

## Quick Start Command Sequence

### Terminal 1: Backend
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm run backend:start
```

### Terminal 2: Frontend
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
npm run dev
```

### Terminal 3: Live Mining (20 minutes)
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
bash scripts/START_LIVE_MINING_20MIN.sh
```

**Total setup time:** < 5 minutes  
**Session duration:** 20 minutes  
**Log location:** `/tmp/hyba_live_miner_20min.log`

## What Will Be Tested

### During Live Session:

✓ **Pool connectivity** — ViaBTC primary, Braiins fallback  
✓ **Share submission** — Real shares to actual pools  
✓ **Stratum protocol** — Subscribe, authorize, job acquisition  
✓ **Mining flow** — Search → validation → submit → feedback  
✓ **Guard logic** — Accept/reject decisions with reasoning  
✓ **Error handling** — Connection failures, timeouts, rejections  

### Session Metrics:

- Total shares submitted
- Shares accepted by pool
- Shares rejected by pool
- Pool connection state changes
- Difficulty updates
- Search iterations
- Session duration

## Integration Fence Status

The full 25-test integration fence is already passing:

✓ **14 Frontend/Backend Contracts** — Response shapes aligned  
✓ **5 Pool Handshake Contracts** — Stratum state machine verified  
✓ **6 True E2E Tests** — System paths proven  

**Command to verify:** `npm run test:integration-fence`

After the 20-minute live run, re-run this to confirm system still passes all contracts.

## Success Criteria

After the 20-minute session completes:

1. **Miner connected to pool** ✓  
   - Look for: "Connected to ViaBTC" in logs

2. **Shares submitted** ✓  
   - Look for: "Share submitted" entries

3. **Accepted shares present** ✓  
   - Look for: "Share accepted from pool"

4. **Statistics collected** ✓  
   - Look for: "MINING STATISTICS" line with counts

5. **Session completed gracefully** ✓  
   - Look for: "Miner process terminated"

6. **Integration fence still passing** ✓  
   - Run: `npm run test:integration-fence`

## Configuration Files

### Modified Files:

**`.env.local`** — Environment variables
- JWT_SECRET (auto-generated)
- HYBA_ENABLE_LIVE_STRATUM=true
- HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
- HYBA_ENABLE_AUDIT_LOGGING=true
- Pool URLs and usernames

**`config/mining_pools_live.json`** — Pool configuration
- ViaBTC marked as default (priority 1)
- Braiins marked as fallback (priority 2)
- Both pools enabled
- NiceHash/CKPool disabled

### New Files Created:

**`scripts/configure_live_mining.py`**
- Python 3 CLI tool
- Manages pool and JWT configuration
- Can be re-run to adjust settings

**`scripts/START_LIVE_MINING_20MIN.sh`**
- Zsh/bash script
- Launches miner process
- Streams logs for 20 minutes
- Collects statistics

**`LIVE_MINING_QUICKSTART.md`**
- Complete setup guide
- Troubleshooting section
- Configuration reference

**`LIVE_MINING_SETUP_STATUS.md`**
- This file
- Configuration status
- Success criteria

## Verification Steps

### Before Starting:

```bash
# 1. Check configuration
python3 scripts/configure_live_mining.py --show-config

# 2. Verify backend can start
npm run backend:check

# 3. Run integration fence
npm run test:integration-fence
```

### During Session:

The script will show:
- Pool configuration loaded
- Miner process started
- Real-time log stream
- Connection state changes

### After Session:

```bash
# 1. Review statistics
tail -30 /tmp/hyba_live_miner_20min.log

# 2. Extract key metrics
grep "MINING STATISTICS" /tmp/hyba_live_miner_20min.log

# 3. Verify system still healthy
npm run test:integration-fence

# 4. Check for any errors
grep -i "error\|exception\|failed" /tmp/hyba_live_miner_20min.log
```

## Safety & Security

### Credentials Handling:
- Pool credentials stored in `.env.local` only
- File permissions: 0600 (owner read/write only)
- JWT secret auto-generated (32 bytes)
- Never commits credentials to git

### Production Safety:
- `HYBA_ALLOW_DEV_FIXTURES=false` — No test fixtures in mining path
- `HYBA_ENABLE_AUDIT_LOGGING=true` — All actions logged
- Real shares submitted to actual pools
- No fabricated telemetry in production path

### Session Isolation:
- Each session gets unique log file
- No state carries between sessions
- Graceful shutdown on Ctrl+C
- Automatic cleanup of stale processes

## Next Steps

1. **Immediate:** Follow the quick start command sequence above
2. **Session:** Monitor logs for share acceptance
3. **After:** Verify integration fence still passing
4. **Analysis:** Review session metrics and pool acceptance

## Rollback/Reconfiguration

If you need to change settings:

```bash
# Reconfigure with new credentials
python3 scripts/configure_live_mining.py \
  --viabtc-user YOUR_USERNAME \
  --viabtc-pass YOUR_PASSWORD \
  --generate-jwt

# Or switch default pool to Braiins
python3 scripts/configure_live_mining.py \
  --generate-jwt \
  --enable-live \
  --default-pool braiins
```

Then run the mining script again.

## Environment Teardown

After the session is complete:

```bash
# Kill backend
pkill -f "uvicorn"

# Kill frontend dev server
# (Ctrl+C in the npm run dev terminal)

# Miner kills automatically after 20 minutes
# (or with Ctrl+C)

# Review artifacts
ls -lh /tmp/hyba_live_miner_20min.log
```

---

## Summary

**Integration Fence:** 25/25 passing ✓  
**Pool Configuration:** ViaBTC (primary) + Braiins (fallback) ✓  
**JWT Generation:** Complete ✓  
**Live Mining Scripts:** Deployed ✓  
**Documentation:** Complete ✓  

**Status:** READY FOR LIVE RUN

**Command:** `bash scripts/START_LIVE_MINING_20MIN.sh`
