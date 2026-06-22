# HYBA_FULLSTACK — Intelligence Platform

**Status:** production-readiness elevation in progress  
**Owner:** HYBA Analytics Ltd  
**Public product surfaces:** QaaS, QIaaS, CIaaS  
**Private validation substrate:** mining / pool telemetry / accepted-share evidence

HYBA_FULLSTACK is a substrate-independent intelligence platform. The repository implements customer-facing quantum-computational and computational-intelligence services over a shared mathematical substrate, with PULVINI reversible memory compression, Salamander regeneration, evidence seals, customer access control, metering, observability, and governance controls.

Mining infrastructure exists in this repository only as a **private validation and stress-test substrate**. It is not a public product, not sold to customers, and not part of the QaaS/QIaaS/CIaaS commercial surface.

---

## 1. Executive summary

HYBA exposes three commercial service layers:

| Layer | Name | Public role | Implementation anchor |
|---|---|---|---|
| QaaS | Quantum-as-a-Service | Virtual fault-tolerant quantum-computational service on classical/substrate-agnostic hardware | `python_backend/hyba_genesis_api/api/quantum_as_a_service.py` |
| QIaaS | Quantum Intelligence-as-a-Service | API-key gated predict / explain / optimise / heal query surface | `python_backend/hyba_genesis_api/api/quantum_intelligence_service.py` |
| CIaaS | Computational Intelligence-as-a-Service | Customer-provisioned commercial intelligence runtimes | `python_backend/hyba_genesis_api/api/computational_intelligence_service.py` |
| PULVINI | Reversible φ-memory substrate | Golden-ratio working-set compression with retained reconstruction kernels | `python_backend/pythia_mining/pulvini_phi_memory.py` and `phi_folding.py` |
| Salamander | Regeneration substrate | Self-healing / topology repair / bounded reflexive optimisation | `python_backend/pythia_mining/*regeneration*`, `autonomous_mining_controller.py` |
| Evidence governance | Claim boundary and audit layer | Evidence seals, telemetry, product-boundary discipline, claim mapping | `docs/evidence`, `docs/product` |

The platform should be presented as an intelligence infrastructure company, not a mining company.

---

## 2. Product boundary

### Public

- **QaaS:** virtual fault-tolerant quantum-computational primitives.
- **QIaaS:** bounded quantum-intelligence query functions.
- **CIaaS:** provisioned computational-intelligence runtimes.
- **PULVINI:** reversible φ-memory compression.
- **Salamander:** self-healing and regeneration substrate.
- **Evidence/governance:** claim boundaries, audit seals, customer metering, observability.

### Private

- Mining routes and pool telemetry.
- Accepted-share evidence.
- Hash-search experiments.
- Private benchmark traces.
- Internal stress tests for autonomy, memory compression, evidence seals, and resilience.

See `docs/product/HYBA_PRODUCT_BOUNDARIES.md` and `docs/private-validation/MINING_INTERNAL_VALIDATION_BOUNDARY.md`.

---

## 3. Memory compression and φ-scaling

PULVINI implements reversible golden-ratio memory folding. The active working set is compressed by recursive φ-folding, while retained reconstruction kernels preserve exact replay and auditability. This means HYBA can discuss working-set reduction separately from retained-state storage.

The product claim is:

> PULVINI reduces active working-set size through deterministic φ-folding while retaining reconstruction kernels for exact replay and audit evidence.

The product claim is **not**:

> Magical compression, hardware quantum advantage, or lossless compression without retained reconstruction information.

---

## 4. Customer access, metering, and control plane

Customer access is API-key based and backed by HMAC-SHA256 key hashing, tiered quota controls, compute-unit metering, and optional Redis-backed state. Customer-facing product surfaces must use `require_customer_api_key` and route usage through the customer-access metering layer.

Production deployments must provide:

- `HYBA_API_KEY_SECRET`
- `JWT_SECRET`
- explicit `HYBA_CORS_ORIGINS`
- Redis or equivalent distributed state for multi-instance deployments
- secret-manager backed runtime credentials

No populated `.env.local`, live pool credential, wallet, JWT secret, or operator credential may be committed.

---

## 5. Claim boundaries

HYBA claim discipline:

- QaaS is a virtual / mathematical service, not physical quantum hardware.
- QIaaS is bounded quantum intelligence on classical hardware, not a consciousness claim.
- CIaaS is a commercial computational-intelligence runtime, not generic cloud IaaS.
- PULVINI φ-memory is reversible working-set compression with retained kernels, not unexplained free compression.
- Mining is internal validation only, not a public product.
- Any statistical or benchmark claim must point to raw data, runner, environment, commit, and evidence seal.

---

## 6. API surfaces

Primary backend entrypoint:

```bash
uvicorn hyba_genesis_api.main:app --app-dir python_backend --host 0.0.0.0 --port 3001
```

Primary public APIs:

```text
/api/v1/fault-tolerant-computers        # QaaS public customer surface
/api/qiaas                              # QIaaS public customer surface
/api/v1/computational-intelligence-services # CIaaS public customer surface
```

Admin APIs remain under `/api/admin/*` and require admin JWT authorization.

---

## 7. Development setup

```bash
cp .env.example .env.local
# Populate secrets locally only; never commit .env.local
python -m venv .venv
. .venv/bin/activate
pip install -r python_backend/hyba_genesis_api/requirements.txt
python -m pytest tests/test_product_boundary_and_secret_hygiene.py
```

---

## 8. Production readiness gates

Before presenting this repo as production-ready, all of the following must pass:

1. Secret scan: no committed runtime credentials or populated env files.
2. Product-boundary scan: README and product docs state mining is private validation only.
3. Auth scan: customer-facing QaaS/QIaaS/CIaaS endpoints require API-key auth except minimal health checks.
4. Route scan: no duplicate public CIaaS mount points.
5. Evidence scan: investor/regulator claims map to evidence files, test logs, raw data, and claim boundaries.
6. CI scan: full production-readiness workflow runs without development fixtures.

---

## 9. Chairman / investor framing

> HYBA is a substrate-independent intelligence platform. Its public services are QaaS, QIaaS, and CIaaS. QaaS exposes virtual fault-tolerant quantum-computational primitives; QIaaS exposes bounded quantum-intelligence query functions; CIaaS provisions commercial computational-intelligence runtimes. PULVINI provides reversible φ-memory compression, Salamander provides self-healing and regeneration, and the evidence layer preserves claim boundaries. Mining is not a product; it is a private stress-test and evidence substrate used internally to validate the platform under extreme conditions.
