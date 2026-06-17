# Observability: Metrics, Dashboards and Alerts

A robust observability strategy allows operators to detect issues early and maintain high reliability. HYBA_FULLSTACK includes basic telemetry collection via the `hyba_genesis_api.core.telemetry` module; this document outlines how to extend it into full monitoring pipelines.

## Defining key metrics

Identify and record metrics that reflect user experience and system health:

- **Request metrics** – Request count, latency (p50/p95/p99), error rate and throughput.
- **Mining metrics** – Hashrate, job completion time, share acceptance rate.
- **Resource usage** – CPU, memory, disk I/O, database connections.
- **Business KPIs** – Accepted blocks, experiment counts, performance of AI modules.

The existing telemetry middleware tracks total requests and errors and logs them as structured JSON【121†L15-L89】. To expose these metrics to Prometheus, wrap the in‑memory metrics in a `/metrics` endpoint (e.g., using `prometheus_client`) and increment counters/timers in the middleware.

## Dashboards

Use a dashboarding tool such as Grafana to visualise metrics. Create panels for:

- API latency and error rate (over time, by endpoint).
- Mining throughput and pool status.
- Database query duration and connection count.
- Resource utilisation per container.

Dashboards should include annotations for deployments and incidents.

## Alerting

Define alert rules that trigger when metrics breach thresholds:

- High error rate (>1% of requests over 5 minutes).
- Slow request latency (p95 > 500 ms).
- Mining hashrate drops below target thresholds.
- Database connection pool saturation or high replication lag.

Alerts should integrate with incident management tools (PagerDuty, Opsgenie) and include links to relevant runbooks. Tune thresholds based on baseline performance and adjust to reduce noise.

## Logging correlation

All logs are structured JSON via `pythonjsonlogger` and include request IDs and timing information【121†L32-L38】. Forward logs to a central log management system (e.g., ELK, Splunk) and correlate log events with metrics to diagnose issues quickly.

Implementing comprehensive observability ensures that operators have the visibility to maintain performance and react to incidents promptly.
