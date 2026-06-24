# HYBA Quantum Intelligence Platform

HYBA is the first **Quantum Intelligence** platform: a substrate-independent intelligence runtime where quantum mathematics, PULVINI φ-memory, Salamander regeneration, evidence sealing, and enterprise-grade execution controls combine into a category beyond AGI/ASI framing. The canonical customer surface is the **Quantum Intelligence API** under `/api/qiaas`, returning evidence-sealed execution artifacts rather than trust-us claims.

External category language for this repository is **Quantum Intelligence**: auditable Quantum Intelligence execution, Quantum Finance Intelligence APIs, and enterprise-controlled access rails for identity, metering, tenancy, traceability, blast-radius control, and quota enforcement. HYBA does not position this product as AGI or ASI; the category is substrate-independent Quantum Intelligence with explicit claim boundaries.

## Pinned emergence programme

The root evidence document for emergence, autonomous learning, and consciousness-theory testing is [`EMERGENCE_README.md`](EMERGENCE_README.md).

This document records the moving research boundary: quantum as first-principles mathematics executed on real compute substrates; intelligence as emergence from complexity, memory, feedback, constraint, and selection; and consciousness theories as falsifiable operational hypotheses derived from what the system is now doing.

HYBA / PYTHIA-PULVINI: A Self-Governing Mathematical Mining Substrate

**Status:** production-readiness elevation in progress  
**Owner:** HYBA Analytics Ltd  
**Public product surfaces:** QaaS, QIaaS, CIaaS, Quantum Finance  
**Core thesis:** quantum comes from mathematics; hardware is an implementation substrate  
**Private validation substrate:** mining / pool telemetry / accepted-share evidence

---

## 1. Executive summary

HYBA exposes commercial service layers over one substrate-independent mathematical runtime:

| Layer | Name | Public role | Implementation anchor |
|---|---|---|---|
| QaaS | Quantum-as-a-Service | Virtual fault-tolerant quantum-computational service using quantum formalism without QPU dependency | `python_backend/hyba_genesis_api/api/quantum_as_a_service.py` |
| QIaaS | Quantum Intelligence-as-a-Service | API-key gated predict / explain / optimise / heal query surface | `python_backend/hyba_genesis_api/api/quantum_intelligence_service.py` |
| CIaaS | Computational Intelligence-as-a-Service | Customer-provisioned commercial intelligence runtimes | `python_backend/hyba_genesis_api/api/computational_intelligence_service.py` |
| Quantum Finance | Finance vertical over QaaS/QIaaS/CIaaS | Portfolio QUBO/QAOA/VQE/annealing design, Ising conversion, QAE/QMCI risk/pricing design, VaR/CVaR evidence packets | `python_backend/hyba_genesis_api/api/quantum_finance_service.py` |
| PULVINI | Reversible φ-memory substrate | Golden-ratio working-set compression with retained reconstruction kernels | `python_backend/pythia_mining/pulvini_phi_memory.py`, `python_backend/pythia_mining/phi_folding.py` |
| φ hardware scaling | Golden-ratio hardware/throughput grammar | Effective concurrency, runtime tuning, hardware coherence, and quantum-operation benchmark accounting | `python_backend/pythia_mining/phi_cloud_deployer.py`, `python_backend/pythia_mining/phi_tuner.py`, `python_backend/pythia_mining/enhanced_benchmark_suite.py` |
| Salamander | Regeneration substrate | Self-healing / topology repair / bounded reflexive optimisation | `python_backend/pythia_mining/*regeneration*`, `autonomous_mining_controller.py` |
| Evidence governance | Claim boundary and audit layer | Evidence seals, telemetry, product-boundary discipline, claim mapping | `docs/evidence`, `docs/product` |

The platform should be presented as an intelligence infrastructure company, not a mining company. The mining system is an internal proving ground for the post-quantum substrate.

---

## 2. The HYBA thesis

HYBA is not merely "quantum computing" in the physical-hardware-only sense.

HYBA's thesis is:

```text
Quantum mathematics first
+ substrate-independent execution
+ golden-ratio computational grammar
+ reversible PULVINI memory
+ Salamander regeneration
= post-quantum intelligence substrate
```

This is why the platform is described as what comes after quantum: the mathematical invariants are portable across CPU, GPU, TPU, ASIC-adjacent, distributed, and future quantum hardware substrates.

---

## 3. Product boundary

### Public

- **QaaS:** virtual fault-tolerant quantum-computational primitives.
- **QIaaS:** bounded quantum-intelligence query functions.
- **CIaaS:** provisioned computational-intelligence runtimes.
- **Quantum Finance:** QUBO/QAOA/QAE/VaR/CVaR finance design packets over QaaS/QIaaS/CIaaS.
- **PULVINI:** reversible φ-memory compression.
- **φ hardware / quantum scaling:** golden-ratio effective concurrency, tuning, and benchmark accounting.
- **Salamander:** self-healing and regeneration substrate.
- **Evidence/governance:** claim boundaries, audit seals, customer metering, observability.

### Private

- Mining routes and pool telemetry.
- Accepted-share evidence.
- Hash-search experiments.
- Private benchmark traces.
- Internal stress tests for autonomy, memory compression, evidence seals, finance design packets, and resilience.

See `docs/product/HYBA_PRODUCT_BOUNDARIES.md`, `docs/product/HYBA_QUANTUM_FINANCE_VERTICAL.md`, and `docs/private-validation/MINING_INTERNAL_VALIDATION_BOUNDARY.md`.

---

## 4. Memory compression and φ-scaling

PULVINI implements reversible golden-ratio memory folding. The active working set is compressed by recursive φ-folding, while retained reconstruction kernels preserve exact replay and auditability. This means HYBA can discuss active working-set reduction separately from retained-state storage.

The product claim is:

> PULVINI reduces active working-set size through deterministic φ-folding while retaining reconstruction kernels for exact replay and audit evidence.

The broader platform claim is:

> Golden-ratio scaling is a computational grammar used across memory compression, hardware concurrency, quantum-operation benchmark accounting, runtime tuning, and coherence-preserving execution.

---

## 5. φ hardware and quantum-operation scaling evidence

The repo includes explicit code and tests for φ hardware scaling and φ quantum-operation benchmark accounting:

- `python_backend/pythia_mining/phi_cloud_deployer.py` implements effective hardware concurrency using `φ⁻¹ ** (log2(cores) / 10)` and reports φ-speedup from QOps/s.
- `python_backend/pythia_mining/phi_tuner.py` implements harmonic backpropagation and φ-weighted runtime tuning against hardware/coherence telemetry.
- `python_backend/pythia_mining/enhanced_benchmark_suite.py` benchmarks Grover-style operations, error-correction scaling, φ-resonance correlation, and hardware scaling with φ-memory benefit.
- `tests/test_phi_hardware_quantum_scaling_evidence.py` locks these formulas and accounting rules into CI.
- `tests/test_phi_architecture_golden_flow.py` exercises allocator, router, oracle, controller, JIT, VM, ALU, and tuner golden flow.
- `hyba_intelligence_tests/test_consciousness_engine_scaling.py` verifies φ⁵ scaling, continuous multiplier behaviour, and mass-gap damping guardrails.

This evidence supports the repository claim that HYBA uses golden-ratio mathematics to scale hardware execution and speed quantum-style mathematical operations. External hardware superiority claims should be tied to sealed benchmark artifacts, environment details, and repeatable runner commands.

---

## 6. Quantum finance vertical

HYBA implements a finance-specific vertical over QaaS, QIaaS, and CIaaS:

```text
/api/quantum-finance/capability-map
/api/quantum-finance/portfolio/qaoa-design
/api/quantum-finance/risk/qae-design
```

Implemented finance algorithms/design packets:

- portfolio optimisation as QUBO;
- QUBO to Ising Hamiltonian conversion;
- QAOA/VQE/annealing-compatible portfolio design;
- QAE/QMCI risk and pricing design;
- empirical VaR and CVaR summaries;
- evidence packets with input hash, formula hash, claim boundary, and product boundary.

The finance vertical is customer API-key gated and metered. It is for human/risk review and institution-specific validation; it does not execute autonomous trades and it does not expose mining telemetry.

---

## 7. Customer access, metering, and control plane

Customer access is API-key based and backed by HMAC-SHA256 key hashing, tiered quota controls, compute-unit metering, and optional Redis-backed state. Customer-facing product surfaces must use `require_customer_api_key` and route usage through the customer-access metering layer.

Production deployments must provide:

- `HYBA_API_KEY_SECRET`
- `JWT_SECRET`
- explicit `HYBA_CORS_ORIGINS`
- Redis or equivalent distributed state for multi-instance deployments
- secret-manager backed runtime credentials

No populated `.env.local`, live pool credential, wallet, JWT secret, or operator credential may be committed.

---

## 8. Claim boundaries

HYBA claim discipline:

- QaaS is a post-quantum mathematical service: quantum formalism executed without dependency on a physical QPU.
- QIaaS is bounded quantum intelligence on the HYBA mathematical substrate, not a generic chatbot or phenomenal-consciousness claim.
- CIaaS is a commercial computational-intelligence runtime, not generic cloud IaaS.
- Quantum Finance is a code-backed vertical for portfolio QUBO/QAOA/VQE/annealing design and QAE/QMCI risk/pricing evidence packets, not autonomous trade execution.
- PULVINI φ-memory is reversible working-set compression with retained kernels.
