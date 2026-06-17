# Operational Metrics Dashboard

## Purpose
This document defines the operational metrics dashboard for monitoring HYBA_FULLSTACK production operations, including key performance indicators (KPIs), alert thresholds, and visualization recommendations.

## Dashboard Overview

**Target Audience**: Operators, DevOps engineers, Mining operations team
**Refresh Rate**: 30 seconds for critical metrics, 5 minutes for historical trends
**Data Retention**: Real-time (24h), Short-term (7 days), Long-term (90 days)

## Dashboard Sections

### Section 1: System Health (Top Priority)

#### Metrics
- **Bridge Status**: Online/Degraded/Offline
- **Backend Status**: Reachable/Unreachable
- **Circuit Breaker State**: Open/Closed
- **Uptime**: Time since last restart
- **Health Check Success Rate**: % of successful health checks

#### Visualization
- Status indicators (green/yellow/red)
- Uptime counter
- Health check success rate gauge (target: >99%)
- Circuit breaker status badge

#### Alert Thresholds
- Bridge offline: Immediate alert
- Backend unreachable: Immediate alert
- Circuit breaker open: Immediate alert
- Health check success rate <95%: Warning alert

#### Prometheus Queries
```promql
# Bridge status
hyba_bridge_status

# Backend reachable
hyba_bridge_backend_reachable

# Circuit breaker state
hyba_bridge_circuit_breaker_open

# Uptime
hyba_bridge_uptime_seconds

# Health check success rate
rate(hyba_bridge_health_check_successes[5m]) / rate(hyba_bridge_health_check_total[5m])
```

### Section 2: Mining Operations

#### Metrics
- **Mining Status**: Idle/Starting/Running/Stopping/Stopped
- **Active Pool**: Currently connected pool
- **Pool Connection State**: Connected/Disconnected/Error
- **Share Rate**: Shares per minute
- **Acceptance Rate**: % of accepted shares
- **Hashrate**: Current hashrate (EH/s)
- **Power Consumption**: Current power usage
- **Network Difficulty**: Current network difficulty
- **Block Height**: Current block height

#### Visualization
- Mining status indicator
- Pool connection status badges
- Share rate line chart (1 hour window)
- Acceptance rate gauge (target: >95%)
- Hashrate trend line (24 hours)
- Power consumption bar chart
- Network difficulty trend (7 days)

#### Alert Thresholds
- Mining stopped unexpectedly: Immediate alert
- Pool disconnected >5 minutes: Critical alert
- Acceptance rate <90%: Critical alert
- Acceptance rate <95%: Warning alert
- Hashrate drop >20%: Warning alert

#### Prometheus Queries
```promql
# Mining status
hyba_mining_status

# Pool connection state
hyba_pool_connection_state

# Share rate
rate(hyba_pool_shares_accepted[5m]) * 60

# Acceptance rate
rate(hyba_pool_shares_accepted[5m]) / rate(hyba_pool_shares_submitted[5m])

# Hashrate
hyba_mining_hashrate

# Power consumption
hyba_mining_power_consumption

# Network difficulty
hyba_mining_network_difficulty
```

### Section 3: Performance Metrics

#### Metrics
- **Backend Latency**: Average response time (ms)
- **P50 Latency**: 50th percentile latency
- **P95 Latency**: 95th percentile latency
- **P99 Latency**: 99th percentile latency
- **Request Rate**: Requests per second
- **Error Rate**: % of failed requests
- **Queue Depth**: Number of queued requests

#### Visualization
- Latency histogram (P50, P95, P99)
- Latency trend line (1 hour)
- Request rate line chart (1 hour)
- Error rate gauge (target: <1%)
- Queue depth bar chart

#### Alert Thresholds
- P95 latency >5 seconds: Warning alert
- P95 latency >10 seconds: Critical alert
- Error rate >1%: Warning alert
- Error rate >5%: Critical alert
- Queue depth >100: Warning alert

#### Prometheus Queries
```promql
# Backend latency
hyba_bridge_backend_latency_ms

# P95 latency
histogram_quantile(0.95, rate(hyba_bridge_latency_bucket[5m]))

# Request rate
rate(hyba_bridge_requests_total[5m])

# Error rate
rate(hyba_bridge_proxy_errors[5m]) / rate(hyba_bridge_requests_total[5m])

# Queue depth
hyba_bridge_queue_depth
```

### Section 4: Quantum Operations

#### Metrics
- **Quantum Solver Status**: Active/Idle/Error
- **Basis Coherence**: Quantum coherence level (0-1)
- **Phi Phase Alignment**: Phi alignment percentage
- **Quantum Speedup Factor**: Theoretical speedup
- **Actual Speedup Factor**: Measured speedup
- **PULVINI Manifold State**: Pure/Mixed/Degenerate
- **Memory Compression Ratio**: Compression efficiency
- **Certificate Validity**: Certificate validation status

#### Visualization
- Quantum solver status indicator
- Coherence gauge (target: >0.9)
- Phi alignment gauge (target: >0.8)
- Speedup comparison chart (theoretical vs actual)
- Manifold state badge
- Compression ratio trend (24 hours)
- Certificate validity checklist

#### Alert Thresholds
- Quantum solver error: Immediate alert
- Coherence <0.8: Warning alert
- Coherence <0.5: Critical alert
- Certificate validation failed: Critical alert

#### Prometheus Queries
```promql
# Quantum solver status
hyba_quantum_solver_status

# Basis coherence
hyba_quantum_basis_coherence

# Phi phase alignment
hyba_quantum_phi_resonance

# Quantum speedup
hyba_quantum_speedup_factor

# Manifold state
hyba_pulvini_manifold_state

# Memory compression ratio
hyba_pulvini_compression_ratio
```

### Section 5: Resource Utilization

#### Metrics
- **CPU Usage**: Percentage CPU utilization
- **Memory Usage**: Memory utilization (MB/GB)
- **Disk Usage**: Disk utilization (GB)
- **Network I/O**: Network bytes in/out
- **Open Connections**: Number of active connections
- **Thread Count**: Number of active threads

#### Visualization
- CPU usage gauge (target: <80%)
- Memory usage gauge (target: <85%)
- Disk usage gauge (target: <90%)
- Network I/O line chart (1 hour)
- Open connections counter
- Thread count trend (24 hours)

#### Alert Thresholds
- CPU usage >80%: Warning alert
- CPU usage >90%: Critical alert
- Memory usage >85%: Warning alert
- Memory usage >95%: Critical alert
- Disk usage >90%: Critical alert

#### Prometheus Queries
```promql
# CPU usage
rate(process_cpu_seconds_total[5m]) * 100

# Memory usage
process_resident_memory_bytes / 1024 / 1024 / 1024

# Disk usage
node_filesystem_avail_bytes

# Network I/O
rate(node_network_receive_bytes_total[5m])
rate(node_network_transmit_bytes_total[5m])

# Open connections
node_netstat_Tcp_CurrEstab

# Thread count
process_threads
```

### Section 6: Security and Compliance

#### Metrics
- **Authentication Attempts**: Total auth attempts
- **Failed Auth Rate**: % of failed authentications
- **Security Events**: Security-related events count
- **Audit Log Entries**: Number of audit log entries
- **Certificate Expiry**: Days until certificate expiry
- **Compliance Score**: Overall compliance percentage

#### Visualization
- Authentication attempt counter
- Failed auth rate gauge (target: <5%)
- Security events timeline (24 hours)
- Audit log entry counter
- Certificate expiry countdown
- Compliance score gauge (target: 100%)

#### Alert Thresholds
- Failed auth rate >10%: Critical alert
- Security event detected: Immediate alert
- Certificate expiring <7 days: Warning alert
- Certificate expiring <1 day: Critical alert
- Compliance score <90%: Warning alert

#### Prometheus Queries
```promql
# Authentication attempts
hyba_auth_attempts_total

# Failed auth rate
rate(hyba_auth_failures_total[5m]) / rate(hyba_auth_attempts_total[5m])

# Security events
rate(hyba_security_events_total[5m])

# Audit log entries
hyba_audit_log_entries_total

# Certificate expiry
hyba_certificate_expiry_days

# Compliance score
hyba_compliance_score
```

## Dashboard Layout Recommendations

### Top Row (Always Visible)
1. **System Health Panel** - Left side, status indicators
2. **Mining Operations Panel** - Center, key mining metrics
3. **Alert Panel** - Right side, active alerts

### Middle Row (Main Content)
1. **Performance Metrics** - Left, latency and throughput
2. **Quantum Operations** - Center, quantum solver status
3. **Resource Utilization** - Right, system resources

### Bottom Row (Detailed Views)
1. **Pool Connection Details** - Left, pool-specific metrics
2. **Security and Compliance** - Center, security metrics
3. **Historical Trends** - Right, long-term trends

## Grafana Dashboard Configuration

### Example Dashboard JSON

```json
{
  "dashboard": {
    "title": "HYBA Operations Dashboard",
    "panels": [
      {
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "hyba_bridge_backend_reachable",
            "legendFormat": "Backend Reachable"
          }
        ]
      },
      {
        "title": "Mining Status",
        "type": "stat",
        "targets": [
          {
            "expr": "hyba_mining_status",
            "legendFormat": "Mining Status"
          }
        ]
      },
      {
        "title": "Backend Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "hyba_bridge_backend_latency_ms",
            "legendFormat": "Latency (ms)"
          }
        ]
      },
      {
        "title": "Share Acceptance Rate",
        "type": "gauge",
        "targets": [
          {
            "expr": "rate(hyba_pool_shares_accepted[5m]) / rate(hyba_pool_shares_submitted[5m])",
            "legendFormat": "Acceptance Rate"
          }
        ]
      }
    ]
  }
}
```

## Alerting Configuration

### Alert Manager Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    
    - match:
        severity: warning
      receiver: 'slack'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#hyba-ops'
```

### Alert Rules

```yaml
# alerts.yml
groups:
  - name: hyba_critical
    interval: 30s
    rules:
      - alert: BackendUnreachable
        expr: hyba_bridge_backend_reachable == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend unreachable"
          description: "Backend has been unreachable for 1 minute"

      - alert: CircuitBreakerOpen
        expr: hyba_bridge_circuit_breaker_open == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker open"
          description: "Circuit breaker has been open for 1 minute"

  - name: hyba_warning
    interval: 30s
    rules:
      - alert: HighLatency
        expr: hyba_bridge_backend_latency_ms > 5000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High backend latency"
          description: "Backend latency is {{ $value }}ms"

      - alert: LowAcceptanceRate
        expr: rate(hyba_pool_shares_accepted[5m]) / rate(hyba_pool_shares_submitted[5m]) < 0.95
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low share acceptance rate"
          description: "Acceptance rate is {{ $value | humanizePercentage }}"

      - alert: PythiaPendingApprovalsStuck
        expr: hyba_pythia_pending_approvals > 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "PYTHIA operator approvals pending too long"
          description: "Pending operator approvals have exceeded the approval timeout window."

      - alert: PythiaConstraintViolationSpike
        expr: sum by (constraint_type) (rate(hyba_pythia_constraint_violations_by_type_total[5m])) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "PYTHIA constraint violation spike"
          description: "Constraint {{ $labels.constraint_type }} is violating at {{ $value }} events/sec."

      - alert: PythiaReflexiveCycleP99High
        expr: histogram_quantile(0.99, sum(rate(hyba_pythia_reflexive_cycle_duration_seconds_bucket[5m])) by (le)) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "PYTHIA reflexive cycle p99 latency high"
          description: "p99 reflexive cycle latency is {{ $value }}s; check CPU/memory pressure before exhaustion."

      - alert: PythiaProposalAcceptanceRateLow
        expr: hyba_pythia_proposal_acceptance_rate < 0.2
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "PYTHIA proposal acceptance rate low"
          description: "Proposal acceptance rate is {{ $value | humanizePercentage }}; investigate search topology degradation."
```

## Mobile Dashboard Considerations

### Simplified Mobile View
- **Top**: System health status (3 key metrics)
- **Middle**: Mining status (active pool, share rate)
- **Bottom**: Active alerts (last 5 alerts)

### Push Notifications
- Critical alerts: Immediate push notification
- Warning alerts: Batched every 15 minutes
- Info alerts: No push notification

## Historical Analysis

### Weekly Reports
- **Mining Performance**: Total shares, acceptance rate, hashrate
- **System Reliability**: Uptime, downtime incidents, MTTR
- **Performance Trends**: Latency trends, resource utilization
- **Security Summary**: Authentication attempts, security events

### Monthly Reports
- **Capacity Planning**: Resource growth projections
- **Cost Analysis**: Mining revenue vs. operational costs
- **Compliance Status**: Audit findings, remediation progress
- **Performance Benchmarks**: Comparison to SLAs

## Dashboard Maintenance

### Regular Updates
- **Weekly**: Review alert thresholds and adjust based on operational experience
- **Monthly**: Add new metrics as features are added
- **Quarterly**: Review dashboard layout and optimize for user feedback

### Performance Optimization
- **Query Optimization**: Ensure Prometheus queries complete within 30 seconds
- **Caching**: Cache expensive queries for 60 seconds
- **Sampling**: Use appropriate sampling rates for high-cardinality metrics

## Access Control

### Role-Based Access
- **Operators**: Full access to all metrics and controls
- **Read-Only**: View-only access to metrics
- **Auditors**: Access to compliance and security metrics only
- **Public**: Limited access to aggregated, non-sensitive metrics

### Authentication
- Dashboard access requires authentication
- API token required for programmatic access
- Audit logging for all dashboard access

## Integration with Other Systems

### Incident Management
- Automatic ticket creation for critical alerts
- Link alerts to incident records
- Update incident status from dashboard

### ChatOps
- Post alerts to Slack/Teams
- Allow dashboard commands from chat
- Share dashboard snapshots

### Automation
- Auto-scale based on resource metrics
- Auto-restart based on health metrics
- Auto-failover based on pool metrics

## Conclusion

This operational metrics dashboard provides comprehensive visibility into HYBA_FULLSTACK operations with:
- **Real-time monitoring** of system health and mining operations
- **Proactive alerting** for operational issues
- **Historical analysis** for capacity planning and optimization
- **Role-based access** for different stakeholder needs
- **Mobile support** for on-the-go monitoring

Regular review and optimization of the dashboard ensures it continues to meet operational needs as the system evolves.
