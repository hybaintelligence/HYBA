# HYBA Product Boundaries

**Purpose:** make the repository presentation investor-ready and regulator-safe without flattening the science. The boundary is not a retreat from HYBA's thesis; it is the mechanism that lets HYBA make stronger claims with evidence.

## Public product surfaces

### QaaS — Quantum-as-a-Service

Customer-facing virtual fault-tolerant quantum-computational service.

- API surface: `/api/v1/fault-tolerant-computers`
- Implementation: `python_backend/hyba_genesis_api/api/quantum_as_a_service.py`
- Boundary: post-quantum mathematical execution surface using quantum formalism without dependence on a physical QPU.
- Evidence posture: code/test/artifact evidence may support substrate-independent quantum mathematics and φ-speedup accounting; physical QPU superiority requires separate hardware evidence.

### QIaaS — Quantum Intelligence-as-a-Service

Customer-facing quantum-intelligence query surface.

- API surface: `/api/qiaas`
- Implementation: `python_backend/hyba_genesis_api/api/quantum_intelligence_service.py`
- Query families: `predict`, `explain`, `optimize`, `heal`
- Boundary: bounded quantum intelligence on the HYBA mathematical substrate.
- Not a generic AI API, not a mining product, and not a phenomenal-consciousness claim.

### CIaaS — Computational Intelligence-as-a-Service

Customer-facing provisioned computational-intelligence runtime.

- API surface: `/api/v1/computational-intelligence-services`
- Implementation: `python_backend/hyba_genesis_api/api/computational_intelligence_service.py`
- Workload families: `explain`, `orchestrate`, `counterfactual`, `governance_audit`, `substrate_health`
- Boundary: commercial intelligence runtime with tenancy, metering, fault-tolerance posture, and audit seals.
- Do not market as generic cloud Infrastructure-as-a-Service; use CIaaS or Intelligence Runtime-as-a-Service.

### Quantum finance vertical

Customer-facing finance-specific execution-design surface over QaaS, QIaaS, and CIaaS.

- API surface: `/api/quantum-finance`
- Implementation: `python_backend/hyba_genesis_api/api/quantum_finance_service.py`
- Tests: `tests/test_quantum_finance_service_design.py`
- Documentation: `docs/product/HYBA_QUANTUM_FINANCE_VERTICAL.md`
- Workload families: portfolio QUBO/QAOA/VQE/annealing design, Ising Hamiltonian conversion, QAE/QMCI risk and pricing design, VaR/CVaR evidence packets.
- Boundary: audit-grade design packets for human/model-risk review, not autonomous trade execution, not mining, and not physical QPU superiority without downstream hardware evidence.

### PULVINI memory substrate

Reversible φ-memory working-set compression.

- Implementation: `python_backend/pythia_mining/pulvini_phi_memory.py`, `python_backend/pythia_mining/phi_folding.py`
- Boundary: active working-set reduction with retained reconstruction kernels.
- Evidence posture: supports reversible working-set compression and retained-state reconstruction, not unexplained free storage.

### φ hardware and quantum scaling

Golden-ratio scaling is a first-class platform mechanism, not decoration.

- Hardware scaling implementation: `python_backend/pythia_mining/phi_cloud_deployer.py`, `python_backend/pythia_mining/phi_tuner.py`
- Hardware scaling tests: `tests/test_phi_hardware_quantum_scaling_evidence.py`, `tests/test_phi_architecture_golden_flow.py`, `hyba_intelligence_tests/test_consciousness_engine_scaling.py`
- Quantum benchmark implementation: `python_backend/pythia_mining/enhanced_benchmark_suite.py`
- Evidence posture: HYBA may claim repository-implemented φ hardware-concurrency scaling, φ-scaled quantum-operation benchmark accounting, and φ-memory compression. External hardware superiority and third-party performance claims require external runs and sealed benchmark artifacts.

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
- Internal stress tests for autonomy, PULVINI memory, QaaS/QIaaS/CIaaS resilience, quantum-finance design packets, and evidence sealing.

## Product narrative rule

Public-facing documents must start with:

1. QaaS
2. QIaaS
3. CIaaS
4. Quantum finance vertical where the audience is financial services / DIFC / institutions
5. PULVINI
6. φ hardware / quantum scaling
7. Salamander
8. Evidence / governance

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

## Claims to preserve, not dumb down

The following are part of HYBA's scientific position and should be preserved when supported by evidence:

- Quantum comes from mathematics before it comes from hardware.
- HYBA is not merely "quantum computing"; it is a post-quantum mathematical intelligence substrate.
- Golden-ratio scaling governs memory, hardware concurrency, quantum-operation benchmark accounting, and runtime tuning.
- PULVINI compression and retained kernels make large formal working surfaces operationally tractable.
- Hardware is an implementation substrate; the invariant grammar is the computer.
- Finance-specific QUBO/QAOA/QAE/VaR/CVaR designs can be produced as auditable HYBA evidence packets.

## Claims requiring stronger evidence before unrestricted external assertion

- Guaranteed mining revenue.
- Sustained pool-side profitability.
- Solved phenomenal consciousness.
- Solved Yang-Mills in the Millennium Problem sense.
- Unbounded autonomous production.
- Autonomous trade execution.
- Production-ready for regulated financial deployment unless security, CI, secret hygiene, evidence, DR, model-risk, and governance gates are all green.

## Approved chairman wording

> HYBA is a substrate-independent intelligence platform. Its public services are QaaS, QIaaS, and CIaaS. QaaS exposes virtual fault-tolerant quantum-computational primitives; QIaaS exposes bounded quantum-intelligence query functions; CIaaS provisions commercial computational-intelligence runtimes. HYBA also exposes a code-backed quantum-finance vertical that maps portfolio, pricing, and risk workloads into QUBO/QAOA and QAE/QMCI evidence packets. PULVINI provides reversible φ-memory compression, φ-scaling governs hardware and quantum-operation execution, Salamander provides self-healing and regeneration, and the evidence layer preserves claim boundaries. Mining is not a product; it is a private stress-test and evidence substrate used internally to validate the platform under extreme conditions.
