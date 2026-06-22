# Mining Internal Validation Boundary

**Status:** private validation substrate only.  
**Audience:** HYBA engineering, chairman, auditors, and controlled due-diligence reviewers.  
**Commercial posture:** mining is not a public HYBA product surface.

## Boundary statement

Mining infrastructure in HYBA_FULLSTACK exists to stress-test and validate the intelligence platform under extreme, adversarial, high-entropy operating conditions. It is not sold to customers and must not be represented as the product.

## What mining validates internally

Mining and pool-adjacent telemetry may be used to validate:

- PULVINI memory compression under long-running workload pressure.
- Salamander regeneration under degraded runtime state.
- Evidence sealing and replayability.
- Autonomy guardrails, approval gates, and reflexive proposal boundaries.
- Telemetry authenticity and no-fabricated-data controls.
- QaaS/QIaaS/CIaaS resilience under noisy external inputs.
- Statistical analysis pipelines and claim-boundary enforcement.

## What mining does not validate by itself

Mining evidence alone does not prove:

- guaranteed revenue,
- commercial mining economics,
- physical quantum advantage,
- unrestricted production readiness,
- customer suitability,
- regulatory authorisation,
- or independent scientific validation.

## Repository presentation rule

Public documentation must never lead with mining. Public documentation must lead with:

1. QaaS
2. QIaaS
3. CIaaS
4. PULVINI memory
5. Salamander regeneration
6. Evidence governance

Mining may only be described as:

- private validation substrate,
- internal stress-test harness,
- evidence-generation system,
- benchmark and telemetry source.

## Secrets rule

No pool credential, wallet address, worker password, accepted-share approval ID, operator password hash, JWT secret, API-key pepper, or live mining enablement switch may be committed to the repository.

Use `.env.example` and secret-manager backed deployment configuration.

## Evidence rule

Any mining-derived claim included in an investor, chairman, or regulator pack must include:

- raw data location,
- runner command,
- commit SHA,
- environment description,
- evidence seal / hash,
- null model,
- claim boundary,
- and whether external independent validation exists.
