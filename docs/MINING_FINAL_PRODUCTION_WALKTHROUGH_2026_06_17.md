# HYBA Mining Final Production Walkthrough — 2026-06-17

## BLUF

The mining system is ready for a controlled command-room cutover **only if** the production-readiness doctor and the autonomous-sovereign gate both pass in the same environment that will run mining.

This is not a blanket, unqualified GO for live share submission. Live share submission remains separately gated by `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true` and `HYBA_LIVE_SHARE_APPROVAL_ID`.

## End-to-end contract chain

```text
operator env / secrets
  -> pool profile loader
  -> Stratum client connect
  -> subscribe / authorize
  -> mining.notify job receipt
  -> UnifiedMiningEngine.search(job)
  -> PULVINI / phi-compressed nonce planning
  -> candidate nonce
  -> local Bitcoin SHA-256d target validation
  -> StratumClient.submit_validated_share(job, nonce)
  -> pool ACK accepted/rejected
  -> engine.on_share_result(...)
  -> metrics / audit / readiness evidence
```

## Hard production invariants

1. Production/live mode never injects development fixture jobs.
2. Live candidate generation must call `UnifiedMiningEngine.search(job)` with a real pool job.
3. A candidate must pass local Bitcoin SHA-256d target validation before pool submission.
4. Accepted-share counters must increment only after explicit pool ACK.
5. Stale jobs and malformed pool responses must not be counted as accepted.
6. Live share submission requires `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true` and `HYBA_LIVE_SHARE_APPROVAL_ID`.
7. Autonomous mining requires explicit operator authorisation, bounded runtime limits, audit logging, and no dev fixtures.
8. No wallet/pool/credential change is autonomous without human authority.

## Autonomous action contract

Autonomous functions may optimise search strategy or hashrate within mathematical and operator bounds, but they do not own production authority. Before live autonomous mining:

```bash
NODE_ENV=production
HYBA_ENV=production
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_AUDIT_LOGGING=true
HYBA_ENABLE_AUTONOMOUS_MINING=true
HYBA_AUTONOMOUS_OPERATOR_APPROVAL_ID=<approval-id>
HYBA_AUTONOMOUS_OPERATOR=<human-operator>
HYBA_AUTONOMOUS_OPERATOR_REASON=<why-autonomy-is-authorised>
HYBA_AUTONOMOUS_MAX_HASHRATE_EHS=100
HYBA_AUTONOMOUS_MAX_POWER_WATTS=500
HYBA_AUTONOMOUS_MIN_PHI_COHERENCE=0.70
```

Live share submission remains separate:

```bash
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false  # until CEO/treasury/legal release
# when release is approved:
HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
HYBA_LIVE_SHARE_APPROVAL_ID=<separate-share-submit-approval-id>
```

## Required gates

Run these before any controlled mining cutover:

```bash
PYTHONPATH=python_backend python scripts/mining_production_readiness_doctor.py --mode live --write
PYTHONPATH=python_backend python scripts/mining_autonomous_sovereign_gate.py --mode live --write
```

Run focused regression tests:

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_phi_unified_mining_engine.py \
  tests/test_unified_mining_api_surface.py \
  tests/test_stratum_share_acceptance_e2e.py \
  tests/test_pulvini_nonce_compression.py \
  tests/test_mining_production_readiness_doctor.py \
  tests/test_mining_autonomous_sovereign_gate.py \
  -q
```

## GO / NO-GO rule

### GO for controlled command-room live connect/search

Allowed when:

- mining production-readiness doctor returns no critical failures;
- autonomous-sovereign gate returns `GO`;
- at least one live pool profile is configured from secrets/env;
- audit logging is on;
- dev fixtures are off;
- live Stratum is on;
- operator approval ID, operator, and operator reason are attached;
- command-room observer is watching pool connection, authorisation, job receipt, search, validation, and submit gate state.

### GO for live share submission

Allowed only when all of the above are true **and**:

- `HYBA_ENABLE_LIVE_SHARE_SUBMIT=true`;
- `HYBA_LIVE_SHARE_APPROVAL_ID` is set;
- CEO / treasury / legal / operations release is recorded externally;
- the first accepted/rejected share is inspected for local validation path and pool ACK path.

### NO-GO

No live cutover if any of these occur:

- doctor critical failure;
- autonomous-sovereign gate `NO_GO`;
- missing pool credentials;
- missing audit logging;
- dev fixtures enabled;
- no live Stratum;
- no operator approval ID for autonomy;
- live share submit enabled without separate share-submit approval ID;
- accepted-share counter increments without pool ACK evidence.

## First-hour command-room observations

Watch and record:

1. pool profile selected;
2. subscribe success;
3. authorize success;
4. `mining.notify` received;
5. no dev fixture injection;
6. `UnifiedMiningEngine.search(job)` invoked;
7. PULVINI compressed nonce plan metrics present;
8. local SHA-256d target validation result;
9. live submit gate state;
10. pool ACK accepted/rejected result;
11. audit log entry for every transition;
12. no credential leak in logs/status surfaces.

## Hiring-day handoff

Chief of Staff owns:

- approval IDs;
- command-room checklist;
- pool credential custody;
- live share-submit release process;
- external record of CEO/treasury/legal/ops signoff.

Engineering Director owns:

- doctor and autonomous-gate execution;
- runtime logs;
- first-hour incident response;
- rollback to `HYBA_ENABLE_LIVE_SHARE_SUBMIT=false`;
- post-cutover artifact pack.

## Final statement

The codebase has a production-shaped mining pathway and explicit readiness gates. The correct signoff is:

> GO for controlled command-room live mining cutover after both gates pass in the real production environment. NO-GO for live share submission until the separate share-submit approval ID is attached and observed.
