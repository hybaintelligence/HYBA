# HYBA Frontend Production Deployment Guide

**Deployment Mode**: Customer-Facing (No Mining UI)  
**Status**: Production Ready  
**Last Updated**: 2026-06-23

---

## Quick Deploy

### 1. Set Environment Variables

```bash
# Customer-facing production deployment
export HYBA_CUSTOMER_MODE=true
export HYBA_INTERNAL_MODE=false
export NODE_ENV=production

# Required secrets (DO NOT commit these)
export JWT_SECRET="your_jwt_secret_here"
export HYBA_API_KEY_SECRET="your_api_key_secret_here"
export HYBA_CORS_ORIGINS="https://yourdomain.com"
```

### 2. Build and Deploy

```bash
# Run production checks
./scripts/production_deploy.sh

# Or manually:
npm run lint
npm run test:frontend:all
npm run build

# Deploy to Cloudflare Pages / your CDN
npm run cloudflare:build
```

---

## Feature Flag Configuration

### Customer Deployment (Default)

```bash
VITE_CUSTOMER_MODE=true
VITE_INTERNAL_MODE=false
```

**Result**:
- ✅ QaaS, QIaaS, CIaaS, Quantum Finance visible
- ✅ Evidence explorer, usage metering, API docs
- ❌ Mining UI hidden
- ❌ Internal telemetry hidden
- ❌ Pool management hidden
- ❌ Hashrate metrics hidden

### Internal Operations (Private)

```bash
VITE_INTERNAL_MODE=true
VITE_CUSTOMER_MODE=false
```

**Result**:
- ✅ All customer features
- ✅ Mining validation UI
- ✅ Internal telemetry
- ✅ Pool management
- ✅ Debug panel

---

## Deployment Verification

### Pre-Deploy Checks

```bash
# 1. No secrets committed
grep -r "JWT_SECRET" .env* || echo "✅ No secrets in .env"

# 2. TypeScript compiles
npm run lint

# 3. Tests pass
npm run test:frontend:all

# 4. Build succeeds
npm run build

# 5. Bundle size acceptable
ls -lh dist/assets/*.js | awk '{print $5, $9}'
```

### Post-Deploy Smoke Tests

```bash
# 1. Health check
curl https://yourdomain.com/api/health

# 2. Customer onboarding loads
curl https://yourdomain.com/ | grep "CustomerOnboarding"

# 3. No mining terminology in customer view
curl https://yourdomain.com/ | grep -i "mining" && echo "❌ Found mining" || echo "✅ Clean"

# 4. Evidence seals present
curl https://yourdomain.com/api/v1/fault-tolerant-computers | jq '.evidence_seal'
```

---

## Production Architecture

```
┌─────────────────────────────────────────────────────┐
│  Cloudflare CDN / Edge                              │
│  - Static assets (React bundle)                     │
│  - Global caching                                   │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  Express Bridge Server (src/server.ts)              │
│  - /api/* → Backend proxy                           │
│  - Health checks: /bridge/health, /bridge/metrics   │
│  - Rate limiting + Circuit breaker                  │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│  FastAPI Backend (Python)                           │
│  - /api/v1/fault-tolerant-computers (QaaS)          │
│  - /api/qiaas (QIaaS)                               │
│  - /api/v1/computational-intelligence-services      │
│  - /api/quantum-finance                             │
└─────────────────────────────────────────────────────┘
```

---

## Customer Onboarding Flow

### Step 1: Welcome (30 seconds)
- Substrate-independent quantum intelligence
- QaaS, QIaaS, CIaaS, Quantum Finance overview
- Mathematics first, hardware agnostic messaging

### Step 2: Provision Service (1 minute)
- Select service type (QaaS/QIaaS/CIaaS/Finance)
- Configure tier (developer/production/sovereign)
- Set data residency

### Step 3: Generate API Key (30 seconds)
- One-click API key generation
- HMAC-SHA256 authenticated
- Copy-paste ready

### Step 4: Quick Win (2 minutes)
- Interactive code example
- Run first API call
- See evidence seal + results

**Total Time**: <5 minutes from signup to first API call

---

## Monitoring & Alerts

### Key Metrics

```yaml
# Frontend Performance
- first_contentful_paint_ms: <1500
- time_to_interactive_ms: <3000
- bundle_size_kb: <500

# API Performance
- api_latency_p95_ms: <500
- error_rate_percent: <1
- evidence_seal_verification_failures: 0

# Customer Activation
- onboarding_completion_rate: >70
- time_to_first_call_seconds: <300
- weekly_active_users_percent: >50
```

### Alert Thresholds

```yaml
Critical:
  - backend_unreachable: >5min
  - evidence_seal_failure: >0 in 1h
  - api_error_rate: >5% in 5min

High:
  - api_latency_p95: >1000ms for 5min
  - customer_quota_exhausted: any occurrence

Medium:
  - onboarding_drop_off: >50% at any step
  - bundle_size_increase: >20% vs baseline
```

---

## Rollback Procedure

If issues detected post-deployment:

```bash
# 1. Immediate: Revert CDN to previous version
cloudflare pages rollback

# 2. Verify rollback successful
curl https://yourdomain.com/api/health

# 3. Investigate root cause
# Review logs, error rates, customer reports

# 4. Fix forward
# Apply hotfix, test, redeploy
```

---

## Customer Support Runbook

### Common Issues

**Issue**: "Can't generate API key"  
**Resolution**: Verify customer role has `api_key:create` permission

**Issue**: "Evidence seal verification failed"  
**Resolution**: Check backend connectivity, review `/api/health` endpoint

**Issue**: "Quota exceeded"  
**Resolution**: Customer on `/usage` page, upgrade tier or wait for period reset

**Issue**: "Onboarding won't complete"  
**Resolution**: Check browser console for errors, verify localStorage available

---

## Security Checklist

- [x] JWT secret not committed (`.gitignore` includes `.env.local`)
- [x] HMAC secret generated per environment
- [x] CORS origins explicitly allowlisted
- [x] Rate limiting enabled (100 req/15min default)
- [x] HTTPS enforced in production
- [x] CSP headers configured
- [x] No inline scripts or eval()
- [x] API responses include evidence seals
- [x] Customer data segregation (tenancy controls)

---

## Performance Optimization

### Bundle Optimization
- Code splitting by route (lazy loading)
- Tree shaking unused dependencies
- Gzip compression enabled
- CDN caching headers

### Runtime Optimization
- React 19 concurrent rendering
- WebSocket for live telemetry (optional)
- Debounced API polling (15s default)
- Memoized expensive computations

---

## Success Criteria (30 Days Post-Launch)

### Reliability
- ✅ 99.5% uptime
- ✅ <500ms API latency p95
- ✅ 0 evidence seal failures

### Customer Activation
- ✅ >70% onboarding completion
- ✅ <5min median time-to-first-call
- ✅ >50% weekly active users

### Commercial
- ✅ >$10K MRR
- ✅ >3 enterprise customers
- ✅ <5% churn rate

---

## Next Steps After Deployment

### Week 1: Monitor & Stabilize
- Watch error rates, latency, customer feedback
- Daily stand-up to review incidents
- Hot-fix any critical issues

### Week 2-4: Optimize
- Review customer usage patterns
- Identify friction points in onboarding
- A/B test messaging (quantum vs. intelligence framing)
- Gather case studies from early adopters

### Month 2+: Scale
- Increase quotas for high-usage customers
- Build industry-specific templates
- Partner integrations (Snowflake, Databricks)
- Community forum launch

---

**Deployment Command**:
```bash
./scripts/production_deploy.sh && npm run start
```

**Verification URL**: https://yourdomain.com  
**API Health**: https://yourdomain.com/api/health  
**Docs**: https://yourdomain.com/docs
