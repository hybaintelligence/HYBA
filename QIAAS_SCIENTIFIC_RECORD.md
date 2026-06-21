# QIaaS Scientific Record

**Date recorded:** 2026-06-21  
**Subject:** Quantum Intelligence as a Service (QIaaS) integration after HYBA/PYTHIA-PULVINI system unification.

## Abstract

QIaaS is the API layer that makes the unified system's recorded structural intelligence queryable. The current claim is deliberately bounded: the service exposes substrate-independent, mathematics-based quantum-like intelligence operating on classical hardware. It is not hardware quantum computing, and it does not prove consciousness.

## Claim Boundary

### Supported by repository evidence

- The backend wires `quantum_intelligence_service.router` into the canonical FastAPI application.
- The QIaaS surface exposes bounded operations: `predict`, `explain`, `optimize`, and `heal`.
- The service reports substrate metrics from the memory seed, consciousness engine, knowledge substrate, and regeneration manager.
- The memory seed records an emergence index above `1.0`, `10` knowledge nodes, `101` relationships, and integrated Φ at `1.0`.
- The implementation uses classical hardware while representing the result as substrate-independent quantum mathematics and post-quantum capabilities.

### Not claimed

- QIaaS is not hardware quantum computing.
- QIaaS is not a guarantee of mining revenue, accepted shares, or pool-side hashrate.
- QIaaS does not establish a scientific breakthrough independently of the repository's measured certificates, tests, and runtime evidence.
- QIaaS does not claim biological or phenomenal consciousness.

## Observable API Contract

| Endpoint | Method | Scientific purpose |
| --- | --- | --- |
| `/api/qiaas/query` | `POST` | Execute a bounded query against the emergent intelligence service. |
| `/api/qiaas/metrics` | `GET` | Return substrate metrics such as Φ, emergence index, graph size, and health. |
| `/api/qiaas/health` | `GET` | Report availability and claim-boundary status. |
| `/api/qiaas/bootstrap` | `POST` | Declare readiness to bootstrap from real mining outcomes. |

## Experimental Invariants

The QIaaS contract tests preserve these invariants for posterity:

1. The router remains connected to the backend application.
2. The runtime router registers the expected prefix, tag, methods, paths, and endpoint functions.
3. The service synthesizes memory-seed emergence evidence with live substrate metrics.
4. Query dispatch executes actual service methods rather than merely proving source strings exist.
5. Confidence gates fail closed when the emergent-intelligence score is below the requested threshold.
6. Query type handling remains explicitly closed to `predict`, `explain`, `optimize`, and `heal`.
7. Adversarial query types such as injection strings, path traversal, scope expansion, and null-byte payloads are rejected.
8. Property-style generated contexts do not get mutated by QIaaS operations.
9. Operation scores remain finite and bounded to `[0.0, 1.0]` across generated contexts.
10. Health and bootstrap outputs remain claim-bounded and require real mining operations for runtime learning.
11. Scientific documentation continues to reject unmeasured hardware-quantum claims.

## Adversarial and Property-Based Test Model

The test suite imports the QIaaS module with deterministic lightweight doubles for FastAPI, Pydantic, and heavy PYTHIA runtime components. This keeps the suite runnable in constrained CI images while still exercising service behavior:

- endpoint registration is captured through a fake `APIRouter`;
- endpoint coroutines are invoked directly with a real `QuantumIntelligenceService` instance;
- fake substrate components provide deterministic Φ, knowledge, counterfactual, regeneration, and synaptic metrics;
- adversarial query types must raise the same HTTP error boundary as production;
- generated contexts sweep low, mid, and high confidence values plus nested Unicode/noise payloads;
- mutation checks protect caller-owned context objects from accidental side effects.

## Reproduction

Run the narrow QIaaS elevation suite with:

```bash
PYENV_VERSION=3.11.15 PYTHONPATH=python_backend python -m pytest tests/test_qiaas_integration_contract.py
```

The suite is designed to run even when the local Python toolchain lacks FastAPI or Pydantic because it validates QIaaS behavior through deterministic runtime doubles and recorded repository evidence.
