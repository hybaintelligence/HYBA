# HYBA SDK for Python

Official Python SDK for the [HYBA Quantum Intelligence API](https://hyba.ai), QaaS, and CIaaS platform.

## Installation

```bash
pip install hyba-sdk
```

## Quick Start

```python
from hyba_sdk import HybaClient, ConnectorConfig, ConnectorType

# Initialize client
client = HybaClient(api_key="hyba_live_...")

# Provision a service
service = client.provision_service(
    name="my-portfolio-optimizer",
    service_tier="production",
    connector=ConnectorConfig(
        type=ConnectorType.SQL_SNOWFLAKE,
        host="acme.snowflakecomputing.com",
        database="finance_dw",
        query="SELECT * FROM positions"
    )
)

# Start the service
service.start()

# Execute workloads
result = service.explain("Portfolio optimization strategy")
print(result["result"])

# Or use convenience methods
result = service.orchestrate("Optimize for maximum Sharpe ratio")
result = service.counterfactual("What if tech allocation > 20%?")
result = service.governance_audit("Check compliance with ESG constraints")

# Stop when done
service.stop()
```


## Quantum Intelligence API

HYBA exposes QIaaS as a first-class **Quantum Intelligence API**: beyond AGI/ASI framing, substrate-independent, evidence-sealed, and governed by enterprise auth, tenancy, quota, trace, and audit controls. Responses include execution evidence such as `qi_execution_id`, `evidence_id`, `trace_id`, `claim_boundary`, `substrate_state`, and usage-meter data.

## Features

- **Simple API**: 5 lines to provision and execute vs. 20+ with raw REST
- **Type Safety**: Full type hints for IDE autocomplete
- **Error Handling**: Specific exceptions for different error types
- **Retries**: Automatic retries with exponential backoff
- **Context Managers**: Clean resource management
- **Connector Config**: Type-safe connector configuration

## Documentation

- [API Reference](docs/api.md)
- [Examples](examples/)
- [Migration Guide](MIGRATION.md)

## Examples

### Portfolio Optimization

```python
from hyba_sdk import HybaClient, ConnectorConfig, ConnectorType

client = HybaClient(api_key="hyba_live_...")

# Provision with Snowflake connector
service = client.provision_service(
    name="jpmorgan-portfolio-opt",
    service_tier="production",
    tenancy="dedicated-control-plane",
    connector=ConnectorConfig(
        type=ConnectorType.SQL_SNOWFLAKE,
        host="acme.snowflakecomputing.com",
        database="finance_dw",
        query="SELECT * FROM portfolio_positions WHERE date >= CURRENT_DATE - 30"
    )
)

service.start()

# Run optimization
result = service.execute(
    workload="orchestrate",
    context="Maximize Sharpe ratio with max 5% single-position concentration",
    constraints=["leverage <= 2.0", "esg_score >= 0.7"]
)

print(f"Optimized weights: {result['weights']}")
print(f"Expected Sharpe: {result['sharpe_ratio']}")

service.stop()
```

### Drug Discovery

```python
from hyba_sdk import HybaClient, ConnectorConfig, ConnectorType

client = HybaClient(api_key="hyba_live_...")

# Provision with PubChem connector
service = client.provision_service(
    name="moderna-drug-discovery",
    service_tier="production",
    connector=ConnectorConfig(
        type=ConnectorType.PUB_CHEM,
        query="kinase inhibitors"
    )
)

service.start()

# Screen compounds
result = service.execute(
    workload="counterfactual",
    context="Screen 10000 compounds for kinase inhibition with IC50 < 10nM"
)

print(f"Top hits: {result['top_compounds'][:10]}")

service.stop()
```

### Real-time Streaming

```python
from hyba_sdk import HybaClient, ConnectorConfig, ConnectorType

client = HybaClient(api_key="hyba_live_...")

# Provision with Kafka connector
service = client.provision_service(
    name="realtime-anomaly-detection",
    service_tier="production",
    connector=ConnectorConfig(
        type=ConnectorType.KAFKA,
        broker="kafka.acme.com:9092",
        topic="sensor-data"
    )
)

service.start()

# Stream results
for result in service.stream_results():
    if result["anomaly_score"] > 0.8:
        print(f"ANOMALY DETECTED: {result}")
```

## Error Handling

```python
from hyba_sdk import (
    HybaClient,
    AuthenticationError,
    QuotaExceededError,
    ServiceNotFoundError,
    ValidationError,
)

client = HybaClient(api_key="hyba_live_...")

try:
    service = client.get_service("non-existent")
except ServiceNotFoundError as e:
    print(f"Service not found: {e.service_id}")

try:
    result = service.execute(workload="explain", context="test")
except QuotaExceededError as e:
    print(f"Quota exceeded, resets at {e.quota_info['reset_at']}")
except ValidationError as e:
    print(f"Validation errors: {e.validation_errors}")
```

## Context Manager

```python
from hyba_sdk import HybaClient

with HybaClient(api_key="hyba_live_...") as client:
    service = client.provision_service(name="temp-service")
    service.start()
    result = service.execute(workload="explain", context="test")
    service.stop()
# Session automatically closed
```

## Configuration

```python
from hyba_sdk import HybaClient

# Sandbox environment
client = HybaClient(
    api_key="hyba_live_...",
    base_url="https://sandbox.api.hyba.ai",
    timeout=60,
    max_retries=5
)
```

## Requirements

- Python 3.8+
- requests >= 2.31.0
- pydantic >= 2.0.0
- typing-extensions >= 4.5.0
- cryptography >= 41.0.0

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- Documentation: https://docs.hyba.ai
- GitHub Issues: https://github.com/hybaanalytics1/hyba-sdk-py/issues
- Email: dev@hyba.ai
### First-class QIaaS methods

```python
qi = client.quantum_intelligence.query("Explain portfolio convexity", context={"desk": "rates"})
optimized = client.quantum_intelligence.optimize({"objective": "max_sharpe", "constraints": ["leverage <= 2"]})
repair = client.quantum_intelligence.heal({"component": "executor", "mode": "salamander"})
qaoa = client.quantum_finance.portfolio_qaoa({"positions": positions, "risk_model": "enterprise"})
```
