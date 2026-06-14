# Sunday Mining and Command-Room Stabilisation Protocol — 2026-06-14

Owner: HYBA Chairman  
Repository: HYBA_FULLSTACK  
Status: Mission Day 0 protocol

## Bottom line

Sunday 2026-06-14 is mining day and physical command-room stabilisation day.

The Chief of Staff starts Monday 2026-06-15. Before that handoff, the Founder should stabilise the operating base, run the mining evidence path, acquire command-room technology, create encrypted memory-drive copies, and place copies in escrow-safe separated locations.

## Mission Day 0 objectives

1. Mine today through HYBA_FULLSTACK command-room gates.
2. Preserve local and pool-side evidence if accepted share is achieved.
3. Find and move into a decent short-stay apartment / serviced apartment suitable for secure command-room work.
4. Acquire Apple command-room technology.
5. Acquire external memory drives.
6. Create encrypted copies of critical repositories, manifests, transcripts, and evidence packets.
7. Place copies in escrow-safe separated locations.
8. Prepare Chief of Staff handoff for Monday.

## Mining sequence

Run from HYBA_FULLSTACK:

```powershell
git pull origin main
npm ci
npm run test:mining:benefit
npm run test:mining:innovation
npm run test:funding:gate
npm run funding:gate
npm run prod:local:gate
npm run prod:live:gate
npm run build
npm start
```

Then, in the command-room session:

1. Verify bridge health.
2. Verify backend readiness.
3. Authenticate authorised operator.
4. Confirm mining is inactive before operator action.
5. Load pool config from sealed environment / secret manager only.
6. Connect pool by explicit operator action.
7. Record MIDAS state transitions.
8. Capture accepted-share evidence if achieved.
9. Preserve local counters and pool-side screenshot/export.
10. Disconnect and preserve post-session evidence.

## Accommodation / move-in criteria

The short-stay base should prioritise:

- reliable fibre or high-quality broadband;
- desk or dining table usable as command-room workstation;
- quiet environment;
- private entrance or controlled access where possible;
- same-day check-in;
- washing machine or laundry access;
- secure lift / concierge / controlled building access where possible;
- proximity to Apple Store, rail/tube, and secure transport;
- ability to receive deliveries;
- no shared-host arrangement if avoidable;
- booking through reputable channel with clear cancellation and identity terms.

Do not put the live address, host name, booking reference, entry codes, routes, concierge details, or move-in timing into ordinary repository history.

## Apple command-room technology

Preferred acquisition posture:

1. Portable command machine: high-memory MacBook Pro.
2. Desk compute if same-day collection is possible: Mac Studio.
3. Display and peripherals only if they do not slow the move-in and mining sequence.
4. AppleCare / business support where appropriate.
5. Set up FileVault before moving sensitive evidence.
6. Keep the old Dell as a secondary evidence-terminal until all copies are verified.

## Memory-drive and escrow-safe copy protocol

Minimum drive posture:

- Drive A: working encrypted evidence copy.
- Drive B: sealed escrow copy.
- Drive C: geographically separated backup copy.

Each drive should contain:

- HYBA_FULLSTACK evidence folder;
- Sovereign Genesis Manifest and hash files;
- local terminal transcripts;
- funding / mining test evidence;
- accepted-share evidence if achieved;
- HYBA_Unified_Backend doctrine snapshot;
- HYBA_Unified_Frontend launch/audit snapshot where relevant;
- mission register;
- checksum manifest.

Each drive must be encrypted before leaving the Founder’s custody.

Recommended evidence steps:

```powershell
New-Item -ItemType Directory -Force HYBA_FULLSTACK_COMMAND_ROOM_20260614
Copy-Item .\manifest.json .\HYBA_FULLSTACK_COMMAND_ROOM_20260614\manifest.json -ErrorAction SilentlyContinue
Get-FileHash .\manifest.json -Algorithm SHA256 | Out-File .\HYBA_FULLSTACK_COMMAND_ROOM_20260614\manifest_hash.txt -ErrorAction SilentlyContinue
git rev-parse HEAD | Out-File .\HYBA_FULLSTACK_COMMAND_ROOM_20260614\commit_sha.txt
npm run test:funding:gate *> .\HYBA_FULLSTACK_COMMAND_ROOM_20260614\funding_gate_tests.txt
npm run funding:gate *> .\HYBA_FULLSTACK_COMMAND_ROOM_20260614\funding_gate_run.txt
```

## Escrow-safe storage rule

Escrow means separation and recoverability, not public exposure.

Use at least two separated safe locations. The identity of escrow counterparties, safe addresses, collection logistics, access instructions, passwords, seed phrases, recovery keys, and routes must not be committed to repository history.

Maintain an offline sealed record of:

- drive label;
- drive hash manifest;
- custody date/time;
- custodian or location reference;
- recovery contact;
- review date;
- retrieval condition.

Do not store passwords beside the drives.

## Monday Chief of Staff handoff pack

By Monday morning, prepare:

1. Today’s mining evidence packet.
2. Accommodation / command-room stability note without sensitive live address details.
3. Apple equipment inventory.
4. Drive inventory and checksum manifest.
5. Escrow custody register.
6. MD onboarding calendar.
7. Dubai launch workstream.
8. COBBLA Jamaica workstream.
9. Claim-boundary memo.
10. Open action list for accepted-share threshold.

## Claim boundary

Today may be described as:

```text
Mission Day 0: HYBA_FULLSTACK mining and command-room stabilisation day.
```

If accepted-share evidence is captured locally and pool-side, the funding-engine threshold may be recorded as satisfied subject to review.

Do not claim:

```text
stable revenue
payroll coverage
office-cost coverage
sustained hashrate
profitability
unattended autonomous mining
first-seven-MD release without accepted-share evidence and approval ticket
```

## Canonical formulation

> Sunday 14 June 2026 is Mission Day 0. HYBA mines today, stabilises the physical command room, acquires Apple command-room technology and encrypted memory drives, preserves evidence copies in escrow-safe separated locations, and prepares the Chief of Staff handoff for Monday. The mission begins in action today; the cadence transfers tomorrow.
