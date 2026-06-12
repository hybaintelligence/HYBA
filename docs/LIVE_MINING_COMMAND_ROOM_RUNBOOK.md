# HYBA_FULLSTACK Live Mining Command-Room Runbook

**Status:** emergency production-readiness path  
**Purpose:** move from RC evidence to live mining when hosted CI is unavailable  
**Owner:** HYBA Group / Company accountable operator  

This runbook replaces a hosted-CI dependency with a local evidence regime. It does **not** waive production standards. It changes where the evidence is produced: from hosted CI to a controlled command-room machine operated by an accountable human.

---

## 1. Command-room doctrine

HYBA_FULLSTACK exists to fund HYBA. The shortage of runway is a legitimate operating constraint, but it does not justify blind activation.

The correct posture is:

```text
No CI available -> local evidence packet required.
No evidence packet -> no live share submission.
No pool-side accepted-share evidence -> no revenue claim.
No treasury/legal approval -> no payroll or office reliance.
```

The target is to reach live mining quickly while preserving:

- anti-simulation discipline;
- production environment validation;
- MIDAS-controlled mining operations;
- disabled autoconnect by default;
- signed live-share approval;
- pool-side reconciliation before treasury reliance.

---

## 2. One-machine local evidence gate

Run from a clean checkout on the command-room machine:

```bash
git pull origin main
npm ci
npm run prod:local:gate
```

This creates a timestamped JSON evidence packet:

```text
artifacts/production_readiness/local_production_gate_rc_<timestamp>.json
```

The packet captures:

- live deployment forensic audit;
- runtime mock/static telemetry guard;
- TypeScript lint;
- production build;
- backend unit tests;
- backend E2E tests;
- live deployment E2E tests;
- live deployment property tests;
- stdout/stderr tails for each step;
- host/platform summary.

This gate does not require production secrets and does not connect to a pool.

---

## 3. Live environment gate

Inject production secrets from the controlled secret store or local sealed environment file that is **not committed**.

Minimum required environment:

```bash
export NODE_ENV=production
export HYBA_ENV=production
export HYBA_ALLOW_DEV_FIXTURES=false
export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_MINING_AUTOCONNECT=false
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
export HYBA_ENABLE_AUDIT_LOGGING=true
export JWT_SECRET='<32+ char production secret>'
export HYBA_OPERATOR_CREDENTIALS='ceo:$argon2id$...:ceo;miner:$argon2id$...:mining_operator'
export PULVINI_BACKEND_URL='http://127.0.0.1:3001'
```

Configure exactly one pool first. Example ViaBTC shape:

```bash
export HYBA_POOL_VIABTC_URL='stratum+tcp://<host>:<port>'
export HYBA_POOL_VIABTC_USERNAME='<account.worker>'
export HYBA_POOL_VIABTC_PASSWORD='<pool-password-or-x>'
export HYBA_POOL_VIABTC_STRATUM_VERSION='1'
```

Then run:

```bash
npm run prod:live:gate
```

This creates:

```text
artifacts/production_readiness/local_production_gate_live_<timestamp>.json
```

The live gate validates:

- production flags;
- operator credential format;
- backend URL;
- pool credential completeness;
- audit logging enabled;
- PULVINI live-cut state invariants, if a state file is present.

---

## 4. Start production without autoconnect

Build and start production with share submission disabled:

```bash
npm run build
npm start
```

Required launch posture:

```text
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
```

Expected before any pool action:

- bridge health passes;
- backend readiness passes;
- operator login works;
- mining status is inactive;
- no dev fixtures;
- internal metrics require token.

Health checks:

```bash
curl -fsS http://127.0.0.1:3000/bridge/health
curl -fsS http://127.0.0.1:3001/api/health/readiness
curl -fsS -H "X-HYBA-Internal-Token: <token>" http://127.0.0.1:3000/bridge/internal/health
```

---

## 5. Operator-initiated live Stratum connection

Only after the RC and live evidence packets pass:

1. Log in as `ceo` or `mining_operator`.
2. Issue an operator-controlled mining start through the MIDAS mining control surface.
3. Confirm state transition:

```text
IDLE -> STARTING -> RUNNING
```

4. Monitor:

- connection state;
- accepted share count;
- rejected share count;
- request IDs;
- backpressure status;
- audit log emission;
- pool dashboard evidence.

Live Stratum connection alone is not a revenue claim.

---

## 6. Live share submission approval

Live share submission requires a signed launch ticket.

Set only after approval:

```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
export HYBA_LIVE_SHARE_APPROVAL_ID='<signed-launch-ticket-id>'
```

Approval owners:

- CEO / accountable operator;
- Treasury;
- Legal;
- Security;
- Operations.

The approval ticket must include:

- pool profile;
- pool account / worker identity;
- jurisdiction and tax acknowledgement;
- custody destination;
- incident rollback owner;
- monitoring owner;
- permitted runtime window;
- no-revenue-claim boundary until accepted shares are observed.

---

## 7. First four-hour live window

During the first live window, record every 15 minutes:

- local accepted shares;
- local rejected shares;
- pool-side accepted shares;
- pool-side rejected shares;
- reported hashrate;
- bridge health;
- backend readiness;
- CPU/GPU/thermal health if available;
- audit-log file size / last write time;
- operator action IDs.

Stop immediately if:

- bridge health fails repeatedly;
- backend readiness fails repeatedly;
- MIDAS validation fails;
- rejected shares exceed acceptable operator threshold;
- pool-side counts disagree materially with local counts;
- unknown state transition occurs;
- autoconnect starts without operator action;
- audit logs stop writing;
- secrets appear in logs.

---

## 8. Treasury reliance boundary

HYBA may say:

> HYBA_FULLSTACK is live-mining capable and entered controlled live mining on `<date>` with local and pool-side evidence under review.

HYBA must not say:

- guaranteed revenue;
- guaranteed hashrate;
- guaranteed solvency;
- payroll covered;
- office obligations covered;
- Foundation funding secured;
- accepted shares unless pool-side evidence confirms them.

Treasury reliance begins only after repeated live windows reconcile pool-side accepted shares, payout mechanics, custody, tax, and operating cost.

---

## 9. Evidence packet contents for Monday

For leadership/offers/office commitments, produce one folder:

```text
HYBA_FULLSTACK_COMMAND_ROOM_<date>/
├── local_production_gate_rc_<timestamp>.json
├── local_production_gate_live_<timestamp>.json
├── production_env_redacted.txt
├── approval_ticket_<id>.md
├── bridge_health.txt
├── backend_readiness.txt
├── mining_status_before_start.json
├── mining_status_after_start.json
├── pool_dashboard_screenshot_or_export.*
├── audit_log_tail.txt
└── treasury_boundary_note.md
```

This is the replacement for hosted CI in an emergency launch path.

---

## 10. Bottom line

This runbook is aggressive but controlled.

HYBA_FULLSTACK can be moved toward live mining without hosted CI, but only by replacing CI with local evidence, signed operator accountability, live-pool reconciliation, and treasury claim discipline.
