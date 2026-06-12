# Deployment Procedures Runbook

## Purpose
This runbook provides standardized procedures for deploying HYBA_FULLSTACK across environments (development, staging, production).

## Deployment Environments

**Development:**
- Purpose: Local development and testing
- Deployment: Manual `npm run dev`
- Data: Local mock data
- Mining: Disabled by default
- Access: localhost only

**Staging:**
- Purpose: Pre-production validation
- Deployment: Automated via CI/CD
- Data: Staging pool credentials
- Mining: Stratum connections (no live shares)
- Access: Authenticated operators only

**Production:**
- Purpose: Live mining operations
- Deployment: Automated via CI/CD with manual approval
- Data: Production pool credentials
- Mining: Live Stratum with share submission
- Access: Authenticated operators with role-based access

## Pre-Deployment Checklist

### Code Quality
- [ ] All CI checks passing (runtime guardrails, backend tests, frontend build)
- [ ] TypeScript compilation successful (`npm run lint`)
- [ ] Docker image builds successfully (`docker build -t hyba-fullstack:local .`)
- [ ] No TODO/FIXME comments in production code
- [ ] Security scan completed (if applicable)

### Testing
- [ ] Unit tests passing (`npm run test:backend`)
- [ ] Integration tests passing (`npm run test:e2e:backend`)
- [ ] Property-based tests passing (`npm run test:property`)
- [ ] Stratum v2 protocol tests passing
- [ ] Manual smoke test completed in staging

### Documentation
- [ ] CHANGELOG.md updated with version and changes
- [ ] Runbooks reviewed and updated if needed
- [ ] API documentation updated (if API changes)
- [ ] Migration guide provided (if breaking changes)

### Operations
- [ ] On-call engineer notified and available
- [ ] Monitoring dashboards prepared
- [ ] Rollback procedure documented
- [ ] Backup pool credentials verified
- [ ] Emergency stop procedure validated

### Security
- [ ] No hardcoded secrets in code
- [ ] Environment variables documented in .env.example
- [ ] JWT_SECRET configured for production
- [ ] Operator credentials use Argon2id hashes
- [ ] Pool credentials stored in secret manager

## Standard Deployment Process

### 1. Development Deployment

```bash
# Install dependencies
npm install
python -m pip install -r python_backend/requirements.txt
python -m pip install -r python_backend/hyba_genesis_api/requirements.txt

# Configure environment
cp config/mining.pools.example.env config/mining.pools.env
# Edit config/mining.pools.env with your credentials

# Run development server
npm run dev
```

### 2. Staging Deployment

```bash
# Run production readiness checks
npm run prod:check

# Build Docker image
docker build -t hyba-fullstack:staging .

# Tag for staging registry
docker tag hyba-fullstack:staging registry.hyba.example.com/hyba-fullstack:staging-$(date +%Y%m%d-%H%M%S)

# Push to registry
docker push registry.hyba.example.com/hyba-fullstack:staging-$(date +%Y%m%d-%H%M%S)

# Deploy to staging (via your orchestration platform)
# kubectl apply -f k8s/staging/
# or
# docker-compose -f docker-compose.staging.yml up -d
```

### 3. Production Deployment

#### Phase 1: Preparation
```bash
# Create release branch
git checkout -b release/v2.1.1

# Update version in package.json
# Update CHANGELOG.md

# Commit and push
git add .
git commit -m "Release v2.1.1"
git push origin release/v2.1.1

# Create pull request to main
# Get approval from code reviewer
```

#### Phase 2: CI/CD Pipeline
```bash
# CI automatically runs:
# - Runtime guardrails check
# - Backend regression tests
# - Frontend typecheck and build
# - Production config validation
# - Docker image build

# Manual approval required for production deployment
```

#### Phase 3: Pre-Deployment Validation
```bash
# Pull latest main
git checkout main
git pull origin main

# Verify production readiness
npm run prod:check

# Build production image locally for validation
docker build -t hyba-fullstack:v2.1.1 .

# Test image locally
docker run -p 3000:3000 -p 3001:3001 \
  -e NODE_ENV=production \
  -e HYBA_ENV=production \
  -e JWT_SECRET=test-secret \
  hyba-fullstack:v2.1.1
```

#### Phase 4: Production Deployment
```bash
# Tag release
git tag -a v2.1.1 -m "Release v2.1.1: [description]"
git push origin v2.1.1

# Deploy via orchestration platform
# Option 1: Docker Compose
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d

# Option 2: Kubernetes
kubectl set image deployment/hyba-backend \
  hyba-backend=registry.hyba.example.com/hyba-fullstack:v2.1.1

# Option 3: Cloudflare Pages (frontend only)
# Trigger deployment via Cloudflare dashboard or API
```

#### Phase 5: Post-Deployment Validation
```bash
# Health checks
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness

# Mining status (if mining enabled)
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# Check logs
docker-compose -f docker-compose.production.yml logs --tail=100

# Monitor metrics
curl -H "X-HYBA-Internal-Token: $TOKEN" http://127.0.0.1:3000/bridge/metrics
```

## Rollback Procedure

### Immediate Rollback Triggers
- Circuit breaker trips repeatedly
- Health checks fail
- Share acceptance rate drops below 90%
- Backend latency increases >50%
- Pool connection failures
- Security incident detected
- Manual intervention request

### Rollback Steps

#### Docker Compose Rollback
```bash
# Identify previous stable version
docker images | grep hyba-fullstack

# Stop current deployment
docker-compose -f docker-compose.production.yml down

# Rollback to previous version
docker tag hyba-fullstack:v2.1.0 hyba-fullstack:current
docker-compose -f docker-compose.production.yml up -d

# Verify rollback
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness
```

#### Kubernetes Rollback
```bash
# Check rollout history
kubectl rollout history deployment/hyba-backend

# Rollback to previous revision
kubectl rollout undo deployment/hyba-backend

# Verify rollback
kubectl rollout status deployment/hyba-backend
```

#### Code Rollback
```bash
# Identify last stable commit
git log --oneline -10

# Checkout stable commit
git checkout <stable-commit-hash>

# Rebuild and redeploy
docker build -t hyba-fullstack:stable .
docker-compose -f docker-compose.production.yml up -d
```

### Post-Rollback Validation
```bash
# Health checks
curl http://127.0.0.1:3000/bridge/health
curl http://127.0.0.1:3001/api/health/readiness

# Mining operations
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# Monitor for 15 minutes
# Check logs
docker-compose -f docker-compose.production.yml logs -f --tail=50
```

## Environment-Specific Configurations

### Development (.env)
```bash
NODE_ENV=development
HYBA_ENV=development
HYBA_ALLOW_DEV_FIXTURES=true
HYBA_ENABLE_LIVE_STRATUM=false
HYBA_ENABLE_MINING_AUTOCONNECT=false
```

### Staging
```bash
NODE_ENV=production
HYBA_ENV=staging
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
```

### Production
```bash
NODE_ENV=production
HYBA_ENV=production
HYBA_ALLOW_DEV_FIXTURES=false
HYBA_ENABLE_LIVE_STRATUM=true
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
HYBA_LIVE_SHARE_APPROVAL_ID=<approval-id>
```

## Database Migrations

### Migration Process
```bash
# Backup current database
cp data/metrics.db data/metrics.db.backup.$(date +%Y%m%d_%H%M%S)

# Run migration script
python3 scripts/migrate_database.py --version v2.1.1

# Verify migration
python3 scripts/verify_migration.py

# If migration fails, restore backup
cp data/metrics.db.backup.<timestamp> data/metrics.db
```

### Rollback Migration
```bash
# Identify migration version
python3 scripts/migration_status.py

# Rollback to previous version
python3 scripts/rollback_migration.py --version v2.1.0

# Verify rollback
python3 scripts/verify_migration.py
```

## Secret Management

### Adding New Secrets
```bash
# Never commit secrets to git
# Use environment variables or secret manager

# For local development, add to .env (gitignored)
echo "NEW_SECRET=value" >> .env

# For production, use secret manager
# AWS Secrets Manager: aws secretsmanager put-secret-value ...
# HashiCorp Vault: vault kv put secret/hyba/production ...
# Kubernetes: kubectl create secret generic hyba-secrets ...
```

### Rotating Secrets
```bash
# 1. Generate new secret
# 2. Update secret manager
# 3. Trigger rolling restart of services
# 4. Verify services use new secret
# 5. Remove old secret from secret manager
```

## Monitoring During Deployment

### Key Metrics to Monitor
- Circuit breaker status
- Backend latency
- Health check success rate
- Mining operation status
- Share acceptance rate
- Pool connection status
- Error rates
- Resource utilization (CPU, memory, disk)

### Monitoring Commands
```bash
# Circuit breaker status
curl -H "X-HYBA-Internal-Token: $TOKEN" http://127.0.0.1:3000/bridge/internal/health

# Backend metrics
curl -H "X-HYBA-Internal-Token: $TOKEN" http://127.0.0.1:3000/bridge/metrics

# Mining status
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:3000/api/mining/status

# Real-time logs
docker-compose -f docker-compose.production.yml logs -f
```

## Deployment Communication

### Pre-Deployment
- Notify on-call team 24 hours in advance for production deployments
- Send deployment notification to stakeholders
- Update status page: "Scheduled maintenance in progress"

### During Deployment
- Provide status updates every 15 minutes
- Alert immediately on rollback triggers
- Maintain communication channel for quick decisions

### Post-Deployment
- Update status page: "Deployment complete"
- Send summary to stakeholders
- Document any issues or learnings

## Troubleshooting

### Common Issues

**Issue: Docker build fails**
```bash
# Check Docker daemon running
docker ps

# Clear Docker cache
docker system prune -a

# Check disk space
df -h
```

**Issue: Backend fails to start**
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs hyba-backend

# Check environment variables
docker-compose -f docker-compose.production.yml config

# Verify Python dependencies
docker-compose -f docker-compose.production.yml run hyba-backend python -m pip list
```

**Issue: Health checks failing**
```bash
# Check backend directly
curl http://127.0.0.1:3001/api/health/readiness

# Check bridge logs
docker-compose -f docker-compose.production.yml logs hyba-bridge

# Verify network connectivity
docker-compose -f docker-compose.production.yml exec hyba-bridge ping hyba-backend
```

**Issue: Mining operations not starting**
```bash
# Check pool credentials
docker-compose -f docker-compose.production.yml exec hyba-backend env | grep POOL

# Check mining logs
docker-compose -f docker-compose.production.yml logs hyba-runtime

# Verify Stratum connection
docker-compose -f docker-compose.production.yml exec hyba-runtime telnet <pool-host> <pool-port>
```

## Deployment Checklist Template

Use this checklist for every production deployment:

```
Deployment Date: ___
Deployment Version: ___
Deployed By: ___
Reviewer: ___

Pre-Deployment:
□ Code review approved
□ CI checks passing
□ Tests passing
□ Documentation updated
□ On-call notified
□ Rollback plan documented

Deployment:
□ Backup created
□ Deployment started
□ Health checks passing
□ Mining operations verified
□ Metrics stable

Post-Deployment:
□ Monitoring active
□ Stakeholders notified
□ Documentation updated
□ Lessons learned documented

Rollback Required: Yes/No
If yes, reason: ___

Issues Encountered:
□ Issue 1: ___
□ Issue 2: ___

Overall Status: Success/Failure
```

## Emergency Contacts

- On-call Engineering: [CONTACT]
- DevOps Lead: [CONTACT]
- Mining Operations: [CONTACT]
- Executive Team: [CONTACT]
- Security Team: [CONTACT]
