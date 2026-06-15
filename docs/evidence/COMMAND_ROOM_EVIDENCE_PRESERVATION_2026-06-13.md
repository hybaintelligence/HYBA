# HYBA_FULLSTACK Command-Room Evidence Preservation — 2026-06-13

Current as of: 2026-06-13  
Owner: HYBA Group Command Room  
Status: Local evidence preserved; dashboard handoff ready under claim boundaries

## Decision

The local command-room evidence preservation sequence has been completed for the Sovereign Genesis Manifest and related HYBA_FULLSTACK funding-engine readiness artifacts.

This record is based on operator-reported local command-room evidence from the Windows HYBA_FULLSTACK machine. The runtime artifacts remain local evidence and are not committed to repository history.

## Local evidence folder

```text
HYBA_FULLSTACK_COMMAND_ROOM_20260613/
```

Preserved artifacts reported by the operator:

```text
manifest.json
manifest_hash.txt
commit_sha.txt
terminal_transcript.txt
EVIDENCE_INDEX.md
```

## Local artifact chain

The operator reported the following provenance chain:

| Field | Value |
| --- | --- |
| Local command-room folder | `HYBA_FULLSTACK_COMMAND_ROOM_20260613/` |
| Preserved manifest file | `manifest.json` |
| Local file SHA-256 prefix | `948BA2935F24...514B770F` |
| Git commit captured locally | `fadacac25ca09b969947750a41f9732db3ef4919` |
| Dashboard handoff documentation commit | `a57d507` |
| Machine ID | `f7a59311afd6da8bb196bfa244de3fba17a9be1559460dc69f10b98241d5ab65` |

## Constitutional signatures recorded in manifest

The operator reported the manifest-level constitutional signatures as:

| Signature | Value |
| --- | --- |
| Manifest Hash | `14e09ee502d5ea5f0fa2214e4ba7f12a56dba5bc15c411000b27f75b75880f59` |
| Certificate Ledger Root | `447e8b8852664bc72dbeb40b93577fbdc612e48d1f246a160adb84050557dfd5` |
| Runtime Manifest Hash | `b149e9c5a123978d3d224b9d34ba2c7964ecc69cc1ca93073705462a5a32d370` |

## Evidence distinction

This record distinguishes between:

1. **Local file hash** — the SHA-256 hash of the preserved `manifest.json` artifact on the command-room machine.
2. **Manifest-level constitutional hashes** — hashes contained inside the manifest payload, including the manifest hash, certificate ledger root, and runtime manifest hash.
3. **Repository documentation commits** — Git commits that describe the evidence posture and dashboard handoff boundaries.

This distinction matters because a file hash can change if formatting, envelope, or serialization changes, while internal manifest hashes represent the constitutional content sealed by the generator.

## Dashboard handoff status

Dashboard render may proceed under the previously recorded claim boundaries.

Allowed dashboard claims:

```text
Sovereign Genesis Manifest generated locally against production PULVINI runtime.
Manifest-backed dashboard handoff ready.
Dynamic phi-exponential scaling contract present.
Certificate ledger root present.
Runtime manifest hash present.
Fixed-point telemetry contract present.
Production facade boundary present.
No quantum-speedup claim boundary present.
```

Not allowed from this evidence alone:

```text
accepted shares
stable hashrate
revenue
profitability
payroll coverage
office-cost coverage
unattended autonomous mining
quantum speedup over SHA-256
proof-of-work bypass
guaranteed mining advantage
external regulatory certification
```

## Required next evidence for funding event

The next threshold is not another manifest run. The next threshold is live accepted-share evidence.

Before the first seven MD offers are released as a funding-dependent event, the command room must preserve:

1. pre-session bridge/backend health;
2. authenticated operator login;
3. inactive mining state before explicit operator action;
4. sealed pool configuration with no committed secrets;
5. explicit pool connection action;
6. MIDAS transition history with zero invalid transitions;
7. local accepted-share counter greater than zero;
8. pool-side accepted/rejected share export or screenshot;
9. post-session disconnect evidence;
10. CEO / Treasury / Legal / Security / Operations approval ticket.

## Canonical formulation

Use this wording in command-room, dashboard, and MD-readiness notes:

> The Sovereign Genesis Manifest has been generated, hashed, indexed, and preserved in the local HYBA_FULLSTACK command-room evidence folder. The dashboard may now render manifest-backed PULVINI/PYTHIA capability facts under claim-boundary enforcement. This is a dashboard handoff and constitutional-runtime evidence event, not yet an accepted-share, revenue, payroll, office-cost, or first-seven-MD offer release event.
