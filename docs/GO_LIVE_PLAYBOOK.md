Positano2!
se cli # GO-LIVE PLAYBOOK: Mining Treasury Launch

**Date**: 2026-06-22  
**Identity**: Internal treasury engine — not a product, not a customer offering  
**Motto**: *Boring operations. Clean evidence. Safe treasury.*

---

## Core Identity (Never Blur These Lines)

| Layer | Identity | Status |
|-------|----------|--------|
| **Mining** | Treasury engine | Going live today |
| **Quantum Intelligence** | Product | Not mining. Never mining. |
| **Salamander** | Immune system | Monitoring treasury |
| **HYBA_FULLSTACK** | Today's vessel | Code frozen |
| **HYBA_Unified_Backend** | Future fusion substrate | Stays offline until treasury creates runway |

**Rules**:
- No repo merger today
- No product claims
- No customer mining language
- No fabricated revenue
- No live share submit until pool auth AND cooling confirmed
- Every accepted share becomes treasury evidence

---

## Operations Room

### Role 1 — Mining Operator
**Owner**: _______________  
**Responsibilities**:
- Pool credentials (Stratum URL, worker name, password)
- Stratum authentication sequence
- Live share submit flag management
- Kill switch authority (operator-held)
- Connection monitoring

**Credentials**:
```
Pool URL:  stratum+tcp://btc.viabtc.com:3333
Pool Name: viabtc
Worker:    HYBA_PYTHAGORAS.quantum_001
Password:  [REDACTED]
```

**Tools**:
- `MiningExecutiveController` — live execution path
- `StratumClient` — pool connection
- Kill switch: `HYBA_ENABLE_LIVE_SHARE_SUBMIT=false`

### Role 2 — Safety Operator
**Owner**: _______________  
**Responsibilities**:
- Power stability monitoring
- Cooling system verification
- Machine temperature tracking
- Cable integrity inspection
- Noise level monitoring
- Physical access control
- Shutdown authority

**Checklist**:
- [ ] Power supply stable (<5% variance)
- [ ] Cooling fans operational, airflow unobstructed
- [ ] CPU/GPU temperature < 80°C
- [ ] All cables secured, no loose connections
- [ ] Ambient noise within acceptable range
- [ ] Physical access restricted to authorized operators
- [ ] Emergency shutdown procedure understood

### Role 3 — Evidence Operator
**Owner**: _______________  
**Responsibilities**:
- Run all tests, save terminal output
- Record commit SHA at start and stop
- Record pool auth result
- Record start time and stop time
- Record accepted shares and rejected shares
- Record machine state (temp, power, uptime)
- Save all artifacts to `artifacts/treasury/`

**Evidence Log Template**:
```json
{
  "commit_sha": "",
  "machine_id": "",
  "python_version": "",
  "pool": "",
  "worker": "",
  "start_time": "",
  "live_share_submit_enabled_at": "",
  "accepted_shares": 0,
  "rejected_shares": 0,
  "reported_revenue_btc": 0.0,
  "temperature_notes": "",
  "power_notes": "",
  "operator_decision": "",
  "stop_time": "",
  "final_status": ""
}
```

### Role 4 — Treasury Operator
**Owner**: _______________  
**Responsibilities**:
- Track all operational costs (electricity, hardware, connectivity)
- Monitor pool account and wallet balance
- Verify payout address
- Calculate expected mining fees
- Track electricity cost exposure
- Define reinvestment order

**Tracking Sheet**:
```csv
Date,Pool,Worker,Revenue_BTC,Cost_USD,Fees_BTC,Net_BTC,Reinvestment
2026-06-22,viabtc,HYBA_PYTHAGORAS.quantum_001,0.0,0.0,0.0,0.0,"None"
```

---

## First Live Window Timeline

**T+0**: Pool auth confirmed, share submit still false.  
**T+5**: Cooling stable, power stable, logs recording.  
**T+10**: Flip `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true` only if Safety + Mining both say GO.  
**T+15**: First monitoring checkpoint: accepted/rejected shares, temp, power, process health.  
**T+30**: Second checkpoint: treasury evidence snapshot.  
**T+60**: First operating review: continue, throttle, or stop.

---

## Room Rule

**Any one operator can stop. Nobody needs permission to protect the system.**

---

## Go/No-Go Sequence

### Step 1: Code Freeze Check
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Verify clean state
git status
git log -1 --oneline

# Expected: Working tree clean, known commit
```
**[ ] PASS** _______________

### Step 2: Full Test Suite
```bash
PYTHONPATH=python_backend python3 -m pytest \
  tests/test_quantum_regeneration_properties.py \
  tests/test_salamander_frontier.py \
  tests/test_regeneration_manager_api.py \
  tests/test_salamander_mining_integration.py \
  -v 2>&1 | tee artifacts/treasury/test_results_$(date +%Y%m%d_%H%M%S).txt
```
**Expected**: 51/51 PASSED  
**[ ] PASS** _______________

### Step 3: Dry-Run Validation
```bash
export PYTHONPATH=python_backend
export HYBA_MINING_MODE=dry_run
export HYBA_SALAMANDER_STRICT_PREFLIGHT=false
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false

python3 -m pythia_mining.production_mining_system 2>&1 | \
  tee artifacts/treasury/dry_run_$(date +%Y%m%d_%H%M%S).txt
```
**Expected**: Session completes, revenue = 0.0 BTC, Salamander gate ready  
**[ ] PASS** _______________

### Step 4: Live Preflight (No Share Submit)
```bash
export HYBA_MINING_MODE=live
export HYBA_POOL_URL="stratum+tcp://btc.viabtc.com:3333"
export HYBA_POOL_NAME="viabtc"
export HYBA_POOL_WORKER="REAL_WORKER"
export HYBA_POOL_PASSWORD="REAL_PASSWORD"
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
export HYBA_OPERATOR_APPROVED_LIVE_MINING=true

python3 -m pythia_mining.production_mining_system 2>&1 | \
  tee artifacts/treasury/live_preflight_$(date +%Y%m%d_%H%M%S).txt
```
**Expected**: Pool subscribe/auth succeeds, telemetry visible, shares = 0 (not submitted)  
**[ ] PASS** _______________

### Step 5: Safety Confirmation
- [ ] Pool auth confirmed
- [ ] Telemetry visible
- [ ] Machine temperature stable (< 80°C)
- [ ] Power stable (< 5% variance)
- [ ] Kill switch location known by operator
- [ ] Operator understands: flip HYBA_ENABLE_LIVE_SHARE_SUBMIT=true to start
- [ ] Operator understands: flip HYBA_ENABLE_LIVE_SHARE_SUBMIT=false to stop

**[ ] PASS** _______________

### Step 6: Live Start
```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true

# Start executive path
# (operator executes MiningExecutiveController + StratumClient path)
```
**Expected**: Shares flowing, telemetry updating, revenue tracking  
**[ ] PASS** _______________

### Step 7: Continuous Monitoring
Every 15 minutes:
- [ ] Pool connection alive
- [ ] Temperature stable
- [ ] Power stable
- [ ] Shares being accepted
- [ ] Revenue accumulating

**[ ] PASS** _______________

### Step 8: Stop Sequence
```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false

# Save final session data
python3 -c "
from pythia_mining.production_mining_system import ProductionMiningSystem
system = ProductionMiningSystem()
report = system.get_revenue_report()
print(report)
" > artifacts/treasury/final_report_$(date +%Y%m%d_%H%M%S).json

# Record final evidence
git log -1 --oneline
```
**[ ] DONE** _______________

---

## Safety Rules

### The Kill Switch
```bash
# STOP all live mining immediately
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false

# If share submit must stop NOW, also kill the process
kill -INT <pid>

# If process does not respond
kill -9 <pid>
```

### When to Kill
- Temperature exceeds 85°C
- Pool connection drops for >60 seconds
- Unexplained share rejection rate >50%
- Revenue anomalies (negative, impossible values)
- Power fluctuation >10%
- Any alert from monitoring
- Operator feels unsafe

### After Kill
1. Save all logs
2. Record final state
3. Write incident report
4. Do NOT restart until root cause identified

---

## Boundary Conditions

### What NOT to Do
- ❌ Do NOT claim mining is a product
- ❌ Do NOT tell customers about mining
- ❌ Do NOT merge any new code today
- ❌ Do NOT fabricate revenue in any document
- ❌ Do NOT touch HYBA_Unified_Backend
- ❌ Do NOT mine on non-HYBA_FULLSTACK path

### What IS Approved
- ✅ Mine from HYBA_FULLSTACK only
- ✅ Save all evidence to `artifacts/treasury/`
- ✅ Track every cost and every satoshi
- ✅ Stop immediately if anything feels wrong
- ✅ Call the kill switch early, call it often

---

## Treasury Rule

**Count only pool-confirmed accepted shares and pool/account-confirmed revenue. Nothing else is revenue.**

---

## Salamander Rule

**If the guard locks, you do not argue with it today. You stop, preserve evidence, diagnose, repair, rerun preflight.**

---

## Artifacts Directory

```
artifacts/treasury/
├── test_results_YYYYMMDD_HHMMSS.txt     # Test output
├── dry_run_YYYYMMDD_HHMMSS.txt          # Dry run output
├── live_preflight_YYYYMMDD_HHMMSS.txt   # Live preflight output
├── live_session_YYYYMMDD_HHMMSS.json    # Live session data
├── final_report_YYYYMMDD_HHMMSS.json    # Final revenue report
├── evidence_log_YYYYMMDD_HHMMSS.json    # Evidence operator log
└── treasury_tracking.csv                # Treasury operator tracking
```

---

## Sign-Off

**Mining Operator**: _______________ Date: _______________ Time: _______________  

**Safety Operator**: _______________ Date: _______________ Time: _______________  

**Evidence Operator**: _______________ Date: _______________ Time: _______________  

**Treasury Operator**: _______________ Date: _______________ Time: _______________  

**Go Decision**: Yes / No  

---

**Last Updated**: 2026-06-22  
**Path**: `HYBA_FULLSTACK` only  
**Motto**: *Boring operations. Clean evidence. Safe treasury.*