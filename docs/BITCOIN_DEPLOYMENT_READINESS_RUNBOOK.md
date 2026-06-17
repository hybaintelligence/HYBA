# HYBA_FULLSTACK Bitcoin Deployment Readiness Runbook

**BLUF:** Bitcoin deployment readiness is not the same thing as frontier/adaptive-science completeness. `npm run prod:local:gate` and `npm run prod:bitcoin:gate` now validate the bounded Bitcoin operational path: evidence boundaries, runtime safety, mining control loop, Stratum/share handling, pool-profile readiness, build integrity, backend tests, and deployment tests.

This gate does **not** claim guaranteed revenue, pool-confirmed hashrate, accepted-share economics, SHA-256 quantum acceleration, or treasury readiness. Live share submission remains disabled until an operator deliberately enables it with approvals and pool-side evidence capture.

## Fast command path

From a clean checkout:

```bash
npm ci
python -m pip install -r python_backend/requirements.txt
npm run prod:bitcoin:gate
```

`npm run prod:local:gate` is an alias-level release-candidate gate and follows the same Bitcoin production path.

## What the Bitcoin gate proves

The Bitcoin deployment gate proves the repository can pass the bounded operational checks needed before controlled Bitcoin/Stratum deployment:

1. Nodus Solutus proof doctrine is present and bounded.
2. Claim/evidence manifest and merge-conflict guards pass.
3. Runtime entrypoint and mining API surface are present.
4. Runtime mock/static telemetry guards pass.
5. Evidence-first intelligence endpoint tests pass.
6. HENDRIX-Φ, unified mining engine, unified API, Stratum share E2E, pool-profile readiness, and mining-doctor tests pass.
7. PULVINI and φ golden-flow production invariants pass.
8. Funding gate runs without accepted-share/revenue overclaim.
9. TypeScript, production build, backend, e2e, and deployment tests pass.
10. A timestamped evidence packet is written under `artifacts/production_readiness/` with SHA-256 sealing.

## What moved out of the deploy blocker path

The following remain important research/elevation evidence but no longer block the Bitcoin RC cutover gate:

- broad `test:adaptive:science` bundle;
- `elevation:full` bundle;
- frontier experiment aggregation;
- post-quantum benchmark evidence beyond production invariant coverage.

Run those with:

```bash
npm run prod:research:gate
npm run prod:command-room:gate:full-forensic
```

## Live activation boundary

Passing the Bitcoin gate permits **release-candidate deployment preparation**, not live share submission.

Before live shares:

```bash
npm run prod:live:gate
```

Required operator controls:

- `HYBA_ENABLE_LIVE_STRATUM=true` only for intentional live pool IO;
- `HYBA_ENABLE_MINING_AUTOCONNECT=false` unless intentionally enabled;
- `HYBA_ENABLE_LIVE_SHARE_SUBMIT=false` until explicit approval;
- `HYBA_LIVE_SHARE_APPROVAL_ID` must reference attached approval evidence;
- pool-side accepted/rejected share evidence must be archived before revenue or economics claims.

## First failure rule

If `prod:bitcoin:gate` fails, stop. Fix the first failed step, rerun from a clean terminal, and preserve the new JSON evidence packet.
