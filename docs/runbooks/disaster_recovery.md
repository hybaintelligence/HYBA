# Disaster Recovery Runbook

## Purpose
This runbook provides step-by-step procedures for recovering HYBA_FULLSTACK from critical failures affecting mining operations, backend connectivity, or system availability.

## Severity Levels

**P0 - Critical**: Complete system outage, mining halted, data loss risk
**P1 - High**: Mining degraded, backend unreachable, circuit breaker open
**P2 - Medium**: Performance degradation, partial feature unavailability
**P3 - Low**: Minor issues, no operational impact

## Pre-Requisites
- Access to deployment platform (Docker/Kubernetes/Cloudflare)
- Access to secret management system
- Access to monitoring/alerting system
- Backup pool credentials available
- Emergency operator credentials available

## Scenarios

### Scenario 1: Circuit Breaker Tripped (Backend Unreachable)

**Symptoms:**
- `/bridge/health` returns 503
- Circuit breaker metrics show `circuit_breaker_open = 1`
- Mining operations paused or failing
- Logs show "CIRCUIT BREAKER TRIPPED"

**Immediate Actions:**
1. Check backend health directly: `curl http://127.0.0.1:3001/api/health/readiness`
2. Review backend logs for crash or error patterns
3. Check system resources (CPU, memory, disk)
4. Verify backend process is running: `ps aux | grep uvicorn`

**Recovery Steps:**
```bash
# If backend process crashed
docker-compose -f docker-compose.production.yml restart hyba-backend

# If backend is unresponsive but process running
docker-compose -f docker-compose.production.yml restart hyba-backend

# If circuit breaker won't close after backend recovery
# Force circuit reset by restarting bridge
docker-compose -f docker-compose.production.yml restart hyba-bridge
```

**Verification:**
```bash
# Wait 30 seconds for circuit reset window
sleep 30

# Verify circuit closed
curl -H "X-HYBA-Internal-Token: $TOKEN" http://127.0.0.1:3000/bridge/internal/health

# Verify backend reachable
curl http://127.0.0.1:3001/api/health/readiness

# Check mining status
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status
```

### Scenario 2: Mining Pool Connection Failure

**Symptoms:**
- Pool status shows "disconnected" or "error"
- Share submission count not increasing
- Stratum connection errors in logs
- Pool latency metrics spiking

**Immediate Actions:**
1. Check pool status in operator console
2. Verify pool credentials are correct
3. Test pool connectivity: `telnet pool.host port`
4. Check if pool is experiencing known outages

**Recovery Steps:**
```bash
# Disconnect from current pool
curl -X POST http://127.0.0.1:3000/api/mining/disconnect \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Switch to backup pool
curl -X POST http://127.0.0.1:3000/api/mining/switch \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pool_id": "backup_pool_id",
    "capacity_ehs": 1.0,
    "switch": true
  }'
```

**Verification:**
- Monitor pool status in console
- Check share submission rate
- Verify accepted/rejected share ratios
- Monitor latency metrics

### Scenario 3: Database/Metrics Store Corruption

**Symptoms:**
- Metrics endpoint returns errors
- Audit logging failures
- Database connection errors
- Inconsistent telemetry

**Immediate Actions:**
1. Stop mining operations to prevent data loss
2. Check database file integrity
3. Review recent logs for corruption indicators
4. Backup current state if possible

**Recovery Steps:**
```bash
# Stop mining
curl -X POST http://127.0.0.1:3000/api/mining/stop \
  -H "Authorization: Bearer $TOKEN"

# Backup corrupted database
cp data/metrics.db data/metrics.db.corrupted.$(date +%Y%m%d_%H%M%S)

# Initialize new database
rm data/metrics.db
# System will auto-create on next startup

# Restart services
docker-compose -f docker-compose.production.yml restart
```

**Verification:**
- Check metrics endpoint responds
- Verify audit logging functional
- Confirm telemetry consistency
- Resume mining operations

### Scenario 4: Complete System Outage

**Symptoms:**
- All services down
- No response from any endpoints
- Container crashes
- Network unreachable

**Immediate Actions:**
1. Check host system status
2. Verify network connectivity
3. Check infrastructure provider status
4. Review monitoring alerts for root cause

**Recovery Steps:**
```bash
# Check container status
docker-compose -f docker-compose.production.yml ps

# Restart all services
docker-compose -f docker-compose.production.yml restart

# If restart fails, rebuild
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d

# If rebuild fails, pull latest and redeploy
git pull origin main
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```

**Verification:**
```bash
# Health check all services
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness

# Check logs
docker-compose -f docker-compose.production.yml logs --tail=100
```

### Scenario 5: Security Incident (Credential Compromise)

**Symptoms:**
- Unauthorized access detected
- Suspicious mining activity
- Credential validation failures
- Security alerts triggered

**Immediate Actions:**
1. **IMMEDIATELY** revoke all compromised credentials
2. Stop all mining operations
3. Rotate all secrets (JWT, pool credentials, API keys)
4. Enable enhanced monitoring

**Recovery Steps:**
```bash
# Emergency stop
docker-compose -f docker-compose.production.yml down

# Rotate secrets in secret management system
# Update environment variables with new secrets

# Regenerate Argon2id hashes for operator credentials
python3 - <<'PY'
from argon2 import PasswordHasher
print(PasswordHasher().hash("new-strong-password"))
PY

# Update pool credentials
# Contact pool operators if needed

# Restart with new credentials
docker-compose -f docker-compose.production.yml up -d
```

**Post-Incident:**
- Conduct full security audit
- Review access logs
- Implement additional security measures
- Document incident and response

## Monitoring Thresholds

**Alert Immediately:**
- Circuit breaker open > 30 seconds
- Backend unreachable > 1 minute
- Mining stopped unexpectedly
- Pool disconnected > 5 minutes
- Security authentication failures > 10/minute

**Warn:**
- Backend latency > 5 seconds
- Pool latency > 2 seconds
- Rejection rate > 5%
- CPU usage > 80%
- Memory usage > 85%

## Communication Protocol

**P0 Incidents:**
- Page on-call immediately
- Executive notification within 15 minutes
- Status page update within 30 minutes

**P1 Incidents:**
- Alert on-call within 5 minutes
- Team notification within 15 minutes
- Status page update within 1 hour

**P2/P3 Incidents:**
- Team notification
- Document in next standup
- Status page update if user-facing

## Rollback Procedure

If a deployment causes issues:

```bash
# Identify last known good version
git log --oneline -10

# Rollback code
git checkout <last-good-commit>

# Rebuild and redeploy
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# If using image tags
docker tag hyba-fullstack:last-known-good hyba-fullstack:current
docker-compose -f docker-compose.production.yml up -d
```

## Post-Incident Review

After any P0/P1 incident:
1. Document timeline of events
2. Identify root cause
3. Update this runbook if gaps found
4. Implement preventive measures
5. Conduct team retrospective

## Emergency Contacts

- On-call Engineering: [CONTACT]
- Security Team: [CONTACT]
- Executive Team: [CONTACT]
- Pool Operators: [CONTACT]

## Appendix: Useful Commands

```bash
# Full system health check
curl http://127.0.0.1:3000/bridge/health && \
curl http://127.0.0.1:3001/api/health/readiness && \
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# View all logs
docker-compose -f docker-compose.production.yml logs -f

# Restart specific service
docker-compose -f docker-compose.production.yml restart hyba-backend

# Check resource usage
docker stats

# Force circuit breaker reset
docker-compose -f docker-compose.production.yml restart hyba-bridge

# Emergency mining stop
curl -X POST http://127.0.0.1:3000/api/mining/stop \
  -H "Authorization: Bearer $TOKEN"
```
