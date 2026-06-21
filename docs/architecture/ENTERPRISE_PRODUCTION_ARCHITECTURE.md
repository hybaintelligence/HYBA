# Enterprise Production Architecture

## Logical architecture

```text
Customer / Operator
        |
        v
Frontend / Console
        |
        v
HYBA Genesis API
  |-- enterprise API posture middleware
  |-- telemetry middleware
  |-- auth, admin, customer, mining, intelligence, QIaaS routers
  |-- resilience circuit breakers for external dependencies
        |
        +--> substrate lifecycle and memory seed
        +--> mining and pool-management workflows
        +--> governance gates and evidence packets
        +--> billing/quota telemetry
        +--> logs, metrics, audit events
```

## Production control points

| Layer | Control |
|---|---|
| Edge | CORS allowlist, WAF/API gateway, TLS termination |
| API | request/correlation IDs, security headers, sanitized errors, body limit, rate-limit backstop |
| Runtime | health endpoint, Prometheus metrics, OpenTelemetry-ready context |
| Workflow | bounded retries, timeouts, circuit breaker, degraded-mode runbook |
| Governance | claim-tier checks, commercialization gates, enterprise closure manifest |
| Data | managed secrets, privacy inventory, low-cardinality metrics |
| Customer operations | status page, support workflow, incident severity matrix |
| FinOps | billing usage metrics, quota gauges, cloud budget alerts |

## Deployment modes

### Local/Docker day-one

Use local Prometheus scrape or direct `/metrics`, local logs, and repository gates.

### Cloud later

Add managed collector, central logs, secret store, IAM, WAF/API gateway, budget alarms, status page, support system, and external audit evidence.

## Non-goals

This architecture document does not claim external certification, customer SLA, or multi-region failover until those systems are deployed and evidenced.
