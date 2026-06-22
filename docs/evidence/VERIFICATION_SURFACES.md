# HYBA executable verification surfaces

HYBA does not ask buyers to accept extraordinary claims on presentation evidence.

HYBA exposes platform claims as executable verification surfaces across its intelligence substrate, product APIs, governance boundaries, runtime telemetry, audit ledgers, and production gates. Mining is one surface, not the system.

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

## System boundary

HYBA_FULLSTACK is a multi-surface intelligence platform. The proof catalogue now treats mining as one domain alongside:

- platform/substrate
- intelligence fabric
- QaaS
- CIaaS
- quantum finance
- commercial access
- fair governance and claim-tiering
- Salamander/regeneration
- observability
- security
- autonomy
- PULVINI memory
- φ/golden-ratio mathematical runtime
- audit ledger
- runtime evidence

## API proof endpoints

| Endpoint | Purpose |
| --- | --- |
| `/api/proofs` | Index of all material proof surfaces, domains, and evidence links. |
| `/api/proofs/platform-overview` | Full-platform boundary: mining is one surface, not HYBA itself. |
| `/api/proofs/intelligence-fabric` | Measured intelligence health, audit, reflection, orchestration, and evidence-first surfaces. |
| `/api/proofs/qaas` | QaaS product proof surface: tenant isolation, customer keys, and metering. |
| `/api/proofs/ciaas` | CIaaS product proof surface: quota-governed computational intelligence workloads. |
| `/api/proofs/quantum-finance` | Quantum-finance API and product-boundary proof surface. |
| `/api/proofs/commercial-access` | Customer API keys, tenant isolation, quota enforcement, and metered commercial access. |
| `/api/proofs/fair-governance` | Fair buyer posture: claim tiers, limitations, governance signals, and external review workflow. |
| `/api/proofs/regeneration` | Salamander/regeneration substrate and API proof surface. |
| `/api/proofs/observability` | Health, metrics, deployment checks, runtime audit, and telemetry proof surface. |
| `/api/proofs/property-tests` | Property and contract test proof surface. |
| `/api/proofs/adversarial` | Cross-platform adversarial boundary proof surface. |
| `/api/proofs/invariants` | Claim/invariant/manifest proof surface. |
| `/api/proofs/mining-readiness` | Mining readiness and share-submission proof surface. |
| `/api/proofs/autonomy` | Bounded PYTHIA autonomy proof surface. |
| `/api/proofs/memory-compression` | PULVINI memory compression/folding proof surface. |
| `/api/proofs/phi-scaling` | φ-scaling and golden-ratio proof surface. |
| `/api/proofs/security` | Security/auth/runtime-guard/tenant-boundary proof surface. |
| `/api/proofs/audit-ledger` | Cross-surface evidence ledger with digestible head hash. |
| `/api/proofs/runtime-evidence` | Runtime telemetry, local gate, and trace-evidence proof surface. |

Every named surface returns:

```json
{
  "key": "qaas",
  "endpoint": "/api/proofs/qaas",
  "domain": "quantum_as_a_service",
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
  "ledger_digest": "sha256 over domain, claim, endpoint, tests, invariants, artifacts, and commands"
}
```

`passes` and `failures` are conservative contract fields. A proof endpoint is not allowed to invent a fresh test result. Runtime freshness is represented by `last_run` and `artifact_records` when the referenced artifacts exist on the running filesystem. The reproducible commands tell the buyer or auditor exactly how to refresh the evidence.

## Buyer interrogation script

```bash
curl -s http://127.0.0.1:3001/api/proofs | jq '.domains, .platform_boundary'
curl -s http://127.0.0.1:3001/api/proofs/platform-overview | jq
curl -s http://127.0.0.1:3001/api/proofs/intelligence-fabric | jq
curl -s http://127.0.0.1:3001/api/proofs/qaas | jq
curl -s http://127.0.0.1:3001/api/proofs/ciaas | jq
curl -s http://127.0.0.1:3001/api/proofs/commercial-access | jq
curl -s http://127.0.0.1:3001/api/proofs/mining-readiness | jq
curl -s http://127.0.0.1:3001/api/proofs/audit-ledger | jq '.head_hash, .domain_count, .surface_count'
```

## Local verification commands

```bash
npm run test:proofs
npm run test:evidence:first
npm run test:integration-fence
npm run review:evidence:gate
npm run test:share:e2e
npm run prod:local:gate
```

The proof endpoints are intentionally not a replacement for running the gates. They are the map from each material claim to the executable evidence that supports or bounds it.
