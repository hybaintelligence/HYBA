# HYBA executable verification windows

HYBA does not ask buyers to accept extraordinary claims on presentation evidence.

HYBA_FULLSTACK is **one non-severable platform**. The proof endpoints are not a product catalogue and they are not detachable modules. They are interrogation windows into the same integrated intelligence operating substrate.

HYBA exposes this one platform through executable verification windows: property tests, adversarial tests, invariants, runtime telemetry, audit ledgers, product API checks, governance boundaries, and production gates.

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

## Platform unity

The correct model is not:

```text
HYBA = mining product + QaaS product + CIaaS product + governance product + observability product
```

The correct model is:

```text
HYBA_FULLSTACK = one integrated platform substrate

/api/proofs/* = verification windows into that same substrate
```

The windows currently expose evidence for these platform dimensions:

- platform/substrate
- intelligence fabric
- QaaS execution
- CIaaS execution
- quantum finance
- commercial access
- fair governance and claim-tiering
- Salamander/regeneration
- observability
- verification/property/adversarial/invariant testing
- mining readiness
- autonomy
- PULVINI memory
- φ/golden-ratio mathematical runtime
- security
- audit ledger
- runtime evidence

Mining is therefore neither ignored nor centred. It is one operational dimension inside HYBA_FULLSTACK.

## API proof endpoints

| Endpoint | Purpose |
| --- | --- |
| `/api/proofs` | Index of all material verification windows, dimensions, unity metadata, and evidence links. |
| `/api/proofs/platform-overview` | One-platform boundary: every window maps back to HYBA_FULLSTACK. |
| `/api/proofs/intelligence-fabric` | Measured intelligence health, audit, reflection, orchestration, and evidence-first checks. |
| `/api/proofs/qaas` | QaaS execution window: tenant isolation, customer keys, and metering. |
| `/api/proofs/ciaas` | CIaaS execution window: quota-governed computational intelligence workloads. |
| `/api/proofs/quantum-finance` | Quantum-finance API and product-boundary verification window. |
| `/api/proofs/commercial-access` | Customer API keys, tenant isolation, quota enforcement, and metered access. |
| `/api/proofs/fair-governance` | Fair buyer posture: claim tiers, limitations, governance signals, and external review workflow. |
| `/api/proofs/regeneration` | Salamander/regeneration substrate and API verification window. |
| `/api/proofs/observability` | Health, metrics, deployment checks, runtime audit, and telemetry. |
| `/api/proofs/property-tests` | Property and contract test verification window. |
| `/api/proofs/adversarial` | Cross-platform adversarial boundary verification window. |
| `/api/proofs/invariants` | Claim/invariant/manifest verification window. |
| `/api/proofs/mining-readiness` | Mining readiness and share-submission verification window. |
| `/api/proofs/autonomy` | Bounded PYTHIA autonomy verification window. |
| `/api/proofs/memory-compression` | PULVINI memory compression/folding verification window. |
| `/api/proofs/phi-scaling` | φ-scaling and golden-ratio verification window. |
| `/api/proofs/security` | Security/auth/runtime-guard/tenant-boundary verification window. |
| `/api/proofs/audit-ledger` | Cross-window evidence ledger with digestible head hash. |
| `/api/proofs/runtime-evidence` | Runtime telemetry, local gate, and trace-evidence verification window. |

Every named verification window returns:

```json
{
  "key": "qaas",
  "endpoint": "/api/proofs/qaas",
  "domain": "quantum_as_a_service",
  "platform_unity": {
    "name": "HYBA_FULLSTACK",
    "unity": "one_non_severable_platform",
    "substrate": "integrated_intelligence_operating_substrate",
    "severability": "not_severable"
  },
  "projection_rule": "This record isolates one verification dimension for interrogation while remaining bound to the same HYBA_FULLSTACK platform substrate.",
  "claim": "...",
  "status": "verified | evidence_linked | runtime_required",
  "test_suite": ["tests/..."],
  "last_run": "filesystem-derived artifact timestamp or null",
  "passes": 0,
  "failures": 0,
  "invariants": ["..."],
  "artifacts": ["artifacts/...", "docs/..."],
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
  "ledger_digest": "sha256 over platform unity, domain, claim, endpoint, tests, invariants, artifacts, and commands"
}
```

`passes` and `failures` are conservative contract fields. A proof endpoint is not allowed to invent a fresh test result. Runtime freshness is represented by `last_run` and `artifact_records` when the referenced artifacts exist on the running filesystem. The reproducible commands tell the buyer or auditor exactly how to refresh the evidence.

## Buyer interrogation script

```bash
curl -s http://127.0.0.1:3001/api/proofs | jq '.platform_identity, .platform_boundary, .domains'
curl -s http://127.0.0.1:3001/api/proofs/platform-overview | jq
curl -s http://127.0.0.1:3001/api/proofs/intelligence-fabric | jq
curl -s http://127.0.0.1:3001/api/proofs/qaas | jq
curl -s http://127.0.0.1:3001/api/proofs/ciaas | jq
curl -s http://127.0.0.1:3001/api/proofs/commercial-access | jq
curl -s http://127.0.0.1:3001/api/proofs/mining-readiness | jq
curl -s http://127.0.0.1:3001/api/proofs/audit-ledger | jq '.head_hash, .platform_identity, .domain_count, .surface_count'
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

The proof endpoints are intentionally not a replacement for running the gates. They are the map from each material claim to the executable evidence that supports or bounds it while preserving HYBA_FULLSTACK as one platform.
