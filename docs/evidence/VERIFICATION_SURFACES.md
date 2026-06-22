# HYBA executable verification surfaces

HYBA does not ask buyers to accept extraordinary claims on presentation evidence.

HYBA exposes its claims as executable verification surfaces: property tests, adversarial tests, invariants, runtime telemetry, audit ledgers, and API-level proof endpoints.

The operating chain is:

```text
claim -> endpoint -> test -> invariant -> artifact -> reproducible run -> buyer confidence
```

The standard is deliberately precise:

```text
Every material operational claim is tied to a test, invariant, endpoint, artifact, or runtime evidence record.
```

The proof posture is therefore:

```text
Do not debate the claim.
Run the proof.
```

## API proof endpoints

| Endpoint | Purpose |
| --- | --- |
| `/api/proofs` | Index of all material proof surfaces and evidence links. |
| `/api/proofs/property-tests` | Property and contract test proof surface. |
| `/api/proofs/adversarial` | Adversarial boundary proof surface. |
| `/api/proofs/invariants` | Claim/invariant/manifest proof surface. |
| `/api/proofs/mining-readiness` | Mining readiness and share-submission proof surface. |
| `/api/proofs/autonomy` | Bounded PYTHIA autonomy proof surface. |
| `/api/proofs/memory-compression` | PULVINI memory compression/folding proof surface. |
| `/api/proofs/phi-scaling` | φ-scaling and golden-ratio proof surface. |
| `/api/proofs/security` | Security/auth/runtime-guard proof surface. |
| `/api/proofs/audit-ledger` | Cross-surface evidence ledger with digestible head hash. |
| `/api/proofs/runtime-evidence` | Runtime telemetry, local gate, and trace-evidence proof surface. |

Every named surface returns:

```json
{
  "claim": "...",
  "status": "verified | evidence_linked | runtime_required",
  "test_suite": ["tests/..."],
  "last_run": "filesystem-derived artifact timestamp or null",
  "passes": 0,
  "failures": 0,
  "invariants": ["..."],
  "artifacts": ["artifacts/...", "docs/..."] ,
  "artifact_records": [
    {
      "path": "...",
      "exists": true,
      "bytes": 1234,
      "modified_at": "...",
      "sha256": "..."
    }
  ],
  "executable_commands": ["npm run ..."],
  "ledger_digest": "sha256 over claim, endpoint, tests, invariants, artifacts, and commands"
}
```

`passes` and `failures` are conservative contract fields. A proof endpoint is not allowed to invent a fresh test result. Runtime freshness is represented by `last_run` and `artifact_records` when the referenced artifacts exist on the running filesystem. The reproducible commands tell the buyer or auditor exactly how to refresh the evidence.

## Buyer interrogation script

```bash
curl -s http://127.0.0.1:3001/api/proofs | jq '.surface_count, .claim_boundary'
curl -s http://127.0.0.1:3001/api/proofs/mining-readiness | jq
curl -s http://127.0.0.1:3001/api/proofs/adversarial | jq
curl -s http://127.0.0.1:3001/api/proofs/audit-ledger | jq '.head_hash, .surface_count'
```

## Local verification commands

```bash
npm run test:proofs
npm run test:share:e2e
npm run test:mining:doctor
npm run review:evidence:gate
npm run prod:local:gate
```

The proof endpoints are intentionally not a replacement for running the gates. They are the map from each material claim to the executable evidence that supports or bounds it.
