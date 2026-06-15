# PYTHIA/PULVINI Mining Production Readiness Contract

## BLUF

HYBA mining readiness is now judged by operational blockers, not by an unbounded bundle of unrelated science, deployment, and review gates.

The production path is ready only when the critical mining contracts below pass:

1. The unified engine must route every mining search through the PULVINI compressed nonce plan.
2. Every candidate must be locally verified with Bitcoin-compatible SHA-256d header validation before any pool submission.
3. Accepted shares must only increment after the Stratum pool returns an accepted response.
4. Live share submission must remain disabled until the operator deliberately enables it with an approval id.
5. Dev fixtures must be unavailable in production.
6. Known Bitcoin/Stratum pitfalls must be anticipated and handled instead of discovered live.

Scientific evidence remains important, but it is not allowed to block a same-day mining cutover unless it protects funds, secrets, pool correctness, runtime safety, or truth of accepted-share claims.

## Canonical workflow

```text
Pool profile / live Stratum config
        │
        ▼
Subscribe + authorize
        │
        ▼
Live mining.notify job
        │
        ▼
UnifiedMiningEngine.search(job)
        │
        ├─ ConsciousnessEngine selects regime
        ├─ AIOptimizer configures PULVINI compressed nonce plan
        ├─ HENDRIX-Φ / M32 / Yang-Mills / φ-gradient traverse candidate space
        └─ PULVINI compressed solver returns a uint32 candidate
        │
        ▼
Local Bitcoin validation
        │
        ├─ coinbase + extranonce2 assembled
        ├─ merkle root computed
        ├─ 80-byte block header built with correct byte order
        ├─ double-SHA256 applied
        └─ effective target checked
        │
        ▼
Live share submit gate
        │
        ├─ if disabled: reject locally as live_share_submit_disabled
        └─ if enabled: submit to pool
        │
        ▼
Pool ACK truth
        │
        ├─ accepted -> accepted counter increments
        └─ rejected/error/malformed/stale -> rejected counter increments
```

## Blocking contracts

### 1. PULVINI compressed search is mandatory

The unified engine may not claim PULVINI memory compression while silently using the base solver path.

Required state after `UnifiedMiningEngine.search(job)`:

```text
nonce_space_contract = pulvini_phi_compressed_pre_search
complete_nonce_coverage = true
overlap_free_nonce_coverage = true
compressed_working_set_size = 20
retained_kernel_lanes = 12
search_space_size = 2^32
```

### 2. Bitcoin SHA-256d validation is mandatory before pool submission

The solver is allowed to generate candidates. It is not allowed to mark a candidate as externally true.

Local validation must own:

```text
coinbase assembly
extranonce2 length
merkle-root computation
version / prevhash / merkle / ntime / nbits / nonce byte order
80-byte header construction
double SHA-256
effective target check
```

### 3. Pool ACK is the only accepted-share truth

A local valid candidate is not the same thing as a pool-accepted share.

Accepted-share counters can increment only in the explicit pool-accepted branch. Malformed pool responses, rejected responses, stale jobs, low-difficulty shares, submit failures, and disabled live-submit windows must increment rejection/error state instead.

### 4. Live submit is a deliberate launch window

`HYBA_ENABLE_LIVE_STRATUM=true` may be used to connect and receive jobs.

`HYBA_ENABLE_LIVE_SHARE_SUBMIT=true` is separate and must require `HYBA_LIVE_SHARE_APPROVAL_ID`.

This prevents accidental share submission during diagnostics.

### 5. Production never uses dev fixtures

Production must not fabricate mining jobs. If `NODE_ENV=production` or `HYBA_ENV=production`, dev fixture jobs are disabled unless the operator is explicitly outside production.

## Pitfalls and required responses

| Pitfall | Required response |
|---|---|
| Wrong nonce endian | `uint32_little_endian_hex` encodes nonce before header hashing. |
| Wrong prevhash / merkle byte order | Header builder reverses fields exactly once for header construction. |
| Wrong compact target | `compact_to_target(nbits)` is computed and the stricter effective target is used. |
| Extranonce2 wrong size | Validation raises before submit. |
| Stale job after `clean_jobs` | Old jobs are marked stale and rejected locally. |
| Pool auth rejected | Connection/auth state remains failed; no mining success is inferred. |
| Malformed pool response | Response is rejected as invalid structure, never accepted. |
| Pool submit network error | Share is rejected with submit failure and metrics persist. |
| Duplicate/low difficulty pool rejection | Rejection is preserved as rejection. |
| Live share submit accidentally on | Approval id is required or readiness blocks. |
| Metal unavailable | CPU exact SHA-256d verifier remains available; Metal is acceleration evidence, not truth. |
| Broad science gate fails | Treat as advisory unless it impacts runtime safety, pool correctness, secrets, or claims. |

## Reasonable gate policy

Use the operational readiness doctor for same-day mining deployment:

```bash
npm run prod:command-room:gate
```

This runs the critical mining contracts and the production build. It writes a packet under:

```text
artifacts/mining_readiness/
```

Use the live version after production env and pool profiles are injected:

```bash
npm run prod:mining:live:ready
```

The old broad forensic gate remains available for deeper review:

```bash
npm run prod:command-room:gate:full-forensic
```

That broad gate is not the same thing as immediate mining readiness. It is a release-review evidence bundle.

## Operator launch sequence

### Prepare

```bash
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install mlx
npm install --legacy-peer-deps --no-audit --no-fund
export PYTHONPATH=python_backend
npm run prod:command-room:gate
```

### Live connection window, no share submission yet

```bash
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_MINING_AUTOCONNECT=false
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
export HYBA_ENABLE_AUDIT_LOGGING=true
export PULVINI_BACKEND_URL=http://127.0.0.1:3001

# private values stay local
export JWT_SECRET='<real-secret>'
export HYBA_OPERATOR_CREDENTIALS='<operator:$argon2id$...:mining:operate>'
export HYBA_POOL_<POOL>_URL='<stratum+tcp://... or stratum+ssl://...>'
export HYBA_POOL_<POOL>_USERNAME='<worker-or-address>'
export HYBA_POOL_<POOL>_PASSWORD='<pool-password-or-x>'
export HYBA_POOL_<POOL>_STRATUM_VERSION='1'

npm run prod:mining:live:ready
npm run build
npm start
```

### Share-submit window

```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_LIVE_SHARE_APPROVAL_ID='<signed-launch-ticket-id>'
```

Then start mining from the authenticated operator surface.

## Claim boundary

Correct claim before pool ACK:

```text
HYBA is prepared for a controlled live mining run.
```

Correct claim after pool ACK:

```text
HYBA has pool-side accepted-share evidence.
```

Do not make revenue, solvency, or first-block claims before pool-side evidence exists.
