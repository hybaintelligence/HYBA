# HYBA API Reference Skeleton

All customer endpoints require `X-API-Key: <key>` unless explicitly marked public health. JSON requests require `Content-Type: application/json`.

## Health

- Method/path: `GET /api/health`
- Auth: none for load balancers; deployment may restrict externally.
- Response: `{"status":"healthy","version":"<git_sha>","timestamp":"<iso8601>"}`
- Errors: `503` degraded dependency.

```bash
curl -s "$HYBA_BASE_URL/api/health"
```

## QaaS — Fault-Tolerant Computers

### Provision computer

- Method/path: `POST /api/v1/fault-tolerant-computers`
- Auth: API key
- Request schema:

```json
{"name":"dev-ftqc","tier":"developer","isolation":"single-tenant","code_distance":7,"logical_qubits":8,"physical_error_rate":0.001,"phi_resonance_target":0.9565,"max_circuit_depth":1024,"max_shots":1024,"data_residency":"us","allowed_operations":["surface_code_cycle"]}
```

- Response schema: `computer_id`, `name`, `state`, `tier`, `owner`, `quantum_parameters`, `fault_tolerance`, `substrate`, `evidence_seal`, `claim_boundary`.
- Error codes: `401`, `403`, `422`, `429`, `503`.

```bash
curl -s -X POST "$HYBA_BASE_URL/api/v1/fault-tolerant-computers" -H "X-API-Key: $HYBA_API_KEY" -H "Content-Type: application/json" -d '{"name":"dev-ftqc","code_distance":7,"logical_qubits":8}'
```

### List computers

- Method/path: `GET /api/v1/fault-tolerant-computers`
- Response: array of computer response objects.

### Start computer

- Method/path: `POST /api/v1/fault-tolerant-computers/{computer_id}/start`

### Execute workload

- Method/path: `POST /api/v1/fault-tolerant-computers/{computer_id}/execute`
- Request schema: `{"operation":"surface_code_cycle","logical_qubits":[0],"circuit_depth":4,"shots":16,"context":{},"substrates":["iit_4"],"idempotency_key":"optional"}`
- Response schema: execution id, metering, result, evidence/claim boundary fields.

## QIaaS

### Execute query

- Method/path: `POST /api/qiaas/query`
- Auth: API key
- Request schema: `{"query_type":"predict","context":{"question":"..."},"confidence_threshold":0.7}`
- Response schema: `qi_execution_id`, `intelligence_type`, `result`, `confidence`, `phi_coherence`, `emergence_index`, `evidence_packet`, `usage_meter`, `trace`, `claim_boundary`, `product_boundary`.
- Errors: `401`, `422`, `429`, `503`.

```bash
curl -s -X POST "$HYBA_BASE_URL/api/qiaas/query" -H "X-API-Key: $HYBA_API_KEY" -H "Content-Type: application/json" -d '{"query_type":"predict","context":{"signal":"demo"}}'
```

### Metrics and health

- `GET /api/qiaas/metrics`
- `GET /api/qiaas/health`

## CIaaS

### Provision service

- Method/path: `POST /api/v1/computational-intelligence-services`
- Auth: API key
- Request schema: service name, tier, isolation, runtime parameters, entitlement-specific options.
- Response schema: service id, state, owner, runtime parameters, evidence seal.

```bash
curl -s -X POST "$HYBA_BASE_URL/api/v1/computational-intelligence-services" -H "X-API-Key: $HYBA_API_KEY" -H "Content-Type: application/json" -d '{"name":"dev-ciaas","tier":"developer"}'
```

### List/start/execute

- `GET /api/v1/computational-intelligence-services`
- `POST /api/v1/computational-intelligence-services/{service_id}/start`
- `POST /api/v1/computational-intelligence-services/{service_id}/workloads`

## Quantum Finance

### Capability map

- Method/path: `GET /api/quantum-finance/capability-map`
- Response schema: finance algorithms, supported surfaces, claim boundaries.

```bash
curl -s "$HYBA_BASE_URL/api/quantum-finance/capability-map" -H "X-API-Key: $HYBA_API_KEY"
```

### Portfolio optimisation

- Method/path: `POST /api/quantum-finance/portfolio/qaoa-design`
- Request schema: `{"expected_returns":[0.05,0.08],"covariance_matrix":[[0.1,0.02],[0.02,0.2]],"budget":1,"risk_aversion":1.0,"surface":"qiaas","qaoa_layers":3}`
- Response schema: `qubo`, `ising_hamiltonian`, `qaoa_circuit_design`, `selected_candidate`, `evidence_packet`, `usage_meter`.

### Risk/pricing

- Method/path: `POST /api/quantum-finance/risk/qae-design`
- Request schema: `{"payoff_samples":[1.0,1.2,0.8],"confidence_level":0.95,"precision_epsilon":0.01,"instrument_type":"generic_payoff","surface":"qaas"}`
- Response schema: `pricing_summary`, `risk_summary`, `qae_design`, `evidence_packet`, `usage_meter`.
