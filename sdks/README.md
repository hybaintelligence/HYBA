# HYBA SDK Quickstart

Set common environment variables:

```bash
export HYBA_BASE_URL="https://staging.hyba.example"
export HYBA_API_KEY="hyba_live_or_test_key"
```

## Install

### Python

```bash
pip install ./sdks/hyba-sdk-py
```

### JavaScript / TypeScript

```bash
cd sdks/hyba-sdk-ts
npm install
npm run build
```

### curl

No installation required beyond `curl`.

## Authentication

All examples send the customer API key in `X-API-Key`. Keep keys out of source control and logs.

## QaaS: first fault-tolerant computer call

### curl

```bash
curl -s -X POST "$HYBA_BASE_URL/api/v1/fault-tolerant-computers" \
  -H "X-API-Key: $HYBA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"quickstart-ftqc","tier":"developer","code_distance":7,"logical_qubits":8}'
```

### Python

```python
from hyba_sdk import HybaClient

client = HybaClient(api_key="hyba_live_or_test_key", base_url="https://staging.hyba.example")
computer = client.provision_computer(name="quickstart-ftqc", tier="developer", code_distance=7, logical_qubits=8)
client.start_computer(computer["computer_id"])
result = client.execute_quantum_workload(
    computer["computer_id"],
    operation="surface_code_cycle",
    logical_qubits=[0],
    circuit_depth=4,
    shots=16,
)
print(result)
```

### JavaScript / TypeScript

```ts
import { HybaClient } from "@hyba/sdk";

const client = new HybaClient({ apiKey: process.env.HYBA_API_KEY!, baseUrl: process.env.HYBA_BASE_URL! });
const computer = await client.provisionComputer({ name: "quickstart-ftqc", tier: "developer", code_distance: 7, logical_qubits: 8 });
await client.startComputer(computer.computer_id);
const result = await client.executeQuantumWorkload(computer.computer_id, { operation: "surface_code_cycle", logical_qubits: [0], circuit_depth: 4, shots: 16 });
console.log(result);
```

## QIaaS: first predict call

### curl

```bash
curl -s -X POST "$HYBA_BASE_URL/api/qiaas/query" \
  -H "X-API-Key: $HYBA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query_type":"predict","context":{"question":"forecast demand"},"confidence_threshold":0.7}'
```

### Python

```python
response = client.quantum_intelligence.query("forecast demand", context={"horizon_days": 7}, query_type="predict")
print(response["result"])
```

### JavaScript / TypeScript

```ts
const prediction = await client.qiaas.predict({ query_type: "predict", context: { horizon_days: 7 }, confidence_threshold: 0.7 });
console.log(prediction.result);
```

## Finance: first portfolio call

### curl

```bash
curl -s -X POST "$HYBA_BASE_URL/api/quantum-finance/portfolio/qaoa-design" \
  -H "X-API-Key: $HYBA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"expected_returns":[0.05,0.08],"covariance_matrix":[[0.1,0.02],[0.02,0.2]],"budget":1,"risk_aversion":1.0,"surface":"qiaas","qaoa_layers":3}'
```

### Python

```python
portfolio = client._request("POST", "/api/quantum-finance/portfolio/qaoa-design", json={
    "expected_returns": [0.05, 0.08],
    "covariance_matrix": [[0.1, 0.02], [0.02, 0.2]],
    "budget": 1,
    "risk_aversion": 1.0,
    "surface": "qiaas",
    "qaoa_layers": 3,
})
print(portfolio["selected_candidate"])
```

### JavaScript / TypeScript

```ts
const portfolio = await client.finance.portfolioOptimize({
  expected_returns: [0.05, 0.08],
  covariance_matrix: [[0.1, 0.02], [0.02, 0.2]],
  budget: 1,
  risk_aversion: 1.0,
  surface: "qiaas",
  qaoa_layers: 3,
});
console.log(portfolio.selected_candidate);
```

## Error handling

- `401`: missing or invalid API key. Rotate or recreate the key.
- `403`: key is valid but not entitled for the requested surface.
- `422`: request schema validation failed; compare with `docs/api/README.md`.
- `429`: rate limit or quota exhaustion; SDKs retry rate limits with exponential backoff.
- `503`: dependency degraded; retry later and preserve the response trace/request id for support.
