# HYBA_FULLSTACK Funding Engine Deployment and MD Offer Gate

Current as of: 2026-06-13  
Owner: HYBA Chairman / HYBA Group Command Room  
Status: Canonical funding-engine deployment gate

## Bottom line

HYBA_FULLSTACK is the separate funding-engine repository.

It is intentionally separated from the broader HYBA_Unified_Backend / HYBA_Unified_Frontend estate so that treasury-supporting mining, command-room deployment evidence, and accepted-share gates can be governed as their own operational rail.

HYBA_FULLSTACK does not replace METIS. It is the self-financing production expression of the METIS doctrine.

The mining innovation and expected-benefit map is maintained at:

```text
docs/MINING_INNOVATIONS_AND_CAPABILITY_MAP.md
```

That document links the funding engine's innovations to property tests and capability boundaries.

## Deployment doctrine

The funding engine is deployed only through evidence gates.

The required sequence is:

```text
1. Local production gate passes.
2. Phi^15 empirical evidence artifacts are present and schema-valid.
3. Deterministic PYTHIA search repeatability is proven.
4. Production server starts in production mode.
5. Bridge and backend readiness return HTTP 200.
6. Operator login is authenticated with authorised role.
7. Mining is inactive before operator action.
8. Pool configuration is loaded from sealed environment or secret manager.
9. Operator explicitly connects the selected pool.
10. MIDAS transitions are valid with zero invalid transitions.
11. Accepted-share evidence is captured from local counters and pool-side export.
12. Only then may the MD-offer trigger be marked satisfied.
```

## Empirical evidence gate

The funding engine must be built around HYBA's empirical evidence, not disconnected telemetry.

The Phi^15 empirical evidence lane is expected at:

```text
artifacts/phi_resonance/phi_resonance_blocks.csv
artifacts/phi_resonance/phi_resonance_summary.json
```

The CSV must contain `resonance_strength` per block.

The JSON summary must contain:

```text
mean_resonance_strength
resonance_above_05_count
resonance_above_05_rate
```

The funding gate validates that the JSON summary agrees with the CSV within tolerance. This prevents the funding engine from relying on unverified or manually edited summaries.

## Deterministic search gate

HYBA_FULLSTACK search must be deterministic.

For the same mining target and nonce range, PYTHIA must return the same nonce on repeated runs. The deployment gate runs the solver twice against the same target/range and fails if the nonce differs or falls outside the requested range.

This does not claim pool acceptance. It proves local deterministic search repeatability before live mining reliance.

The mining innovation property tests expand this gate by checking range-safety, invalid-range failure, PULVINI capacity caps, projection-vs-measured benchmark boundaries, phi-weight normalisation, and bounded resonance telemetry.

Run the capability property suite with:

```bash
npm run test:mining:innovation
```

## Accepted-share gate

The first accepted share is the funding-engine threshold event.

Before that event, HYBA_FULLSTACK may be described as:

```text
controlled production rehearsal and live-Stratum connection ready
```

After at least one accepted share is evidenced locally and pool-side, HYBA_FULLSTACK may be described as:

```text
funding engine accepted-share evidence captured
```

No payroll, office-cost, revenue, or stable-hashrate reliance may be made until accepted-share evidence exists and has been reviewed.

## MD offer trigger

The first seven MD offers may be released only when the following are true:

1. `npm run prod:local:gate` has passed or equivalent local evidence packet exists.
2. `npm run funding:gate` has passed.
3. Live mining was started by an authorised operator, not autoconnect.
4. MIDAS state history shows valid transitions and zero invalid transitions.
5. At least one accepted share is evidenced by local counters.
6. Pool-side accepted/rejected share evidence is captured by screenshot or export.
7. CEO / Treasury / Legal / Security / Operations approval ticket exists.
8. Credentials used during the session have not been committed and are rotated if exposed.

The Chief of Staff MD may begin immediately as command-room owner if the Chairman approves, because that role is required to run the evidence room, offer sequencing, and MD onboarding cadence. However, the first seven MD offers as a funding-dependent event remain gated by accepted-share evidence unless the Chairman explicitly overrides the funding dependency in writing.

## Commands

Pre-share funding-engine gate:

```bash
npm run funding:gate
```

Accepted-share-required gate:

```bash
npm run funding:accepted-share:gate
```

The accepted-share gate writes a runtime evidence packet under:

```text
artifacts/funding_engine/
```

That folder is ignored by Git because it may contain local deployment metadata. Preserve the packet in the command-room evidence folder, not in the public repo history.

## Claim boundary

Allowed before accepted share:

```text
HYBA_FULLSTACK is deployment-ready for signed live-pool evidence capture and has deterministic empirical-search gates in place.
```

Allowed after accepted share and pool-side evidence:

```text
HYBA_FULLSTACK has captured first accepted-share funding-engine evidence and may proceed to MD-offer release under the signed command-room approval ticket.
```

Not allowed without further evidence:

```text
stable revenue
payroll coverage
office-cost coverage
sustained hashrate
profitability
unattended autonomous mining
```

## Canonical formulation

Use this wording in command-room notes:

> HYBA_FULLSTACK is HYBA's separate funding-engine repository. Deployment is governed by local production evidence, Phi^15 empirical evidence artifacts, deterministic PYTHIA search repeatability, MIDAS state integrity, and accepted-share proof. The first seven MD offers are released when the first accepted share is evidenced locally and pool-side, subject to signed CEO, Treasury, Legal, Security, and Operations approval.
