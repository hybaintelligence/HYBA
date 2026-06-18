# HYBA Live Mining — 20-Minute Session Quickstart

## Overview

Configure and run a 20-minute live mining session against **ViaBTC** (primary) and **Braiins** (fallback) pools with full Stratum I/O and share submission enabled.

## Prerequisites

✓ Backend dependencies installed  
✓ Python 3.12+  
✓ Node.js 20+  
✓ `.env.local` file (created by configuration script)

## Quick Start (4 Steps)

### Step 1: Configure Pools and JWT

```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Quick configuration with default credentials
python3 scripts/configure_live_mining.py --quick --generate-jwt --enable-live
```

**What this does:**
- Generates a new JWT secret
- Configures ViaBTC as primary pool (PYTHIA.001)
- Configures Braiins as fallback pool (PYTHAGORAS)
- Enables live Stratum I/O and share submission
- Sets environment to development mode

**Verify configuration:**
```bash
python3 scripts/configure_live_mining.py --show-config
```

Expected output:
```
✓ ViaBTC BTC [DEFAULT]
  URL: stratum+tcp://btc.viabtc.io:3333
  User: PYTHIA.001

✓ Braiins Pool
  URL: stratum+tcp://stratum.braiins.com:3333
  User: PYTHAGORAS
```

### Step 2: Start the Backend (Terminal 1)

```bash
npm run backend:start
```

Wait for output:
```
INFO:     Uvicorn running on http://127.0.0.1:3001
```

### Step 3: Start the Frontend (Terminal 2)

```bash
npm run dev
```

Wait for output:
```
VITE v8.0.16  ready in XXX ms

➜  Local:   http://localhost:3000/
```

### Step 4: Run 20-Minute Live Mining Session (Terminal 3)

```bash
bash scripts/START_LIVE_MINING_20MIN.sh
```

You'll see:
```
╔════════════════════════════════════════════════════════════════╗
║       HYBA LIVE MINING — 20 MIN SHARE ACCEPTANCE TEST          ║
║             ViaBTC + Braiins Dual Pool Session                 ║"
╚════════════════════════════════════════════════════════════════╝

✓ Live Stratum I/O:        ENABLED
✓ Live share submit:       ENABLED
✓ Pool config:             config/mining_pools_live.json

📡 Pool Configuration:
  Default pool: viabtc
  ✓ ACTIVE [DEFAULT] ViaBTC BTC
  ✓ ACTIVE              Braiins Pool
```

## Configuration Reference

### Pool Credentials

| Pool | URL | User | Password |
|------|-----|------|----------|
| ViaBTC (Primary) | stratum+tcp://btc.viabtc.io:3333 | PYTHIA.001 | 123 |
| Braiins (Fallback) | stratum+tcp://stratum.braiins.com:3333 | PYTHAGORAS | anything123 |
| Braiins V2 | stratum2+ssl://stratum.braiins.com:3336 | PYTHAGORAS | anything123 |

**Note:** These are public pool routing parameters, not secrets.

### Custom Configuration

```bash
# Use different ViaBTC credentials
python3 scripts/configure_live_mining.py \
  --viabtc-user YOUR_USERNAME \
  --viabtc-pass YOUR_PASSWORD \
  --generate-jwt \
  --enable-live

# Use Braiins as default pool
python3 scripts/configure_live_mining.py \
  --generate-jwt \
  --enable-live \
  --default-pool braiins

# Set custom JWT secret
python3 scripts/configure_live_mining.py \
  --jwt-secret your-secret-here \
  --enable-live

# Check current configuration
python3 scripts/configure_live_mining.py --show-config
```

## Mining Session Details

### What Gets Logged

The miner logs to: `/tmp/hyba_live_miner_20min.log`

**Key metrics tracked:**
- Pool connection state
- Share submissions (accepted/rejected)
- Stratum difficulty updates
- Job acquisition and completion
- Search iterations and time

**Example log entries:**
```
Connected to ViaBTC pool
Mining difficulty updated: 8388608
Share submitted: nonce=0x12345678
Share accepted from pool
Share rejected: difficulty too low
MINING STATISTICS: 1250 searches, 3 accepted, 1 rejected
```

### Live Monitoring

The script streams logs in real-time. Watch for:

✓ **Share accepted** — indicates successful pool submission  
✗ **Share rejected** — pool rejected the submission  
⚠️ **Connection dropped** — pool disconnected (automatic fallback to Braiins)  
📊 **MINING STATISTICS** — final session summary

### Session Timeline

| Time | Event |
|------|-------|
| 0:00 | Miner starts, connects to ViaBTC |
| 0:05 | First mining job acquired |
| 0:30-19:30 | Continuous mining, share submissions |
| 19:55 | Session approaching end |
| 20:00 | Session terminates, statistics collected |

## Troubleshooting

### Backend Won't Start

```bash
# Check if port 3001 is in use
lsof -i :3001

# Kill existing process
killall uvicorn

# Try again
npm run backend:start
```

### Pool Connection Fails

Check credentials in pool config:
```bash
python3 scripts/configure_live_mining.py --show-config
```

Verify network access:
```bash
nc -zv btc.viabtc.io 3333
```

### No Shares Submitted

1. Check if live share submit is enabled:
   ```bash
   grep HYBA_ENABLE_LIVE_SHARE_SUBMIT .env.local
   ```
   Should be: `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true`

2. Check pool username and password in config

3. Review `/tmp/hyba_live_miner_20min.log` for connection errors

### Miner Crashes Early

Check the log:
```bash
tail -50 /tmp/hyba_live_miner_20min.log
```

Common issues:
- JWT_SECRET not set: `python3 scripts/configure_live_mining.py --generate-jwt`
- Backend not running: Start with `npm run backend:start`
- Invalid pool credentials: Update with config script

## Session Artifacts

After the 20-minute run:

```
/tmp/hyba_live_miner_20min.log       — Complete session log
```

Extract key metrics:
```bash
# Show share statistics
grep "MINING STATISTICS" /tmp/hyba_live_miner_20min.log

# Show all share submissions
grep -E "(accepted|rejected)" /tmp/hyba_live_miner_20min.log

# Count connection events
grep -E "(Connected|Disconnected)" /tmp/hyba_live_miner_20min.log | wc -l
```

## Integration Fence Verification

After the live session, run the integration fence to verify system health:

```bash
npm run test:integration-fence
```

Expected result: **25/25 tests passing**

This confirms:
- Frontend/backend contract alignment ✓
- Pool handshake protocol correctness ✓
- Dashboard bootstrap viability ✓
- Runtime mining path behavior ✓

## Next Steps

1. **Review Session Metrics**
   - Total shares accepted
   - Accepted/rejected ratio
   - Pool connectivity pattern

2. **Validate Pool Integration**
   - Check that shares reach the pool
   - Verify difficulty adjustments
   - Monitor for authentication issues

3. **Run Production Gate**
   ```bash
   npm run prod:check
   ```

4. **Inspect Audit Logs**
   ```bash
   ls -lh logs/audit/
   ```

## Environment Variables (Advanced)

These are automatically set by the configuration script, but you can override:

```bash
# In .env.local:
HYBA_ENABLE_LIVE_STRATUM=true              # Live pool I/O
HYBA_ENABLE_LIVE_SHARE_SUBMIT=true         # Real share submission
HYBA_ENABLE_AUDIT_LOGGING=true             # Session audit trail
HYBA_POOL_CONFIG_PATH=config/mining_pools_live.json
JWT_SECRET=<auto-generated>
NODE_ENV=development
HYBA_ENV=development
HYBA_ALLOW_DEV_FIXTURES=false              # No test fixtures
```

## FAQ

**Q: Can I stop the session early?**  
A: Yes, press Ctrl+C. The miner will gracefully shutdown and log final statistics.

**Q: What if a pool goes offline?**  
A: The miner automatically tries the next enabled pool (Braiins is configured as fallback).

**Q: Are my pool credentials secure?**  
A: Credentials are stored in `.env.local` with 0600 permissions (owner read/write only). Never commit to git.

**Q: Can I run multiple 20-minute sessions back-to-back?**  
A: Yes, just run the script again. Each session gets its own log file with timestamp.

**Q: What's the difference between this and the 10-minute script?**  
A: Only the duration (20 vs 10 minutes) and log file name. Everything else is identical.

## Support

For issues or questions:

1. Check the log: `tail -100 /tmp/hyba_live_miner_20min.log`
2. Verify configuration: `python3 scripts/configure_live_mining.py --show-config`
3. Run integration fence: `npm run test:integration-fence`
4. Review backend health: `curl http://127.0.0.1:3001/health`

---

**Ready?** Run: `bash scripts/START_LIVE_MINING_20MIN.sh`
