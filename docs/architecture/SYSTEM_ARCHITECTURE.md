# HYBA System Architecture

```mermaid
flowchart LR
  Customer[Customer / SDK / curl] --> Gateway[API Gateway / Ingress]
  Gateway --> FastAPI[FastAPI hyba_genesis_api]
  FastAPI --> QaaS[QaaS Fault-Tolerant Computers]
  FastAPI --> QIaaS[QIaaS Predict / Explain / Optimise / Heal]
  FastAPI --> CIaaS[CIaaS Provisioned Intelligence Runtimes]
  FastAPI --> Finance[Quantum Finance QUBO / QAOA / QAE / QMCI]
  QaaS --> PULVINI[PULVINI phi-memory substrate]
  QIaaS --> PULVINI
  CIaaS --> PULVINI
  Finance --> PULVINI
  QaaS --> Salamander[Salamander self-healing layer]
  QIaaS --> Salamander
  CIaaS --> Salamander
  PULVINI --> Redis[(Redis distributed state / cache)]
  FastAPI --> Postgres[(Postgres customer, billing, audit data)]
```

## Runtime boundaries

- Mining is an internal validation substrate, not a customer product surface.
- QaaS, QIaaS, CIaaS, and Quantum Finance are customer-facing revenue surfaces.
- PULVINI and Salamander are shared internal substrate services used by product surfaces.
- Redis supports distributed state, response caching, idempotency, and coordination.
- Postgres is the intended durable system of record for tenants, billing, invoices, and audit trails.
