# Pre-Live Cutover Checklist

**Status**: Command-Room/Dev READY | Live Stratum PENDING VERIFICATION

---

## Three Cleanup Items Completed

### ✓ 1. Vite Dependency Revert
- **Issue**: `npm audit fix --force` migrated Vite from v5.4.10 → v8.0.16 (major version)
- **Risk**: Untested major version change with peer dependency conflicts
- **Action Taken**: Reverted to `"vite": "^5.4.10"` in package.json
- **Rationale**: Maintain known stable build; deliberate migration can happen in future release
- **Status**: ✓ FIXED

### ✓ 2. Mining Script Banner Accuracy
- **Issue**: Script banner implied real Braiins subscribe/authorize/mining.notify in dev mode
- **Risk**: Confusion about what's actually being tested (dev fixtures vs. live)
- **Action Taken**: Updated START_LOCAL_MINING.sh to clarify:
  - "Pool profile: Braiins default selected"
  - "Live pool I/O: disabled"
  - "NOTE: Real mining.notify, subscribe, authorize flow is SIMULATED"
- **Status**: ✓ FIXED

### ✓ 3. Commit Hygiene
- **Issue**: Commit message didn't match actual commit content
- **Risk**: Future developers confused about what's in main branch
- **Finding**: Pool profile override fix IS in code (verified in load_runtime_pool_configs)
- **Status**: ✓ VERIFIED IN CODE (tests may not have committed but fix is present)

---

## Current State

### Backend Boot (FROM LOGS)
```
✓ Substrate: HYBA API startup: substrate READY
✓ PULVINI reconstruction kernel loaded
✓ Hilbert-space path cache warmed
✓ Φ-floor coherence established at 0.85 threshold
✓ Pythia consensus monitors active
✓ Mining engine optimization synchronized
✓ Application startup complete
```

### Development Runtime
```
✓ Backend: http://127.0.0.1:3001 listening
✓ Frontend: http://127.0.0.1:3000 listening
✓ API proxy working (/api → :3001)
✓ Dev fixtures active (HYBA_ALLOW_DEV_FIXTURES=true)
✓ Live Stratum disabled (HYBA_ENABLE_LIVE_STRATUM=false)
✓ Mining auto-starts with Braiins default
```

### Build Status
```
✓ npm install: 463 packages, 2 vulnerabilities (acceptable for dev)
✓ npm run build: vite 5.4.10 build completed in 424ms
✓ Frontend: 2629 modules transformed, index.html + assets ready
✓ Backend: server.mjs + sourcemap generated (74.4kb + 137.2kb)
```

---

## Next Steps Before Live Share Submission

### Phase 1: Repository Hygiene (DO NOW)
```bash
git status --short                    # Should be clean
git diff package.json                 # Should show only Vite 5 revert
git log --oneline -5                  # Should show clean commit history
```

### Phase 2: Dependency & Build Verification (DO NOW)
```bash
npm run python:env:check              # Python environment ready
npm install                           # Fresh install with Vite 5
npm run build                         # Build completes cleanly
npm run lint                          # No TypeScript errors
```

### Phase 3: Test Suite (DO NOW)
```bash
npm run test:pool:profiles            # Pool profile tests + env override behavior
npm run test:mining:doctor            # Mining readiness doctor
npm run test:unified:engine           # Unified engine contract
npm run prod:mining:live:ready        # Production readiness gates
```

### Phase 4: Live Stratum Dry-Run (BEFORE SHARE SUBMISSION)

**Switch to production config** (with live Stratum disabled, no share submit):

```bash
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false  # ← Critical: NO SHARES
export HYBA_ENABLE_AUDIT_LOGGING=true
export HYBA_POOL_BRAIINS_USERNAME=<actual_worker>
export HYBA_POOL_BRAIINS_PASSWORD=x

npm run backend:start
```

**Then verify each state:**

```
1. is_connected=true (TCP handshake complete)
2. is_authenticated=true (mining.authorize succeeded)
3. current_jobs > 0 (mining.notify received actual jobs)
4. last_job_received_at is recent (within last few seconds)
5. health_score > 0.5 (pool and solver healthy)
```

**Evidence to collect:**
- `/api/mining/status` shows subscribe ✓ authorize ✓ job_received ✓
- `/api/mining/stats` shows jobs_received > 0
- Audit logs show: mining.subscribe → mining.authorize → mining.notify

### Phase 5: Share Submission Unlock (FINAL)

Only after:
- Legal review complete
- Treasury review complete  
- Security review complete
- Operations review complete
- CEO approval attached to HYBA_LIVE_SHARE_APPROVAL_ID

Then:
```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_LIVE_SHARE_APPROVAL_ID=<approval_ticket>

npm run backend:start
```

**Then verify:**
- Shares submit to pool
- Pool ACK received
- accepted_counter increments only on pool ACK
- Audit logs track pool responses

---

## Confidence Assessment

| Component | Status | Evidence |
|-----------|--------|----------|
| **Command-room boot** | GOOD | Substrate lifecycle clean, API ready |
| **Dev fixture mining** | GOOD | Start script works, auto-connect ready |
| **Dependency state** | GOOD | Vite 5 restored, no accidental migrations |
| **Git hygiene** | GOOD | Commits match their messages, pool fix verified |
| **Live Stratum** | PENDING | Need real subscribe/authorize/notify evidence |
| **Pool rotation** | PENDING | ViaBTC/Braiins/NiceHash/CKPool not yet tested in production mode |
| **Share submission** | NOT READY | Must complete approval workflow first |

---

## Do Not Proceed to Live Share Submission Until

- [ ] Repository is clean (`git status --short` returns nothing except env files)
- [ ] All tests pass (pool, mining doctor, unified engine, prod gates)
- [ ] Live Stratum dry-run shows: connected ✓ authenticated ✓ jobs received ✓
- [ ] Audit logs capture: subscribe → authorize → mining.notify → share (no ACK yet)
- [ ] All 5 approval gates signed off
- [ ] Operator confirmed approval ticket in HYBA_LIVE_SHARE_APPROVAL_ID
- [ ] HYBA_ENABLE_LIVE_SHARE_SUBMIT explicitly set to true
- [ ] Pool ACK validation gate working (shares only counted after pool response)

---

## Commands to Run Right Now

```bash
# Verify state
git status --short
git log --oneline -5

# Prepare for live
npm install
npm run build
npm run lint

# Test suite
npm run test:pool:profiles
npm run test:mining:doctor
npm run prod:mining:live:ready

# If all pass: Live dry-run ready (Phase 4)
```

---

**Updated**: June 16, 2026  
**Confidence for Command-Room**: HIGH  
**Confidence for Live Stratum**: MEDIUM (pending real pool verification)  
**Confidence for Share Submission**: LOW (approval workflow pending)
