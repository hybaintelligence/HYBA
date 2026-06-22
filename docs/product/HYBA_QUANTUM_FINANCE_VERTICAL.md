# HYBA Quantum Finance Vertical

**Purpose:** implement the finance blueprint as a HYBA product vertical over QaaS, QIaaS, and CIaaS rather than leave it as a generic quantum-finance strategy note.

## Implementation anchors

- API module: `python_backend/hyba_genesis_api/api/quantum_finance_service.py`
- API surface: `/api/quantum-finance`
- Router mount: `python_backend/hyba_genesis_api/main.py`
- Evidence tests: `tests/test_quantum_finance_service_design.py`
- Customer controls: `require_customer_api_key`, `customer_access.meter`

## Product boundary

This is a public finance vertical. It is **not** mining.

The service exposes auditable design packets for human/risk review:

- portfolio optimisation via QUBO + Ising Hamiltonian + QAOA/VQE/annealing design;
- risk/pricing via QAE/QMCI design, VaR, and CVaR summaries;
- evidence packets with input hashes, formula hashes, claim boundaries, product boundaries, and verification notes.

The vertical does not execute autonomous trades, does not expose pool telemetry, and does not claim physical QPU superiority without downstream hardware evidence.

## Endpoint map

| Endpoint | Surface | Purpose |
|---|---|---|
| `GET /api/quantum-finance/capability-map` | QaaS/QIaaS/CIaaS | Returns implemented finance workload map and explicit non-goals. |
| `POST /api/quantum-finance/portfolio/qaoa-design` | QIaaS/CIaaS/QaaS | Builds portfolio QUBO, converts to Ising Hamiltonian, returns QAOA design and audit candidate. |
| `POST /api/quantum-finance/risk/qae-design` | QaaS/QIaaS/CIaaS | Builds QAE/QMCI design for payoff expectation, VaR, CVaR, and quadratic speedup accounting. |

## Portfolio optimisation implementation

The service implements a binary Markowitz-style design:

```text
minimise risk_aversion * x'Σx
       - return_weight * μ'x
       + budget_penalty * (Σx - B)^2
       + optional target-return, transaction-cost, liquidity, and regulatory penalties
```

The implementation then converts the QUBO to Ising form via:

```text
x = (1 - Z) / 2
H = constant + Σ h_i Z_i + Σ J_ij Z_i Z_j
```

The returned QAOA design includes:

1. binary asset-selection qubits;
2. initial superposition over binary allocations;
3. problem Hamiltonian from finance QUBO;
4. mixer Hamiltonian;
5. classical parameter optimiser;
6. bitstring sampling and portfolio decoding;
7. evidence packet for audit and model-risk review.

## Risk/pricing implementation

The service implements QAE/QMCI design for payoff samples:

- expected payoff;
- sample variance;
- empirical VaR;
- empirical CVaR;
- amplitude-estimation iteration count;
- classical Monte Carlo sample count for the same precision epsilon;
- quadratic speedup accounting factor.

The speedup accounting is explicit:

```text
QAE: O(1 / epsilon)
Classical Monte Carlo: O(1 / epsilon^2)
```

## Finance-specific controls

The portfolio request supports:

- budget constraints;
- target return constraints;
- transaction costs;
- liquidity penalties;
- sector/regulatory caps;
- product-surface selection across QaaS, QIaaS, and CIaaS.

## Evidence posture

The finance vertical is Class A at the code/test level for:

- deterministic QUBO construction;
- deterministic Ising conversion;
- deterministic QAOA design packet generation;
- deterministic QAE/VaR/CVaR design packet generation;
- API-key gating and customer metering;
- product boundary excluding mining.

External performance claims remain evidence-gated:

- physical QPU performance requires hardware evidence;
- production model-risk deployment requires institution-specific validation;
- regulated financial deployment requires security, DR, audit, and governance gates.

## Chairman wording

> HYBA now includes a code-backed quantum finance vertical. The platform maps finance workloads into QUBO/QAOA and QAE/QMCI execution designs across QaaS, QIaaS, and CIaaS, with evidence packets for auditability. The vertical is designed for portfolio construction, risk/pricing, VaR/CVaR, and scenario analytics. It is not a mining product and does not perform autonomous trade execution.
