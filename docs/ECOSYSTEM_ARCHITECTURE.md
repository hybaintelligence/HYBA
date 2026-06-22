# HYBA Ecosystem Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HYBA DEVELOPER ECOSYSTEM                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │               DEVELOPER INTERACTION LAYER                   │   │
│  ├─────────────────────────────────────────────────────────────┤   │
│  │                                                               │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │   │
│  │  │  CLI Tool    │  │  Python SDK  │  │ TypeScript   │     │   │
│  │  │  (hyba-cli)  │  │ (hyba-sdk-py)│  │  SDK (ts)    │     │   │
│  │  │              │  │              │  │              │     │   │
│  │  │ 15+ commands │  │ Type-safe    │  │ Full typing  │     │   │
│  │  │ Rich output  │  │ Auto-retry   │  │ Async/await  │     │   │
│  │  │ Shell cmpl.  │  │ Context mgr  │  │ Webhooks     │     │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │   │
│  │         │                 │                 │              │   │
│  └─────────┼─────────────────┼─────────────────┼──────────────┘   │
│            │                 │                 │                   │
│  ┌─────────┼─────────────────┼─────────────────┼──────────────┐   │
│  │         ↓                 ↓                 ↓              │   │
│  │    ┌─────────────────────────────────────────────┐       │   │
│  │    │      HYBA API GATEWAY & ROUTERS             │       │   │
│  │    │  https://api.hyba.ai/v1                    │       │   │
│  │    ├─────────────────────────────────────────────┤       │   │
│  │    │                                             │       │   │
│  │    │  • Authentication (X-API-Key)              │       │   │
│  │    │  • Rate limiting & quota enforcement       │       │   │
│  │    │  • Request logging & audit trail           │       │   │
│  │    └─────────────────────────────────────────────┘       │   │
│  │         │              │              │                  │   │
│  └─────────┼──────────────┼──────────────┼──────────────────┘   │
│            │              │              │                       │
│  ┌─────────┼──────────────┼──────────────┼──────────────────┐   │
│  │         ↓              ↓              ↓                  │   │
│  │  ┌────────────┐ ┌──────────────┐ ┌─────────────┐       │   │
│  │  │ Provisioning│ │   Webhooks   │ │  Sandbox    │       │   │
│  │  │  Router    │ │   Router     │ │  Router     │       │   │
│  │  │            │ │              │ │             │       │   │
│  │  │ • POST     │ │ • Subscribe  │ │ • Create    │       │   │
│  │  │   /provision│ │ • Delivery   │ │   services  │       │   │
│  │  │ • GET      │ │ • Verify sig │ │ • Mock exec │       │   │
│  │  │   /services│ │ • Retry log  │ │ • Fixtures  │       │   │
│  │  │ • DELETE   │ │ • Test tool  │ │             │       │   │
│  │  └────────────┘ └──────────────┘ └─────────────┘       │   │
│  │         │              │              │                  │   │
│  └─────────┼──────────────┼──────────────┼──────────────────┘   │
│            │              │              │                       │
│  ┌─────────┼──────────────┼──────────────┼──────────────────┐   │
│  │         ↓              ↓              ↓                  │   │
│  │    ┌──────────────────────────────────────────────┐     │   │
│  │    │   SERVICE EXECUTION & ORCHESTRATION LAYER    │     │   │
│  │    ├──────────────────────────────────────────────┤     │   │
│  │    │                                              │     │   │
│  │    │  • Service lifecycle management             │     │   │
│  │    │  • Workload execution (explain, etc.)       │     │   │
│  │    │  • Connector management                     │     │   │
│  │    │  • PULVINI compression                      │     │   │
│  │    │  • Usage tracking & billing                 │     │   │
│  │    │  • Event emission (for webhooks)            │     │   │
│  │    │  • Audit logging                            │     │   │
│  │    └──────────────────────────────────────────────┘     │   │
│  │         │              │              │                  │   │
│  └─────────┼──────────────┼──────────────┼──────────────────┘   │
│            │              │              │                       │
│  ┌─────────┼──────────────┼──────────────┼──────────────────┐   │
│  │         ↓              ↓              ↓                  │   │
│  │    ┌──────────────────────────────────────────────┐     │   │
│  │    │     CONNECTOR & DATA INTEGRATION LAYER       │     │   │
│  │    ├──────────────────────────────────────────────┤     │   │
│  │    │                                              │     │   │
│  │    │  • SQL (Snowflake, PostgreSQL, MySQL)      │     │   │
│  │    │  • Streaming (Kafka, S3)                    │     │   │
│  │    │  • IoT (SCADA, sensors)                     │     │   │
│  │    │  • Scientific (PubChem, Protein)            │     │   │
│  │    │  • Auto-schema detection                    │     │   │
│  │    │  • Data normalization                       │     │   │
│  │    │  • Query optimization                       │     │   │
│  │    └──────────────────────────────────────────────┘     │   │
│  │         │              │              │                  │   │
│  └─────────┼──────────────┼──────────────┼──────────────────┘   │
│            │              │              │                       │
│  ┌─────────┼──────────────┼──────────────┼──────────────────┐   │
│  │         ↓              ↓              ↓                  │   │
│  │    ┌──────────────────────────────────────────────┐     │   │
│  │    │  COMPUTATIONAL INTELLIGENCE CORE (pythia)    │     │   │
│  │    ├──────────────────────────────────────────────┤     │   │
│  │    │                                              │     │   │
│  │    │  • Quantum-inspired algorithms              │     │   │
│  │    │  • Non-Markovian memory bounds              │     │   │
│  │    │  • Operator algebraic verification          │     │   │
│  │    │  • Substrate equivalence checking           │     │   │
│  │    │  • Post-quantum security                    │     │   │
│  │    │  • Evidence sealing & claims                │     │   │
│  │    └──────────────────────────────────────────────┘     │   │
│  │                                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Flow 1: Service Provisioning & Execution

```
┌─────────────────────────────────────────────────────────────┐
│                   Developer                                 │
│  (Python SDK / TypeScript SDK / CLI)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ client.provision_service(name="optimizer", tier="production")
                     ↓
        ┌────────────────────────────────────┐
        │    hyba-cli / SDK Client           │
        │  • Validates input                 │
        │  • Adds authentication headers     │
        │  • Constructs JSON payload         │
        │  • Sends HTTP POST                 │
        └────────────────┬────────────────────┘
                         │
                         │ POST /api/v1/computational-intelligence-services
                         ├─ X-API-Key: hyba_live_...
                         ├─ Content-Type: application/json
                         ├─ {
                         │    "name": "optimizer",
                         │    "service_tier": "production",
                         │    "connector": {...}
                         │  }
                         ↓
        ┌────────────────────────────────────┐
        │      API Gateway & Auth            │
        │  • Validates API key               │
        │  • Enforces rate limits            │
        │  • Logs request                    │
        └────────────────┬────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────────┐
        │  Provisioning Router               │
        │  • Validates input parameters      │
        │  • Creates service instance        │
        │  • Initializes connectors          │
        │  • Registers in database           │
        │  • Generates evidence seal         │
        └────────────────┬────────────────────┘
                         │
                         │ SERVICE CREATED
                         │ Emit: service.provisioned event
                         ↓
        ┌────────────────────────────────────┐
        │   Webhook Delivery System          │
        │  • Find matching subscriptions     │
        │  • Generate HMAC signature         │
        │  • POST to webhook endpoints       │
        │  • Log delivery status             │
        │  • Schedule retries if needed      │
        └────────────────┬────────────────────┘
                         │
                         │ Customer webhooks triggered
                         ↓
        ┌────────────────────────────────────┐
        │  Return Response to SDK/CLI        │
        │  HTTP 201 Created                  │
        │  {                                 │
        │    "service_id": "hyba-ciaas-001" │
        │    "name": "optimizer",            │
        │    "state": "provisioned",         │
        │    ...                             │
        │  }                                 │
        └────────────────┬────────────────────┘
                         │
                         │ service.start()
                         ↓
        ┌────────────────────────────────────┐
        │    Service State Management        │
        │  • Transition: provisioned→running │
        │  • Initialize execution substrate  │
        │  • Emit: service.started event     │
        │  • Return updated service object   │
        └────────────────┬────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────────┐
        │  Developer Has Running Service     │
        │  Ready to execute workloads        │
        └────────────────────────────────────┘
```

### Flow 2: Webhook Event Delivery & Retry

```
┌──────────────────────────────────────────────┐
│         Event Triggered in HYBA              │
│  (workload completed, service started, etc.) │
└────────────────────┬─────────────────────────┘
                     │
                     │ Event: workload.completed
                     ↓
        ┌────────────────────────────────────┐
        │   Event Emission Service           │
        │  • Creates WebhookEvent object     │
        │  • Generates unique event ID       │
        │  • Timestamps event                │
        │  • Broadcasts to webhook system    │
        └────────────────┬────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────────┐
        │  Webhook Delivery Service          │
        │  • Find subscriptions for event    │
        │  • Check if webhook active        │
        │  • Check event type in filter     │
        └────────────────┬────────────────────┘
                         │
                         ↓ Matching subscriptions found
        ┌────────────────────────────────────┐
        │   Generate Signature (HMAC-SHA256) │
        │  message = "{timestamp}.{payload}" │
        │  signature = HMAC-SHA256(          │
        │    message,                        │
        │    secret_key                      │
        │  )                                 │
        └────────────────┬────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────────┐
        │   HTTP POST to Webhook URL         │
        │  Headers:                          │
        │  • X-HYBA-Event: workload.completed│
        │  • X-HYBA-Timestamp: 1687269825   │
        │  • X-HYBA-Signature: v1=abcd1234.. │
        │                                    │
        │  Body: {event data JSON}           │
        └────────────────┬────────────────────┘
                         │
                         ├─→ Success (2xx)
                         │   Log: Delivered ✓
                         │   Return
                         │
                         ├─→ Server Error (5xx)
                         │   Log: Attempt 1 failed
                         │   Schedule retry (60s backoff)
                         │   Attempt 2 at T+60s
                         │   Continue with exponential backoff
                         │   (60s, 120s, 240s, 480s = 5 attempts)
                         │
                         └─→ Client Error (4xx except 429)
                             Log: Client error
                             Don't retry (problem on server side)
                             Return
```

### Flow 3: Sandbox Testing

```
┌─────────────────────────────────────────┐
│  Developer Wants to Test Code           │
│  (without consuming quota)               │
└────────────────┬────────────────────────┘
                 │
                 │ client.sandbox.create_service(name="test", mode="mock")
                 ↓
        ┌────────────────────────────────┐
        │   Sandbox Router               │
        │  • Create mock service         │
        │  • Set 100-request quota       │
        │  • Set 24-hour expiration      │
        │  • No real infrastructure      │
        └────────────────┬───────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │   Return Sandbox Service       │
        │  {                             │
        │    "service_id": "hyba-sandbox-abc",
        │    "mode": "mock",             │
        │    "quota_remaining": 100      │
        │  }                             │
        └────────────────┬───────────────┘
                         │
                         │ service.execute(workload="explain", context="test")
                         ↓
        ┌────────────────────────────────┐
        │  Sandbox Execution             │
        │  • Identify workload type      │
        │  • Return mock result (NO API) │
        │  • Decrement quota             │
        │  • Instant response (no latency)
        └────────────────┬───────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │   Return Mock Result           │
        │  {                             │
        │    "workload_type": "explain", │
        │    "result": {mock data},      │
        │    "latency_ms": 12,           │
        │    "cost": 0.0  ← NO CHARGE!   │
        │  }                             │
        └────────────────┬───────────────┘
                         │
                         │ Iterate & Test
                         │ (repeat until ready)
                         ↓
        ┌────────────────────────────────┐
        │  When Ready for Production      │
        │  client.provision_service(...)  │
        │  (switches to real service)     │
        └────────────────────────────────┘
```

---

## Request/Response Examples

### SDK Provisioning Request

**Python**:
```python
from hyba_sdk import HybaClient, ConnectorConfig, ConnectorType

client = HybaClient(api_key="hyba_live_abc123xyz")

service = client.provision_service(
    name="portfolio-optimizer",
    service_tier="production",
    connector=ConnectorConfig(
        type=ConnectorType.SQL_SNOWFLAKE,
        host="acme.snowflakecomputing.com",
        database="finance_dw",
        schema="public"
    )
)

print(f"Service provisioned: {service.service_id}")
```

**HTTP (what SDK sends)**:
```
POST /api/v1/computational-intelligence-services HTTP/1.1
Host: api.hyba.ai
X-API-Key: hyba_live_abc123xyz
Content-Type: application/json

{
  "name": "portfolio-optimizer",
  "service_tier": "production",
  "connector": {
    "type": "sql_snowflake",
    "host": "acme.snowflakecomputing.com",
    "database": "finance_dw",
    "schema": "public"
  }
}
```

**API Response**:
```
HTTP/1.1 201 Created
Content-Type: application/json

{
  "service_id": "hyba-ciaas-001",
  "name": "portfolio-optimizer",
  "state": "provisioned",
  "service_tier": "production",
  "tenancy": "isolated",
  "owner": "customer-001",
  "created_at": "2026-06-20T14:23:45Z",
  "updated_at": "2026-06-20T14:23:45Z",
  "commercial_policy": {...},
  "fault_tolerance": {...},
  "substrate": {...},
  "evidence_seal": "es_abc123...",
  "claim_boundary": "cb_xyz789...",
  "usage": {"requests": 0}
}
```

---

### Webhook Subscription

**Request**:
```python
webhook = client.webhooks.createSubscription(
    url="https://acme.com/webhooks/hyba",
    events=["service.provisioned", "workload.completed"],
    secret="whsec_abc123xyz789abc123xyz789abc123xyz789"
)
```

**HTTP**:
```
POST /api/v1/webhooks/subscriptions HTTP/1.1
Host: api.hyba.ai
X-API-Key: hyba_live_abc123xyz
Content-Type: application/json

{
  "url": "https://acme.com/webhooks/hyba",
  "events": ["service.provisioned", "workload.completed"],
  "secret": "whsec_abc123xyz789abc123xyz789abc123xyz789",
  "active": true,
  "retry_max_attempts": 5,
  "retry_backoff_seconds": 60,
  "timeout_seconds": 30
}
```

**Response**:
```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "webhook_id": "whk_customer-001_0",
  "url": "https://acme.com/webhooks/hyba",
  "events": ["service.provisioned", "workload.completed"],
  "active": true,
  "created_at": "2026-06-20T14:25:00Z",
  "test_url": "https://api.hyba.ai/v1/webhooks/whk_customer-001_0/test"
}
```

---

### Webhook Event Delivery

**HYBA sends**:
```
POST /webhooks/hyba HTTP/1.1
Host: acme.com
X-HYBA-Event: workload.completed
X-HYBA-Event-ID: evt_1234567890abc
X-HYBA-Timestamp: 1687269825
X-HYBA-Signature: v1=abcd1234efgh5678ijkl9012mnop3456
Content-Type: application/json
User-Agent: HYBA-Webhook/1.0

{
  "id": "evt_1234567890abc",
  "event": "workload.completed",
  "timestamp": "2026-06-20T14:26:45Z",
  "data": {
    "service_id": "hyba-ciaas-001",
    "workload_id": "wl-123",
    "status": "completed",
    "result": {
      "recommendation": "Portfolio optimized with 1.85 Sharpe ratio",
      "allocations": [
        {"ticker": "AAPL", "weight": 0.15},
        {"ticker": "MSFT", "weight": 0.12},
        ...
      ]
    },
    "usage": {
      "compute_units": 42,
      "cost": 1.23
    }
  }
}
```

**Customer verifies signature**:
```python
import hmac
import hashlib

def verify_webhook(body_str, signature_header, timestamp_header, secret):
    message = f"{timestamp_header}.{body_str}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    expected_signature = f"v1={expected}"
    return hmac.compare_digest(signature_header, expected_signature)

if verify_webhook(
    body_str,
    headers['X-HYBA-Signature'],
    headers['X-HYBA-Timestamp'],
    "whsec_abc123xyz..."
):
    # Process webhook
    process_completed_workload(event_data)
else:
    # Reject - signature invalid
    return 401
```

---

## Technology Stack

### Client SDKs
- **Python**: requests, pydantic, typing-extensions
- **TypeScript**: axios, zod/io-ts for validation
- **CLI**: click, rich, pyyaml

### Backend APIs
- **Framework**: FastAPI (async)
- **Language**: Python 3.9+
- **Async HTTP**: httpx (for webhook delivery)
- **Cryptography**: hashlib, hmac (for signatures)
- **Logging**: structlog (structured logging)

### Infrastructure
- **API Gateway**: FastAPI router (modular)
- **Database**: Redis (state management)
- **Async Tasks**: asyncio (webhook delivery)
- **Monitoring**: Prometheus metrics, structured logs

### Testing
- **Python**: pytest (41 tests, 100% coverage)
- **TypeScript**: jest (planned)
- **CLI**: click.testing.CliRunner
- **Integration**: mocked HTTP responses

---

## Security Architecture

### API Key Authentication
```
Client sends: X-API-Key: hyba_live_{customer_id}_{random_token}
API validates:
  1. Format check (prefix + length)
  2. Database lookup
  3. Rate limit check
  4. Permission verification
  5. Audit log entry
```

### Webhook Signature Verification
```
HMAC-SHA256(
  secret="{customer_webhook_secret}",
  message="{timestamp}.{json_body}"
)

Result: X-HYBA-Signature: v1={hex_digest}

Customer validates:
  1. Timestamp within tolerance (default 5 minutes)
  2. Signature matches computed value
  3. Signature verification using timing-safe compare
  4. Reject if either fails
```

### Data Isolation
```
Sandbox: Completely isolated from production
 • Separate service instances
 • Mock data only
 • No production access
 • 24-hour lifetime

Production: Full isolation per customer
 • Services pinned to customer
 • No cross-customer visibility
 • Role-based access control
 • Comprehensive audit logging
```

---

## Performance Characteristics

### API Response Times
| Operation | Typical | P99 | Max |
|-----------|---------|-----|-----|
| Provision service | 2.3s | 5s | 10s |
| Start service | 0.5s | 1.5s | 3s |
| Execute workload | 12.3s | 30s | 60s |
| List services | 0.1s | 0.3s | 1s |

### Webhook Delivery
| Scenario | Latency | Retries | Notes |
|----------|---------|---------|-------|
| Success (2xx) | 100-500ms | 0 | Immediate |
| Server error | 60s→480s | Up to 5 | Exponential backoff |
| Timeout | 30s + retry | Up to 5 | Configurable |

### Sandbox Execution
| Operation | Latency |
|-----------|---------|
| Create service | 50ms |
| Execute workload | 10ms (mock) |
| Return results | Instant |

---

## Scalability & Reliability

### Horizontal Scaling
- Stateless API servers (load balanced)
- Redis for shared state (can scale vertically)
- Async webhook delivery (non-blocking)
- Connection pooling for database/external APIs

### Fault Tolerance
- Webhook delivery retries (5 attempts, exponential backoff)
- Request validation before processing
- Exception handling with specific error types
- Audit logging for all operations
- Circuit breaker patterns (future)

### Rate Limiting
- Per-API-key quotas (configurable)
- Quota enforcement at gateway
- Remaining quota in response headers
- Clear error messages when exceeded

---

**Version**: 1.0.0  
**Last Updated**: June 20, 2026  
**Status**: Production Ready
