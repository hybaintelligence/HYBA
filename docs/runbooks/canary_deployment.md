# Canary Deployment Runbook

## Purpose
This runbook defines the canary deployment process for mining algorithm updates to minimize risk and enable rapid rollback if issues are detected.

## Canary Strategy Overview

**Deployment Pattern**: Blue-Green with Canary Phase
- **Canary Duration**: 30 minutes minimum
- **Canary Traffic Split**: 10% initial, 50% after 15 minutes if healthy
- **Rollback Trigger**: Any P0/P1 alert or manual intervention
- **Success Criteria**: Zero circuit breaker trips, <5% latency increase, stable share acceptance rate

## Pre-Deployment Checklist

**Code Readiness:**
- [ ] All CI checks passing (runtime guardrails, backend tests, frontend build)
- [ ] Docker image builds successfully
- [ ] Version tag created and pushed
- [ ] Change control ticket approved
- [ ] Security review completed for code changes

**Operational Readiness:**
- [ ] On-call engineer notified and available
- [ ] Monitoring dashboards prepared
- [ ] Rollback procedure documented and tested
- [ ] Backup pool credentials verified
- [ ] Emergency stop procedure validated

**Mining State:**
- [ ] Current mining operations stable
- [ ] Pool connection healthy
- [ ] Share acceptance rate >95%
- [ ] No active incidents

## Canary Deployment Process

### Phase 1: Preparation (5 minutes)

```bash
# Tag the new version
git tag -a v2.1.1 -m "Canary deployment: quantum optimization update"
git push origin v2.1.1

# Build canary image
docker build -t hyba-fullstack:v2.1.1-canary .

# Verify image
docker images | grep hyba-fullstack
```

### Phase 2: Canary Launch (10 minutes)

```bash
# Deploy canary instance (10% traffic)
docker-compose -f docker-compose.canary.yml up -d

# Verify canary health
curl http://127.0.0.1:3001/bridge/health
curl http://127.0.0.1:3001/api/health/readiness

# Check canary logs
docker-compose -f docker-compose.canary.yml logs -f --tail=50
```

### Phase 3: Traffic Splitting (30 minutes)

**Initial 10% Traffic (0-15 minutes):**
```bash
# Update load balancer to route 10% traffic to canary
# (Implementation depends on your load balancer)

# Monitor key metrics:
# - Circuit breaker status (should remain closed)
# - Backend latency (should not increase >5%)
# - Share acceptance rate (should remain >95%)
# - Error rate (should remain <1%)
```

**Increased 50% Traffic (15-30 minutes):**
```bash
# If metrics healthy, increase to 50% traffic
# Update load balancer configuration

# Continue monitoring with increased scrutiny
# Pay special attention to quantum operation timing
# Monitor PULVINI manifold convergence
```

### Phase 4: Full Cutover (5 minutes)

```bash
# If canary healthy for 30 minutes:
# - Zero circuit breaker trips
# - Latency increase <5%
# - Share acceptance rate stable
# - No error spikes

# Proceed to full deployment
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# Verify full deployment
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status
```

## Monitoring During Canary

**Critical Metrics (Alert Immediately):**
```bash
# Circuit breaker status
curl -H "X-HYBA-Internal-Token: $TOKEN" http://127.0.0.1:3000/bridge/internal/health | jq '.circuitBreakerOpen'

# Backend latency
curl http://127.0.0.1:3001/api/health/readiness

# Mining status
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# Share acceptance rate
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/ops/metrics
```

**Warning Metrics (Monitor Closely):**
- Quantum operation timing (should remain <1ms per operation)
- PULVINI manifold convergence (should maintain pure state)
- Pool latency (should not increase >20%)
- Memory usage (should not increase >15%)

## Rollback Procedure

**Immediate Rollback Triggers:**
- Circuit breaker trips
- Share acceptance rate drops below 90%
- Backend latency increases >20%
- Quantum operation failures
- Pool connection failures
- Manual intervention request

**Rollback Steps:**
```bash
# 1. Immediate traffic shift back to stable
# Update load balancer to route 100% traffic to stable version

# 2. Stop canary instance
docker-compose -f docker-compose.canary.yml down

# 3. Verify stable version is healthy
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness

# 4. Check mining operations
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# 5. Document rollback
# Create incident ticket with:
# - Time of rollback
# - Trigger reason
# - Metrics at rollback time
# - Canary version rolled back from
```

## Post-Deployment Validation

**Immediate (5 minutes):**
```bash
# Health checks
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness

# Mining operations
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# Check logs for errors
docker-compose -f docker-compose.production.yml logs --tail=100
```

**Short-term (30 minutes):**
- Monitor circuit breaker status
- Track share acceptance rate
- Verify pool connection stability
- Check quantum operation timing
- Review error logs

**Long-term (24 hours):**
- Review overall performance metrics
- Compare to baseline performance
- Check for any delayed issues
- Update runbooks if needed

## Canary-Specific Configurations

**Environment Variables for Canary:**
```bash
# Canary-specific settings
HYBA_DEPLOYMENT_MODE=canary
HYBA_CANARY_INSTANCE_ID=canary-001
HYBA_METRICS_PREFIX=canary

# Conservative settings for canary
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
BACKEND_PROXY_TIMEOUT_MS=15000  # Shorter timeout for faster failure detection
```

**Docker Compose for Canary:**
```yaml
# docker-compose.canary.yml
services:
  hyba-backend-canary:
    image: hyba-fullstack:v2.1.1-canary
    environment:
      NODE_ENV: production
      HYBA_DEPLOYMENT_MODE: canary
      HYBA_CANARY_INSTANCE_ID: canary-001
    ports:
      - "3002:3001"  # Different port for canary
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://127.0.0.1:3001/api/health/readiness"]
      interval: 5s   # More frequent checks for canary
      timeout: 2s
      retries: 3
```

## Success Criteria

**Must Pass:**
- Zero circuit breaker trips during canary period
- Share acceptance rate remains >95%
- Backend latency increase <5%
- No pool connection failures
- Zero quantum operation errors

**Should Pass:**
- Memory usage increase <15%
- CPU usage increase <10%
- No error rate increase
- Stable PULVINI manifold convergence

## Communication

**Pre-Deployment:**
- Notify on-call team 30 minutes before
- Update status page: "Canary deployment in progress"
- Notify stakeholders of maintenance window

**During Canary:**
- Provide status updates every 15 minutes
- Alert immediately on rollback triggers
- Maintain communication channel for quick decisions

**Post-Deployment:**
- Update status page: "Deployment complete"
- Send summary to stakeholders
- Document any issues or learnings

## Emergency Contacts

- On-call Engineering: [CONTACT]
- DevOps Lead: [CONTACT]
- Mining Operations: [CONTACT]
- Executive Team: [CONTACT]

## Appendix: Canary Monitoring Script

```bash
#!/bin/bash
# monitor_canary.sh - Monitor canary deployment health

TOKEN=$1
BACKEND_URL=$2
INTERVAL=30

echo "Starting canary monitoring..."
echo "Backend URL: $BACKEND_URL"
echo "Check interval: ${INTERVAL}s"

while true; do
  # Health check
  HEALTH=$(curl -s http://127.0.0.1:3000/bridge/health)
  STATUS=$(echo $HEALTH | jq -r '.status')
  
  # Circuit breaker
  CIRCUIT=$(curl -s -H "X-HYBA-Internal-Token: $TOKEN" http://127.0.0.1:3000/bridge/internal/health)
  CIRCUIT_OPEN=$(echo $CIRCUIT | jq -r '.circuitBreakerOpen')
  
  # Mining status
  MINING=$(curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status)
  
  echo "[$(date)] Status: $STATUS, Circuit Open: $CIRCUIT_OPEN"
  
  if [ "$CIRCUIT_OPEN" = "true" ]; then
    echo "🚨 CIRCUIT BREAKER OPEN - INITIATE ROLLBACK"
    exit 1
  fi
  
  if [ "$STATUS" != "ok" ]; then
    echo "⚠️  Health check failed - investigate"
  fi
  
  sleep $INTERVAL
done
```

## Lessons Learned Template

After each canary deployment, document:

**Deployment Details:**
- Version: ___
- Date: ___
- Canary Duration: ___
- Traffic Split: ___

**Issues Encountered:**
- Issue 1: ___
- Issue 2: ___

**Rollback Required:** Yes/No
- If yes, reason: ___

**Performance Impact:**
- Latency change: ___
- Error rate change: ___
- Share acceptance rate: ___

**Recommendations for Next Time:**
- ___
- ___
