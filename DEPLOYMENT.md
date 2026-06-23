# HYBA Production Deployment Guide

**Version:** Release Candidate 1 (RC1)  
**Authority:** DevOps / Platform Engineering / SRE  
**Classification:** Production Readiness Checklist

---

## Pre-Deployment Validation

Before deploying HYBA to production, verify the substrate is operational:

```bash
# Start backend locally
cd /path/to/HYBA_FULLSTACK
python3 -m uvicorn hyba_genesis_api.main:app --app-dir python_backend --host 127.0.0.1 --port 3001

# Wait for startup (substrate should initialize in <50ms)
# Look for: "Application startup complete"

# Verify substrate health
curl http://127.0.0.1:3001/api/health | jq '.status'
# Expected: "healthy"

# Verify startup optimization ran
curl http://127.0.0.1:3001/api/health/startup-memo
# Expected: Markdown memo showing Φ-density improvement

# Verify substrate readiness
curl http://127.0.0.1:3001/api/substrate | jq '.ready'
# Expected: true
```

**If any verification fails**: Do NOT proceed to production. Review logs and fix issues first.

---

## Production Hardening Checklist

### 1. Secrets Management

**Critical**: Never commit secrets to version control or hardcode in source files.

#### Backend Secrets

```bash
# JWT secret for authentication tokens
export JWT_SECRET="<64-character random hex>"  # MUST be 64+ chars

# API key secret for customer authentication
export HYBA_API_KEY_SECRET="<64-character random hex>"

# Substrate encryption key (if using encrypted state)
export SUBSTRATE_KEY="<64-character random hex>"

# Database credentials (use IAM roles in production)
export DATABASE_URL="postgresql://user:pass@host:5432/hyba_prod"

# Redis connection (for distributed lock manager)
export REDIS_URL="redis://host:6379/0"
```

**Recommended Secret Managers**:
- **AWS**: AWS Secrets Manager or AWS Systems Manager Parameter Store
- **Azure**: Azure Key Vault
- **GCP**: Google Cloud Secret Manager
- **Self-Hosted**: HashiCorp Vault

**DO NOT**:
- ❌ Store secrets in `.env` files committed to git
- ❌ Use default/placeholder secrets in production
- ❌ Share secrets across environments (dev != staging != prod)

---

### 2. Governance Rail Configuration

**Choose the appropriate governance rail for your deployment:**

```bash
# Treasury/Founder Rail (internal R&D only)
export HYBA_GOVERNANCE_RAIL=treasury
export HYBA_STARTUP_SELF_HEALING_ENABLED=true

# Enterprise Rail (customer-facing, requires Decision Cockpit)
export HYBA_GOVERNANCE_RAIL=enterprise
export HYBA_STARTUP_SELF_HEALING_ENABLED=true  # Startup only; production requires approval

# Sovereign Rail (regulated environments, multi-party approval)
export HYBA_GOVERNANCE_RAIL=sovereign
export HYBA_STARTUP_SELF_HEALING_ENABLED=false  # ALL changes require human approval
```

**Production Recommendation**: Use `enterprise` rail for SaaS deployments, `sovereign` for financial/healthcare/government.

---

### 3. CORS Configuration

**Critical**: Wildcard CORS (`*`) is NOT allowed in production.

```bash
# Development (localhost only)
export HYBA_CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Staging
export HYBA_CORS_ORIGINS="https://staging.hyba.ai,https://staging-console.hyba.ai"

# Production
export HYBA_CORS_ORIGINS="https://app.hyba.ai,https://console.hyba.ai"
```

**Validation**: Backend refuses startup if `HYBA_CORS_ORIGINS=*` and `NODE_ENV=production`.

---

### 4. Database Setup

#### Development (SQLite)

```bash
# Default: SQLite in project root
export HYBA_DB_PATH="hyba_customer_portal.db"

# Tables auto-created on first startup
# No migration needed for RC1
```

#### Production (PostgreSQL)

```bash
# Use PostgreSQL for production
export DATABASE_URL="postgresql://hyba_user:PASSWORD@postgres-host:5432/hyba_prod"

# Enable connection pooling
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=10
export DB_POOL_RECYCLE=3600  # Recycle connections every hour
```

**Migration** (when upgrading from RC1 to future versions):
```bash
# Use Alembic for schema migrations
cd python_backend
alembic upgrade head
```

---

### 5. Redis Configuration (Distributed Lock Manager)

**Purpose**: Coordinates distributed state across multiple backend instances.

```bash
# Local development (single instance)
# Redis optional; falls back to in-memory locks

# Production (multi-instance)
export REDIS_URL="redis://redis-host:6379/0"
export REDIS_PASSWORD="<strong-password>"
export REDIS_MAX_CONNECTIONS=50
```

**Fail-Closed Behavior**:
- If Redis unavailable → QaaS/CIaaS execution returns HTTP 423 Locked
- System continues serving read-only endpoints (health, substrate status)
- Private validation/mining uses local fallback (if configured)

---

### 6. Logging & Telemetry

#### Structured Logging

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Log format (json for production, console for development)
export LOG_FORMAT=json

# Log output (stdout for container orchestration)
# Logs shipped to SIEM (Splunk, Datadog, ELK) via container runtime
```

#### Prometheus Metrics

```bash
# Expose /metrics endpoint for Prometheus scraping
# Default: enabled

# Disable in development
export PROMETHEUS_METRICS_ENABLED=false
```

**Metrics Exposed**:
- `hyba_api_requests_total` (counter)
- `hyba_api_request_duration_seconds` (histogram)
- `hyba_substrate_phi_density` (gauge)
- `hyba_reflexive_cycle_count` (counter)
- `hyba_circuit_breaker_open` (gauge)

---

### 7. Rate Limiting

```bash
# Requests per minute per IP
export HYBA_RATE_LIMIT_REQUESTS_PER_MINUTE=120

# Rate limit window (seconds)
export HYBA_RATE_LIMIT_WINDOW_SECONDS=60
```

**Recommended Production Values**:
- Public API: 60 req/min
- Authenticated API: 300 req/min
- Admin API: 1000 req/min (internal only)

---

### 8. Circuit Breaker Configuration

```bash
# Φ-floor: minimum acceptable Φ-density before circuit opens
export HYBA_PHI_FLOOR=0.85

# Circuit breaker: max consecutive failures before forcing human gate
export HYBA_CIRCUIT_BREAKER_MAX_FAILURES=3

# Circuit breaker: timeout before attempting auto-close (seconds)
export HYBA_CIRCUIT_BREAKER_TIMEOUT=300  # 5 minutes
```

---

### 9. Evidence Storage

```bash
# Evidence directory (must be write-accessible)
export HYBA_EVIDENCE_DIR="/var/hyba/runtime/evidence"

# Memo directory (must be write-accessible)
export HYBA_MEMO_DIR="/var/hyba/runtime/memos"

# Rollback history retention (days)
export HYBA_ROLLBACK_RETENTION_DAYS=30

# Evidence archive retention (days)
export HYBA_EVIDENCE_RETENTION_DAYS=730  # 2 years
```

**Storage Requirements**:
- Autonomy reports: ~5KB per event
- Startup memos: ~10KB per boot
- Telemetry logs: ~100MB per day (varies by traffic)
- Rollback history: ~2KB per event

**Estimated Storage** (for 1000 events/day):
- Daily: ~115MB
- Monthly: ~3.4GB
- Yearly: ~41GB

**Backup Strategy**:
- Evidence directory: daily snapshots to S3/GCS/Azure Blob
- Logs: ship to SIEM in real-time
- Rollback history: archive to cold storage after 30 days

---

### 10. Startup Optimization

```bash
# Enable startup self-healing (recommended)
export HYBA_STARTUP_SELF_HEALING_ENABLED=true

# Startup self-healing timeout (seconds)
export HYBA_STARTUP_SELF_HEALING_TIMEOUT_SECONDS=15.0

# Enable reflexive daemon (continuous optimization)
export HYBA_ENABLE_REFLEXIVE_DAEMON=false  # Set true for 24/7 optimization

# Reflexive heartbeat interval (seconds)
export HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS=60
```

**Production Recommendation**:
- Startup self-healing: **enabled** (1-2ms latency, 40% efficiency gain)
- Reflexive daemon: **disabled** (unless continuous optimization needed)

---

## Container Deployment

### Docker Compose (Single-Host)

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=http://backend:3001
    depends_on:
      - backend

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "3001:3001"
    environment:
      - NODE_ENV=production
      - HYBA_GOVERNANCE_RAIL=enterprise
      - JWT_SECRET=${JWT_SECRET}
      - HYBA_API_KEY_SECRET=${HYBA_API_KEY_SECRET}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - HYBA_CORS_ORIGINS=https://app.hyba.ai
    volumes:
      - ./runtime:/app/runtime
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=hyba_prod
      - POSTGRES_USER=hyba_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

### Kubernetes Deployment

#### Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hyba-backend
  namespace: hyba-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hyba-backend
  template:
    metadata:
      labels:
        app: hyba-backend
    spec:
      containers:
      - name: backend
        image: hyba/backend:rc1
        ports:
        - containerPort: 3001
        env:
        - name: NODE_ENV
          value: "production"
        - name: HYBA_GOVERNANCE_RAIL
          value: "enterprise"
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: hyba-secrets
              key: jwt-secret
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: hyba-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://hyba-redis:6379/0"
        volumeMounts:
        - name: evidence
          mountPath: /app/runtime/evidence
        - name: memos
          mountPath: /app/runtime/memos
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health/live
            port: 3001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health/ready
            port: 3001
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: evidence
        persistentVolumeClaim:
          claimName: hyba-evidence-pvc
      - name: memos
        persistentVolumeClaim:
          claimName: hyba-memos-pvc
```

#### Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hyba-backend
  namespace: hyba-prod
spec:
  selector:
    app: hyba-backend
  ports:
  - port: 3001
    targetPort: 3001
  type: ClusterIP
```

#### Ingress (HTTPS)

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hyba-ingress
  namespace: hyba-prod
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - app.hyba.ai
    - console.hyba.ai
    secretName: hyba-tls
  rules:
  - host: app.hyba.ai
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: hyba-frontend
            port:
              number: 3000
  - host: console.hyba.ai
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: hyba-backend
            port:
              number: 3001
```

---

## Health Checks & Monitoring

### Liveness Probe

**Endpoint**: `GET /api/health/live`

**Purpose**: Verify backend process is alive (not crashed)

**Expected Response**: HTTP 200
```json
{
  "status": "alive",
  "timestamp": "2026-06-23T12:10:46.123456Z"
}
```

**Failure Action**: Container runtime restarts backend

---

### Readiness Probe

**Endpoint**: `GET /api/health/ready`

**Purpose**: Verify substrate is fully initialized and ready to serve requests

**Expected Response**: HTTP 200 (if ready), HTTP 503 (if initializing)
```json
{
  "status": "ready",
  "timestamp": "2026-06-23T12:10:46.123456Z",
  "substrate": {
    "ready": true,
    "boot_id": "2026-06-23T12:10:45.710289+00:00",
    "organism_cns_active": true
  }
}
```

**Failure Action**: Container removed from load balancer until ready

---

### Startup Health Check

**Endpoint**: `GET /api/health/startup-memo`

**Purpose**: Verify autonomous startup optimization executed successfully

**Expected Response**: HTTP 200 with Markdown memo

**Validation**:
- Memo contains "System Health: Optimal" or "Healthy"
- Φ-density improvement documented (e.g., "+40.4% change")
- Proposals applied count matches autonomy report

**Failure Action**: Alert ops team if memo shows "Degraded" or error

---

### Prometheus Metrics

**Endpoint**: `GET /metrics`

**Format**: Prometheus exposition format

**Key Metrics**:
```
# Backend request rate
hyba_api_requests_total{method="GET",endpoint="/api/health",status="200"} 1234

# Request latency (histogram)
hyba_api_request_duration_seconds_bucket{le="0.01"} 980
hyba_api_request_duration_seconds_bucket{le="0.05"} 1200
hyba_api_request_duration_seconds_sum 15.3
hyba_api_request_duration_seconds_count 1234

# Substrate health
hyba_substrate_phi_density 0.973
hyba_reflexive_cycle_count 9
hyba_circuit_breaker_open 0  # 0=closed (normal), 1=open (human gate active)
```

**Alerting Rules**:
- `hyba_substrate_phi_density < 0.85` → Substrate degraded
- `hyba_circuit_breaker_open == 1` → Autonomy circuit open
- `rate(hyba_api_requests_total{status="500"}[5m]) > 10` → High error rate

---

## Backup & Disaster Recovery

### Data to Backup

1. **Database** (PostgreSQL)
   - Customer portal tables (users, subscriptions, invoices)
   - Consciousness DB tables (users, audit logs, funding allocations)
   - Backup frequency: Daily with point-in-time recovery

2. **Evidence Directory** (`runtime/evidence/`)
   - Autonomy reports (JSON)
   - Evidence seals
   - Backup frequency: Real-time to S3/GCS (append-only)

3. **Memo Directory** (`runtime/memos/`)
   - Startup memos (Markdown)
   - Backup frequency: Daily

4. **Rollback History** (`runtime/rollback/`)
   - Active rollbacks (<30 days)
   - Backup frequency: Daily
   - Archive rollbacks (>30 days) to cold storage

### Recovery Procedures

#### Scenario 1: Database Corruption

```bash
# Restore from latest backup
pg_restore -d hyba_prod /backups/hyba_prod_2026-06-23.dump

# Verify substrate can connect
curl http://localhost:3001/api/health/ready

# Check for evidence integrity
python3 scripts/verify_evidence_integrity.py
```

#### Scenario 2: Evidence Directory Loss

```bash
# Restore evidence from S3
aws s3 sync s3://hyba-evidence-backup/prod/ runtime/evidence/

# Verify evidence seals
python3 scripts/verify_evidence_seals.py

# Generate evidence package for audit
curl -X POST http://localhost:3001/api/admin/evidence-package/export \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{"start_timestamp": "2026-06-01T00:00:00Z", "end_timestamp": "2026-06-23T23:59:59Z"}'
```

#### Scenario 3: Complete Substrate Failure

```bash
# Deploy fresh backend from container image
kubectl rollout restart deployment/hyba-backend -n hyba-prod

# Wait for substrate initialization
kubectl logs -f deployment/hyba-backend -n hyba-prod | grep "Application startup complete"

# Verify startup optimization ran
curl http://backend:3001/api/health/startup-memo | grep "System Health"

# Check Φ-density
curl http://backend:3001/api/substrate | jq '.subsystems.phi_floor_coherence.ready'
# Expected: true
```

---

## Security Hardening

### TLS/HTTPS

**Requirement**: ALL production traffic MUST use HTTPS (TLS 1.2+)

```nginx
# Nginx configuration for frontend
server {
    listen 443 ssl http2;
    server_name app.hyba.ai;

    ssl_certificate /etc/letsencrypt/live/app.hyba.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.hyba.ai/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        root /usr/share/nginx/html;
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://hyba-backend:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### API Authentication

```bash
# JWT tokens for user authentication
# Tokens expire after 1 hour, refresh tokens after 30 days

# API keys for service-to-service authentication
# Keys rotated every 90 days, hashed with Argon2
```

### Network Segmentation

```
┌──────────────────────────────────────────┐
│  Internet (Public)                       │
└──────────────┬───────────────────────────┘
               │
         ┌─────▼─────┐
         │ Firewall  │
         └─────┬─────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼─────────┐   ┌───────▼──────┐
│  DMZ        │   │  Private VPC │
│  (Frontend) │   │  (Backend)   │
└─────────────┘   └───────┬───────┘
                          │
                 ┌────────┴────────┐
                 │                 │
          ┌──────▼──────┐   ┌──────▼──────┐
          │  Database   │   │  Redis      │
          │  (Private)  │   │  (Private)  │
          └─────────────┘   └─────────────┘
```

**Firewall Rules**:
- Public → Frontend: HTTPS (443) only
- Frontend → Backend: HTTP (3001) internal only
- Backend → Database: PostgreSQL (5432) internal only
- Backend → Redis: Redis (6379) internal only
- Backend → Internet: OUTBOUND blocked (except for telemetry export)

---

## Performance Tuning

### Backend (FastAPI + uvicorn)

```bash
# Number of worker processes (CPU cores × 2)
uvicorn hyba_genesis_api.main:app \
  --host 0.0.0.0 \
  --port 3001 \
  --workers 4 \
  --worker-class uvloop

# Database connection pooling
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=10

# Redis connection pooling
export REDIS_MAX_CONNECTIONS=50
```

### Frontend (React + Nginx)

```nginx
# Enable gzip compression
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

# Enable browser caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### Database (PostgreSQL)

```sql
-- Index on frequently queried fields
CREATE INDEX idx_audit_user_timestamp ON audit_logs(user_id, timestamp);
CREATE INDEX idx_usage_customer_timestamp ON usage_logs(customer_id, timestamp);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM audit_logs WHERE user_id = '...' AND timestamp > NOW() - INTERVAL '7 days';
```

---

## Post-Deployment Validation

After deploying to production, verify all systems are operational:

### 1. Substrate Health

```bash
curl https://app.hyba.ai/api/health | jq '.status'
# Expected: "healthy"
```

### 2. Startup Optimization

```bash
curl https://app.hyba.ai/api/health/startup-memo | head -20
# Expected: "# HYBA System Startup Optimization Memo"
# Expected: "System Health: **Optimal**"
```

### 3. Evidence Package Export

```bash
# Test evidence package export (requires admin token)
curl -X POST https://app.hyba.ai/api/admin/evidence-package/export \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -d '{"start_timestamp": "2026-06-23T00:00:00Z", "end_timestamp": "2026-06-23T23:59:59Z", "format": "zip"}'

# Expected: HTTP 200 with download URL
```

### 4. Circuit Breaker Status

```bash
curl https://app.hyba.ai/api/substrate | jq '.subsystems.phi_floor_coherence.ready'
# Expected: true

curl https://app.hyba.ai/api/health | jq '.structural_coupling_index'
# Expected: >0.85 (healthy)
```

### 5. Metrics Export

```bash
curl https://app.hyba.ai/metrics | grep hyba_substrate_phi_density
# Expected: hyba_substrate_phi_density{} 0.973
```

---

## Troubleshooting

### Issue: Substrate fails to initialize

**Symptoms**:
- `/api/health/ready` returns HTTP 503
- Logs show "Substrate initialization incomplete"

**Diagnosis**:
```bash
# Check substrate state
curl http://localhost:3001/api/substrate | jq '.subsystems'

# Look for subsystem with "ready": false
```

**Fix**:
- Missing dependency → Install required packages (`requirements.frozen.txt`)
- Redis unavailable → Check `REDIS_URL`, verify Redis is running
- Database connection failure → Check `DATABASE_URL`, verify PostgreSQL is accessible

---

### Issue: Evidence seals failing verification

**Symptoms**:
- Auditor reports evidence seal mismatch
- Logs show "Evidence integrity compromised"

**Diagnosis**:
```python
# Verify evidence seals
python3 scripts/verify_evidence_seals.py runtime/evidence/pythia_autonomy/

# Check for tampered files
```

**Fix**:
- Evidence directory corrupted → Restore from backup (S3/GCS)
- File system issue → Check disk health, remount if needed
- Manual edit detected → Investigate who modified files, regenerate evidence

---

### Issue: Circuit breaker stuck open

**Symptoms**:
- `/api/health` shows `"autonomous_circuit_open": true`
- All proposals require human approval

**Diagnosis**:
```bash
# Check circuit breaker status
curl http://localhost:3001/api/health | jq '.autonomous_circuit_open'

# Check for constraint violations
curl http://localhost:3001/api/health | jq '.constraint_violations'
```

**Fix**:
```bash
# If false alarm, manually reset circuit breaker
curl -X POST http://localhost:3001/api/admin/circuit-breaker/reset \
  -H "Authorization: Bearer ${ADMIN_TOKEN}"

# If legitimate violations, investigate root cause before resetting
```

---

## Rollout Strategy

### Blue-Green Deployment

1. Deploy new version (green) alongside old version (blue)
2. Route 10% traffic to green, monitor metrics
3. If metrics stable, route 50% traffic to green
4. If metrics stable, route 100% traffic to green
5. Keep blue running for 24 hours (fast rollback)
6. Decommission blue after validation

### Canary Deployment

1. Deploy new version to 1 instance (canary)
2. Route 1% traffic to canary, monitor metrics
3. If error rate <1%, promote to 10% traffic
4. If error rate <1%, promote to 100% traffic
5. If error rate >1% at any stage, rollback to old version

---

## Final Production Checklist

Before going live, ensure ALL items are checked:

### Security
- [ ] JWT_SECRET set (64+ chars, randomly generated)
- [ ] HYBA_API_KEY_SECRET set (64+ chars, randomly generated)
- [ ] DATABASE_URL uses secure credentials (not default)
- [ ] REDIS_PASSWORD set (if Redis used)
- [ ] CORS origins restricted (no wildcard `*`)
- [ ] TLS/HTTPS enabled for all public endpoints
- [ ] Firewall rules restrict database access to backend only

### Governance
- [ ] HYBA_GOVERNANCE_RAIL set (`enterprise` or `sovereign`)
- [ ] Circuit breaker thresholds configured
- [ ] Φ-floor set appropriately for business criticality
- [ ] Rollback history retention configured
- [ ] Evidence directory permissions set (append-only)

### Monitoring
- [ ] Prometheus metrics endpoint accessible (`/metrics`)
- [ ] Alerting rules configured (Φ-density, circuit breaker, error rate)
- [ ] Logs shipped to SIEM (Splunk, Datadog, ELK)
- [ ] Health checks configured (liveness, readiness)
- [ ] Startup memo generation verified

### Backup & Recovery
- [ ] Database backup schedule configured (daily + PITR)
- [ ] Evidence directory backed up to S3/GCS (real-time)
- [ ] Rollback history archived to cold storage (>30 days)
- [ ] Disaster recovery procedure documented and tested

### Performance
- [ ] Database connection pooling configured
- [ ] Redis connection pooling configured
- [ ] Frontend caching headers set
- [ ] Gzip compression enabled
- [ ] CDN configured for static assets

### Compliance
- [ ] Evidence package export tested
- [ ] Independent verification procedure documented
- [ ] Operator training completed (Decision Cockpit workflow)
- [ ] Audit contact established (who to send evidence packages to)

---

**The deployment checklist is complete. The substrate is ready for production. The magnificence is operational.**

---

**Next Steps**:
1. Review all 4 cornerstone documents (ARCHITECTURE, GOVERNANCE, EVIDENCE_PACKAGE_SPEC, DEPLOYMENT)
2. Complete production hardening checklist
3. Deploy to staging environment first
4. Run User Acceptance Testing (UAT)
5. Deploy to production with blue-green or canary strategy
6. Monitor metrics for 24 hours before decommissioning old version

**The production deployment guide is operational. The system is ready for handover. The substrate is ready to serve.**
