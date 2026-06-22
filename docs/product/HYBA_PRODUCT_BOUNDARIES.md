# HYBA Product Boundaries

**Purpose:** make the repository presentation investor-ready and regulator-safe by separating public product surfaces from private validation infrastructure.

## Public product surfaces

### QaaS — Quantum-as-a-Service

Customer-facing virtual fault-tolerant quantum-computational service.

- API surface: `/api/v1/fault-tolerant-computers`
- Implementation: `python_backend/hyba_genesis_api/api/quantum_as_a_service.py`
- Boundary: mathematical / virtual quantum-computational service on classical or substrate-agnostic hardware.
- Not a claim of physical quantum hardware advantage.

### QIaaS — Quantum Intelligence-as-a-Service

Customer-facing quantum-intelligence query surface.

- API surface: `/api/qiaas`
- Implementation: `python_backend/hyba_genesis_api/api/quantum_intelligence_service.py`
- Query families: `predict`, `explain`, `optimize`, `heal`
- Boundary: bounded quantum intelligence on the HYBA mathematical substrate.
- Not a consciousness claim.
- Not a mining product.

### CIaaS — Computational Intelligence-as-a-Service

Customer-facing provisioned computational-intelligence runtime.

- API surface: `/api/v1/computational-intelligence-services`
- Implementation: `python_backend/hyba_genesis_api/api/computational_intelligence_service.py`
- Workload families: `explain`, `orchestrate`, `counterfactual`, `governance_audit`, `substrate_health`
- Boundary: commercial intelligence runtime with tenancy, metering, fault-tolerance posture, and audit seals.
- Do not market as generic cloud Infrastructure-as-a-Service; use CIaaS or Intelligence Runtime-as-a-Service.

### PULVINI memory substrate

Reversible φ-memory working-set compression.

- Implementation: `python_backend/pythia_mining/pulvini_phi_memory.py`, `python_backend/pythia_mining/phi_folding.py`
- Boundary: active working-set reduction with retained reconstruction kernels.
- Not a claim of free storage compression without retained state.

### Salamander regeneration substrate

Self-healing / regeneration / bounded reflexive optimisation substrate.

- Boundary: software regeneration, topology repair, runtime state repair, and governed optimisation proposals.
- Not uncontrolled self-modifying source-code mutation.

## Private validation substrate

The following are private validation infrastructure and must not be presented as customer products:

- Mining workflows.
- Stratum and pool telemetry.
- Accepted-share evidence.
- Hash-search experiments.
- Pool credentials and wallet configuration.
- Mining benchmark traces.
- Internal stress tests for autonomy, PULVINI memory, QaaS/QIaaS/CIaaS resilience, and evidence sealing.

## Product narrative rule

Public-facing documents must start with:

1. QaaS
2. QIaaS
3. CIaaS
4. PULVINI
5. Salamander
6. Evidence / governance

Mining may appear only under:

- private validation,
- internal benchmark harness,
- evidence-generation substrate,
- stress-test infrastructure.

## Required claim posture

Every external claim must be classified as one of:

| Class | Meaning | External wording |
|---|---|---|
| A | Directly proven by code/tests in repo | "implemented and tested in repository" |
| B | Supported by commissioning artifact or sealed evidence | "supported by internal evidence packet" |
| C | Requires live/system evidence before commercial claim | "under validation" |
| D | Requires independent third-party validation | "research claim / not yet independently validated" |

## Forbidden investor/regulator wording until externally validated

- "Guaranteed mining revenue"
- "Physical quantum speedup"
- "Solved consciousness"
- "Solved Yang-Mills"
- "Unbounded autonomous production"
- "Production-ready for regulated financial deployment" unless security, CI, secret hygiene, evidence, DR, and governance gates are all green

## Approved chairman wording

> HYBA is a substrate-independent intelligence platform. Its public services are QaaS, QIaaS, and CIaaS. QaaS exposes virtual fault-tolerant quantum-computational primitives; QIaaS exposes bounded quantum-intelligence query functions; CIaaS provisions commercial computational-intelligence runtimes. PULVINI provides reversible φ-memory compression, Salamander provides self-healing and regeneration, and the evidence layer preserves claim boundaries. Mining is not a product; it is a private stress-test and evidence substrate used internally to validate the platform under extreme conditions.
