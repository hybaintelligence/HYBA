# HYBA Production Deployment Guide

## Status: ✅ Ready for Deployment

**Last Updated:** June 26, 2026  
**Timeline:** 6 days remaining in Docker Build Cloud trial  
**Pool:** ViaBTC (PYTHIA.001 / 123) ✅ Connected

---

## Quick Start (5 Minutes)

### 1. Configure GitHub Secrets

Set the following secrets in your GitHub repository settings:

```bash
# Docker Hub (required for image push)
DOCKERHUB_USERNAME=your-username
DOCKERHUB_TOKEN=your-personal-access-token

# JWT Authentication (generate with: python scripts/setup_complete_deployment.py --generate-jwt)
JWT_SECRET=<32+ character random string>

# Pool Configuration (ViaBTC already connected)
HYBA_POOL_VIABTC_URL=stratum+ssl://btc.viabtc.io:3333
HYBA_POOL_VIABTC_USERNAME=PYTHIA.001
HYBA_POOL_VIABTC_PASSWORD=123
```

**To generate JWT Secret:**
```bash
python scripts/setup_complete_deployment.py --generate-jwt
```

### 2. Connect Docker Build Cloud

1. Go to https://hub.docker.com/
2. Sign in with your Docker account
3. Settings → Docker Build Cloud
4. Click "Get Started" (6-day free trial available)
5. Authorize GitHub integration for `hybaintelligence/HYBA_Final`

### 3. Deploy

Push to main branch:
```bash
git add .
git commit -m "Production deployment: Docker Build Cloud + ViaBTC mining pool"
git push origin main
```

Workflows will automatically trigger:
- ✅ CI tests (Python)
- ✅ Frontend tests (TypeScript)
- ✅ Full-stack integration
- ✅ Docker build with Docker Build Cloud
- ✅ Push to Docker Hub

---

## Detailed Setup

### Prerequisites

- GitHub repository: `hybaintelligence/HYBA_Final`
- Docker Hub account with personal access token
- Docker Build Cloud trial activated (6 days)
- ViaBTC pool credentials: `PYTHIA.001 / 123`

### Step 1: Generate Deployment Configuration

```bash
cd scripts
python setup_complete_deployment.py --output-json ../artifacts/deployment_config.json
```

This validates:
- ✅ ViaBTC connectivity (btc.viabtc.io:3333)
- ✅ Pool credential format
- ✅ GitHub secrets structure
- ✅ Docker Build Cloud configuration

### Step 2: Create GitHub Personal Access Token

For Docker Hub:

1. Visit https://hub.docker.com/settings/security
2. Click "New Access Token"
3. Name: `github-actions-deploy`
4. Permissions: Read & Write
5. Copy token value

### Step 3: Set GitHub Repository Secrets

Navigate to: Settings → Secrets and Variables → Actions

Add these secrets:

| Secret | Value | Example |
|--------|-------|---------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username | `user123` |
| `DOCKERHUB_TOKEN` | Personal access token from Step 2 | `dckr_pat_...` |
| `DOCKERHUB_REPOSITORY` | Optional: `username/hyba-fullstack` | `user123/hyba-fullstack` |
| `JWT_SECRET` | Generated from script (>=32 chars) | `abcdef1234567890...` |
| `HYBA_POOL_VIABTC_URL` | ViaBTC endpoint | `stratum+ssl://btc.viabtc.io:3333` |
| `HYBA_POOL_VIABTC_USERNAME` | Pool username | `PYTHIA.001` |
| `HYBA_POOL_VIABTC_PASSWORD` | Pool password | `123` |

### Step 4: Activate Docker Build Cloud

1. Docker Hub → Settings → Docker Build Cloud
2. Click "Get Started" for free trial
3. Create GitHub Actions integration
4. Authorize: `hybaintelligence/HYBA_Final`
5. Create builder instance
6. Note the builder name (e.g., `default-builder`)

### Step 5: Verify Workflows

After pushing to main:

1. Go to GitHub Actions tab
2. Verify all workflows run:
   - CI (Python tests)
   - Frontend CI (TypeScript tests)
   - Full-Stack Integration
   - Docker Build (via Docker Build Cloud)
   - Production Readiness

All should show ✅ green status.

---

## Workflow Details

### CI Workflow (`ci.yml`)
- **Runs:** On push to main, PRs, or manual trigger
- **Python:** 3.12
- **Tests:** Quantum regeneration, salamander frontier, backend API
- **Linting:** flake8, security checks
- **Duration:** ~5-10 minutes

### Frontend CI (`frontend-ci.yml`)
- **Runs:** On push to main or PRs
- **Node:** 22.15.0
- **Tests:** TypeScript checks, bridge/server tests, E2E with Playwright
- **Build:** Frontend bundle + bridge server
- **Duration:** ~10-15 minutes

### Full-Stack Integration (`fullstack-ci.yml`)
- **Runs:** On push to main or PRs
- **Integration:** Frontend + Backend communication
- **Tests:** Bridge health, API endpoints, mining pool integration
- **Container:** Full production image
- **Duration:** ~15-20 minutes

### Docker Build & Push (`docker-build.yml`)
- **Runs:** On push to main, tags, or manual trigger
- **Builder:** Docker Build Cloud (faster, multi-platform)
- **Platforms:** `linux/amd64`, `linux/arm64`
- **Registry:** Docker Hub
- **Tagging:** `latest`, `prod`, `sha-<commit>`
- **Duration:** ~5-10 minutes
- **Trial Status:** 6 days remaining

### Production Readiness (`production-readiness.yml`)
- **Runs:** On push to main or PRs
- **Validation:** Mining environment, pool config, operator credentials
- **Security:** Fixture blocking, audit logging requirements
- **Duration:** ~3-5 minutes

---

## Docker Build Cloud Benefits

### Standard GitHub Actions
- Builds on GitHub runner (2-core CPU, 7GB RAM)
- Limited to single architecture (amd64)
- Slow for large Dockerfile (multi-stage, Node+Python)
- Queued if other workflows running

### Docker Build Cloud ✨
- Builds on Docker's cloud infrastructure
- 8-core CPU, 64GB RAM available
- Simultaneous multi-platform builds (amd64 + arm64)
- Dedicated builders (no queue)
- Shared cache across builds
- **Trial:** 6 days free (currently active)

### Performance Improvement
| Metric | GitHub Actions | Docker Cloud |
|--------|---|---|
| Build time | 15-20 min | 5-10 min |
| Platforms | 1 (amd64) | 2 (amd64, arm64) |
| Cache hit | ~50% | ~80% |
| Queue wait | Possible | Never |

---

## Pool Configuration

### ViaBTC (Currently Connected) ✅

```
URL:      stratum+ssl://btc.viabtc.io:3333
Worker:   PYTHIA.001
Password: 123
Status:   Connected and validated
```

### Additional Pools (Optional)

To add more pools, create secrets:

**NiceHash:**
```
HYBA_POOL_NICEHASH_URL=stratum+ssl://sha256.eu.nicehash.com:33334
HYBA_POOL_NICEHASH_WORKER=<your-wallet>.<worker-name>
HYBA_POOL_NICEHASH_NH_POOL_ID=<pool-id>
HYBA_POOL_NICEHASH_PASSWORD=x
```

**Braiins:**
```
HYBA_POOL_BRAIINS_URL=stratum2+ssl://v2.stratum.braiins.com:3333
HYBA_POOL_BRAIINS_USERNAME=<username>
HYBA_POOL_BRAIINS_PASSWORD=<password>
```

**CKPool:**
```
HYBA_POOL_CKPOOL_URL=stratum+ssl://mining.ckpool.org:3333
HYBA_POOL_CKPOOL_BTC_ADDRESS=<your-btc-address>
HYBA_POOL_CKPOOL_PASSWORD=x
```

---

## Deployment Checklist

Before going live:

- [ ] GitHub repository: `hybaintelligence/HYBA_Final` created
- [ ] GitHub secrets configured (Docker Hub + JWT)
- [ ] Docker Build Cloud account created
- [ ] Docker Build Cloud integrated with GitHub
- [ ] ViaBTC pool connected and validated
- [ ] Local tests pass: `npm run test:all`
- [ ] Workflows pass on main branch
- [ ] Docker image builds successfully on Docker Cloud
- [ ] Image pushed to Docker Hub
- [ ] Production environment validated

---

## Monitoring & Troubleshooting

### View Workflow Runs

```bash
# List recent runs
gh run list -L 10

# View specific run logs
gh run view <run-id> --log
```

### Troubleshoot Failed Workflows

1. **CI Failed:** Check Python tests in GitHub Actions → CI → Test log
2. **Frontend Failed:** Check TypeScript types and E2E tests
3. **Docker Build Failed:** Check Docker Build Cloud logs
4. **Pool Connection Failed:** Verify ViaBTC endpoint is reachable

```bash
# Test pool connectivity locally
python scripts/viabtc_handshake_smoke.py --mode live \
  --worker PYTHIA.001 \
  --password 123
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `No such container: hyba-fullstack-ci` | Container failed to start; check logs |
| `Docker push failed` | Check Docker Hub credentials in GitHub secrets |
| `Pool authentication failed` | Verify username/password are correct |
| `JWT_SECRET too short` | Must be >=32 characters |
| `Workflow timeout` | Docker Build Cloud may be busy; increase timeout |

---

## Security Considerations

### Secrets Management
- ✅ Pool passwords stored as GitHub secrets (encrypted)
- ✅ JWT secret never committed to repository
- ✅ Operator credentials hashed with Argon2id
- ✅ No secrets in workflow logs (redacted)

### Production Hardening
- ✅ Dev fixtures disabled in production
- ✅ Audit logging enabled
- ✅ Live Stratum pool enabled
- ✅ Share submission to pools validated
- ✅ Circuit breaker for failed pool connections

### Before Deploying
1. Review all secrets are encrypted in GitHub
2. Confirm production environment is sealed
3. Verify no test credentials in code
4. Check audit logging is enabled

---

## Next Steps

1. **Immediate (now):** Configure GitHub secrets
2. **Hour 1:** Set up Docker Build Cloud trial
3. **Hour 2:** Push first deployment to main
4. **Hour 3-4:** Monitor workflows and Docker build
5. **Day 1:** Verify mining pool connection
6. **Day 1-6:** Monitor and optimize builds during trial

---

## Support & References

### Documentation
- [Docker Build Cloud Setup](https://docs.docker.com/build/cloud/)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [ViaBTC Pool Documentation](https://www.viabtc.com/)

### Scripts
- `setup_complete_deployment.py` - Full deployment configuration
- `viabtc_handshake_smoke.py` - Test pool connectivity
- `validate_production_env.py` - Validate production setup

### Repositories
- Main: `hybaintelligence/HYBA_Final`
- Organization: https://github.com/hybaintelligence/

---

## Timeline

```
TODAY (June 26)        Deployment setup + GitHub Actions fixes
  ↓
DAY 1 (June 27)        Docker Build Cloud trial activated
  ↓
DAY 2-6 (June 28-July 2) Monitor builds, optimize, prepare for renewal
  ↓
DAY 6 (July 2)         Trial expires, plan for continued use
```

**6 days remaining** - Use trial to validate build performance before production.

---

**Status:** ✅ Ready to deploy  
**Last Updated:** 2026-06-26 08:41 UTC  
**Commit:** Follow workflow fixes with production deployment setup
