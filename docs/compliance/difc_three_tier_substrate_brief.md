# PULVINI Three-Tier Substrate: DIFC-Ready Technical Brief

## Purpose
PULVINI separates regulator-visible governance from the numerical mining kernel so an auditor can verify operational integrity without requiring access to GPUs, private research modules, or NumPy-heavy execution hosts.

## Tier 1 — Constitutional Production Façade
- Regulator-visible outputs are wrapped in `ProductionResponse` envelopes.
- Each response binds the result to a module-version hash and a concrete `CertificateLedger` entry.
- Capability manifests map façade endpoints to mathematical invariants.

## Tier 2 — Mathematical Kernel
- `KernelSupervisor` enforces PSD, Hermiticity, trace-one, Bures, purity, and deterministic replay contracts.
- Invariant failures raise `MathematicalException` and are recorded as ledger events rather than disappearing into process logs.
- `OperatorMathProvider` is the production data-plane adapter; `StaticMathProvider` is the dependency-free audit/control-plane adapter.

## Tier 3 — Research Substrate and Elevation Bridge
- `ElevationBridge` implements the air-lock: research code is promoted only after certificate-suite verification.
- Production telemetry can flow back as anonymized fixed-point samples, preserving read-only research feedback without exposing workers or operational identities.

## Regulatory Mapping
| Regulatory objective | PULVINI artifact |
| --- | --- |
| Operational resilience | Hash-chained `CertificateLedger`, manifest root hash, replayable audit CLI |
| Computational transparency | Endpoint invariant manifest, fixed-point telemetry spec |
| Algorithmic accountability | `KernelSupervisor`, `MathematicalException`, autonomic repair ledger events |
| Hype-risk control | Explicit `quantum_speedup_claimed = False` compliance field |

## Verification Workflow
1. Export the ledger using `CertificateLedger.to_bytes()`.
2. Run `scripts/pulvini_audit.py <ledger-export>` on an auditor terminal.
3. Confirm the hash chain passes and no runtime passport or mathematical exception violations are present.

## Lifecycle Artifacts
- `scripts/generate_pulvini_manifest.py` produces `manifest.json` during CI/CD so every build carries a self-documenting compliance manifest.
- `scripts/pulvini_audit.py` accepts one or more ledgers; multiple ledgers are aggregated into a consensus report for multi-node deployments.
- `public/pulvini_audit_dashboard.html` converts audit JSON into a regulator-friendly scorecard without requiring backend services.
