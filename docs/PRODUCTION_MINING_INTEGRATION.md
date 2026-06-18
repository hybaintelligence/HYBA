# Production Mining Integration Guide

## Overview

This guide covers the production-grade mining implementation that integrates with real cryptocurrency pools via Stratum v1/v2 protocol with enterprise-class reliability, health monitoring, and multi-pool failover support.

## Architecture

### Components

1. **ProductionMiningGateway** - High-level orchestration and lifecycle management
2. **ProductionMiningOrchestrator** - Multi-pool coordination with health monitoring
3. **StratumClient** - Low-level protocol implementation for each pool
4. **Mining API** - REST endpoints for external integration
5. **Deployment Gate** - Pre-flight validation before production deployment

## Configuration

### Environment Variables

#### Basic Pool Configuration

Define pools using environment variables (up to 10 pools):

```bash
# Pool 1 (Primary)
export HYBA_POOL_1_NAME="NiceHash"
export HYBA_POOL_1_URL="stratum+ssl://btc.nicehash.com:3334"
export HYBA_POOL_1_USERNAME="34HKwkSmM2VNSVQ4XvCvYqWjV5YSKzS6mF"
export HYBA_POOL_1_PASSWORD="x"
export HYBA_POOL_1_STRATUM_VERSION="1"
export HYBA_POOL_1_PRIORITY="100"
export HYBA_POOL_1_TLS_REQUIRED="true"

# Pool 2 (Backup)
export HYBA_POOL_2_NAME="ViaBTC"
export HYBA_POOL_2_URL="stratum+ssl://btc.viabtc.com:3333"
export HYBA_POOL_2_USERNAME="username.worker"
export HYBA_POOL_2_PASSWORD="password"
export HYBA_POOL_2_STRATUM_VERSION="1"
export HYBA_POOL_2_PRIORITY="90"
export HYBA_POOL_2_TLS_REQUIRED="true"

# Pool 3 (Final Fallback)
export HYBA_POOL_3_NAME="F2Pool"
export HYBA_POOL_3_URL="stratum+ssl://btc.f2pool.com:3333"
export HYBA_POOL_3_USERNAME="username.worker"
export HYBA_POOL_3_PASSWORD="password"
export HYBA_POOL_3_STRATUM_VERSION="1"
export HYBA_POOL_3_PRIORITY="80"
export HYBA_POOL_3_TLS_REQUIRED="true"
```

#### JSON Configuration

For more complex configurations, use JSON:

```bash
export HYBA_MINING_POOLS_JSON='[
  {
    "name": "NiceHash Primary",
    "url": "stratum+ssl://btc.nicehash.com:3334",
    "username": "34HKwkSmM2VNSVQ4XvCvYqWjV5YSKzS6mF",
    "password": "x",
    "stratum_version": 1,
    "priority": 100,
    "tls_required": true
  },
  {
    "name": "ViaBTC Backup",
    "url": "stratum+ssl://btc.viabtc.com:3333",
    "username": "username.worker",
    "password": "password",
    "stratum_version": 1,
    "priority": 90,
    "tls_required": true
  }
]'
```

#### Mining Strategy

```bash
# Failover strategy (default) - submit to first healthy, cascade on failure
export HYBA_MINING_STRATEGY="failover"

# Multi-pool strategy - submit to all healthy pools simultaneously
export HYBA_MINING_STRATEGY="multi_pool"

# First-pool only strategy - only use primary pool
export HYBA_MINING_STRATEGY="first_pool"
```

#### Other Configuration

```bash
# Health check interval (seconds)
export HYBA_HEALTH_CHECK_INTERVAL="30"

# Pool failures before marking degraded
export HYBA_POOL_DEGRADED_THRESHOLD="3"

# Pool failures before marking offline
export HYBA_POOL_OFFLINE_THRESHOLD="10"

# Production mode (disable development fixtures)
export NODE_ENV="production"
```

## API Integration

### Initialize Mining

```bash
POST /api/v1/mining-production/initialize

Response:
{
  "status": "initialized",
  "message": "Mining gateway initialized successfully",
  "health": {
    "initialized": true,
    "running": false,
    "status": "healthy",
    "stats": { ... },
    "pools": { ... }
  }
}
```

### Start Mining

```bash
POST /api/v1/mining-production/start

Response:
{
  "status": "started",
  "message": "Mining operations started",
  "health": {
    "initialized": true,
    "running": true,
    "status": "healthy",
    ...
  }
}
```

### Get Status

```bash
GET /api/v1/mining-production/status

Response:
{
  "initialized": true,
  "running": true,
  "status": "healthy",
  "stats": {
    "total_shares_submitted": 150,
    "total_shares_accepted": 142,
    "total_shares_rejected": 8,
    "global_acceptance_rate": 0.9467,
    "active_pools": 2,
    "healthy_pools": 2,
    "degraded_pools": 0,
    "offline_pools": 1,
    "total_pools": 3,
    ...
  },
  "pools": {
    "pool_1": {
      "pool_name": "NiceHash",
      "pool_url": "stratum+ssl://...",
      "health": "healthy",
      "shares_submitted_total": 100,
      "shares_accepted_total": 95,
      ...
    },
    ...
  }
}
```

### Get Pool Health

```bash
GET /api/v1/mining-production/health?pool_id=pool_1

Response:
{
  "pool_health": {
    "pool_1": {
      "pool_name": "NiceHash",
      "pool_url": "stratum+ssl://btc.nicehash.com:3334",
      "health": "healthy",
      "connection_state": "AUTHENTICATED",
      "last_job_time": 1718000000.0,
      "last_share_time": 1718000050.0,
      "shares_submitted_total": 100,
      "shares_accepted_total": 95,
      "shares_rejected_total": 5,
      ...
    }
  },
  "timestamp": null
}
```

### Get Next Mining Job

```bash
GET /api/v1/mining-production/next-job

Response:
{
  "job_available": true,
  "job": {
    "job_id": "12345",
    "prevhash": "abc123...",
    "version": "00000001",
    "nbits": "1a00ffff",
    "ntime": "63a5f0ff",
    "clean_jobs": false
  }
}
```

### Submit Share

```bash
POST /api/v1/mining-production/submit-share

Request:
{
  "job_id": "12345",
  "nonce": 1234567890,
  "extranonce2": "00000001"
}

Response:
{
  "accepted": true,
  "message": "Share submitted successfully"
}
```

### Get Mining Metrics

```bash
GET /api/v1/mining-production/metrics

Response:
{
  "metrics": {
    "total_shares_submitted": 1000,
    "total_shares_accepted": 947,
    "total_shares_rejected": 53,
    "global_acceptance_rate": 0.947,
    "active_pools": 2,
    ...
  },
  "pools": { ... }
}
```

## Deployment

### Pre-Deployment Validation

Run the deployment gate to validate configuration:

```bash
python scripts/production_mining_deployment_gate.py
```

This validates:
- Environment configuration correctness
- Pool connectivity
- Mining operations
- Share submission

### Docker Deployment

Example Docker Compose configuration:

```yaml
version: '3.8'

services:
  hyba-mining:
    image: hyba-fullstack:latest
    environment:
      NODE_ENV: production
      HYBA_POOL_1_NAME: "NiceHash"
      HYBA_POOL_1_URL: "stratum+ssl://btc.nicehash.com:3334"
      HYBA_POOL_1_USERNAME: ${POOL_USERNAME}
      HYBA_POOL_1_PASSWORD: ${POOL_PASSWORD}
      HYBA_POOL_2_NAME: "ViaBTC"
      HYBA_POOL_2_URL: "stratum+ssl://btc.viabtc.com:3333"
      HYBA_POOL_2_USERNAME: ${POOL_2_USERNAME}
      HYBA_POOL_2_PASSWORD: ${POOL_2_PASSWORD}
      HYBA_MINING_STRATEGY: failover
    ports:
      - "3001:3001"  # API
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/api/v1/mining-production/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "10"
```

### Kubernetes Deployment

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hyba-mining
  labels:
    app: hyba-mining
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hyba-mining
  template:
    metadata:
      labels:
        app: hyba-mining
    spec:
      containers:
      - name: mining
        image: hyba-fullstack:latest
        env:
        - name: NODE_ENV
          value: "production"
        - name: HYBA_POOL_1_NAME
          value: "NiceHash"
        - name: HYBA_POOL_1_URL
          value: "stratum+ssl://btc.nicehash.com:3334"
        - name: HYBA_POOL_1_USERNAME
          valueFrom:
            secretKeyRef:
              name: mining-secrets
              key: pool-1-username
        - name: HYBA_POOL_1_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mining-secrets
              key: pool-1-password
        ports:
        - containerPort: 3001
        livenessProbe:
          httpGet:
            path: /api/v1/mining-production/status
            port: 3001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/mining-production/status
            port: 3001
          initialDelaySeconds: 10
          periodSeconds: 5
```

## Monitoring

### Health Check Endpoints

Regular health checks:

```bash
# Every 30 seconds
curl http://localhost:3001/api/v1/mining-production/status

# Per-pool health
curl http://localhost:3001/api/v1/mining-production/health
```

### Metrics Collection

Prometheus-compatible metrics endpoint:

```bash
curl http://localhost:3001/metrics
```

### Logging

Structured logs are written to stdout with timestamps, levels, and context:

```
2024-06-18T12:34:56 - pythia_mining.production_mining_orchestrator - INFO - Initializing mining orchestrator with 3 pools
2024-06-18T12:34:57 - pythia_mining.stratum_client - INFO - Connecting via Stratum v1 to pool NiceHash
2024-06-18T12:35:00 - pythia_mining.production_mining_orchestrator - INFO - Pool NiceHash health changed: unknown -> healthy
```

## Troubleshooting

### Pool Connection Issues

**Problem**: "Failed to connect to pool"

**Solutions**:
1. Verify pool URL and credentials
2. Check network connectivity: `telnet btc.nicehash.com 3334`
3. Check firewall rules allow outbound to pool
4. Verify credentials are correct on pool website

### Low Share Acceptance Rate

**Problem**: "Global acceptance rate is < 90%"

**Solutions**:
1. Verify mining difficulty matches target
2. Check pool connection latency
3. Verify nonce generation correctness
4. Check for clock skew (NTP sync)

### Pools Going Offline

**Problem**: "Pool marked offline after 10 failures"

**Solutions**:
1. Check pool status page
2. Try alternative pools
3. Verify credentials haven't changed
4. Check for pool maintenance

## Best Practices

1. **Use Multiple Pools**: Configure at least 2 pools for failover
2. **Monitor Metrics**: Check acceptance rate regularly (target > 95%)
3. **Test Before Deployment**: Run deployment gate before going live
4. **Use TLS**: Always use `stratum+ssl://` or `stratum+tls://` when available
5. **Rotate Passwords**: Change pool passwords periodically
6. **Track Earnings**: Monitor shares accepted per pool to optimize strategy

## Performance Tuning

### Share Submission Strategy

- **Failover** (default): Best for single-pool focus with backup
- **Multi-pool**: Best for maximum share acceptance
- **First-pool**: Best for dedicated single-pool mining

### Health Check Interval

- **10 seconds**: Aggressive monitoring (higher CPU)
- **30 seconds**: Balanced (recommended)
- **60 seconds**: Conservative monitoring (lower CPU)

## Security Considerations

1. **Credentials**: Use environment variables or secrets management
2. **TLS/SSL**: Always use encrypted connections to pools
3. **Rate Limiting**: API has built-in rate limiting
4. **Audit Logging**: All operations are logged for audit trail

## Production Readiness Checklist

- [ ] Environment variables configured for all pools
- [ ] Credentials verified and secure
- [ ] Deployment gate passes successfully
- [ ] At least 2 pools configured for failover
- [ ] Monitoring and alerting configured
- [ ] Logs centralized and monitored
- [ ] Backup/recovery procedures tested
- [ ] Performance benchmarked and meets targets

## Support & Troubleshooting

For issues:
1. Check the logs: `docker logs hyba-mining`
2. Run deployment gate: `python scripts/production_mining_deployment_gate.py`
3. Check API status: `curl http://localhost:3001/api/v1/mining-production/status`
4. Review pool credentials and connectivity

## Example: Complete Setup

```bash
#!/bin/bash

# 1. Configure pools
export HYBA_POOL_1_NAME="NiceHash"
export HYBA_POOL_1_URL="stratum+ssl://btc.nicehash.com:3334"
export HYBA_POOL_1_USERNAME="34HKwkSmM2VNSVQ4XvCvYqWjV5YSKzS6mF"
export HYBA_POOL_1_PASSWORD="x"

export HYBA_POOL_2_NAME="ViaBTC"
export HYBA_POOL_2_URL="stratum+ssl://btc.viabtc.com:3333"
export HYBA_POOL_2_USERNAME="username.worker"
export HYBA_POOL_2_PASSWORD="password"

# 2. Set production mode
export NODE_ENV="production"

# 3. Start backend
npm run backend:start &

# 4. Wait for backend to be ready
sleep 10

# 5. Run validation gate
python scripts/production_mining_deployment_gate.py

# 6. Initialize mining
curl -X POST http://localhost:3001/api/v1/mining-production/initialize

# 7. Start mining
curl -X POST http://localhost:3001/api/v1/mining-production/start

# 8. Monitor status
watch -n 5 'curl -s http://localhost:3001/api/v1/mining-production/status | jq .'
```

---

For questions or issues, refer to the main README or contact support.
