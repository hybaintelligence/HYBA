# Local Docker Cloud Deployment Guide

**Based on Gordon's Tier 1 Deployment Strategy**  
**Governance Rail: treasury**  
**Evidence Storage: Local filesystem**

This guide explains how to deploy HYBA locally using Docker Cloud (Docker Build Cloud) instead of Docker Desktop.

---

## Overview

This deployment follows Gordon's historic deployment strategy from `HYBA_HISTORIC_DEPLOYMENT_STRATEGY.md`:

- **Tier 1: Development & Validation** - Single backend instance with local evidence storage
- **Image Source**: Docker Cloud (multi-platform builds via GitHub Actions)
- **Governance**: Treasury rail (founder/R&D mode)
- **Evidence**: Stored locally on host filesystem

---

## Prerequisites

### GitHub Secrets (Already Configured)

The following GitHub secrets are already configured in your workflows:

- `DOCKERHUB_USERNAME` - Your Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token
- `DOCKERHUB_REPOSITORY` - Optional: Custom repository name

### Local Requirements

- Docker Engine (not Docker Desktop)
- Docker Compose
- Git

---

## Quick Start

### 1. Configure Local Environment

Edit `.env.local` and set your Docker Hub username:

```bash
# .env.local
DOCKERHUB_USERNAME=your-actual-dockerhub-username
```

### 2. Deploy Locally (Windows)

```cmd
cd c:\Users\USER\OneDrive\Desktop\HYBA_Final
scripts\deploy-local.bat
```

### 3. Deploy Locally (Linux/Mac)

```bash
cd /path/to/HYBA_Final
chmod +x scripts/deploy-local.sh
./scripts/deploy-local.sh
```

---

## What Gets Deployed

### Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend (Bridge) | 3000 | React/Vite frontend |
| Backend API | 3001 | Python FastAPI backend |
| PostgreSQL | 5432 | Customer portal database |
| Redis | 6379 | Distributed locks/cache |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3002 | Observability dashboard |

### Evidence Storage

Evidence is stored locally per Gordon's Tier 1 strategy:

- `./runtime/evidence/` - PYTHIA autonomy evidence
- `./runtime/memos/` - Startup and operational memos

---

## Docker Cloud Integration

### Image Building (CI/CD)

Images are built and pushed via GitHub Actions:

- **Workflow**: `.github/workflows/docker-cloud-deploy.yml`
- **Trigger**: Push to `main` branch
- **Platforms**: `linux/amd64`, `linux/arm64`
- **Registry**: Docker Hub

### Image Pulling (Local)

Local deployment pulls the pre-built image:

```yaml
# docker-compose.local.yml
services:
  backend:
    image: ${DOCKERHUB_USERNAME}/hyba-fullstack:latest
```

---

## Configuration

### Environment Variables (.env.local)

Key variables for local deployment:

```bash
# Docker Cloud
DOCKERHUB_USERNAME=your-username

# Governance (Gordon's Tier 1)
HYBA_GOVERNANCE_RAIL=treasury

# Mining (disabled by default for local)
HYBA_ENABLE_MINING_AUTOCONNECT=false
HYBA_ENABLE_LIVE_STRATUM=false

# Evidence (local filesystem)
HYBA_EVIDENCE_STORAGE_PATH=/app/runtime/evidence
HYBA_EVIDENCE_SYNC_ENABLED=false
```

### Governance Rails

Per Gordon's strategy, local deployment uses the **treasury rail**:

- No human gates required
- Direct deployment
- Autonomous optimization enabled
- Evidence stored locally

---

## Useful Commands

### View Logs

```bash
docker-compose -f docker-compose.local.yml logs -f
```

### Stop Services

```bash
docker-compose -f docker-compose.local.yml down
```

### Restart Services

```bash
docker-compose -f docker-compose.local.yml restart
```

### Check Status

```bash
docker-compose -f docker-compose.local.yml ps
```

### Pull Latest Image

```bash
docker-compose -f docker-compose.local.yml pull
```

---

## Enabling Mining (Optional)

To enable mining in local deployment:

1. Edit `.env.local`:
```bash
HYBA_ENABLE_MINING_AUTOCONNECT=true
HYBA_ENABLE_LIVE_STRATUM=true
```

2. Restart services:
```bash
docker-compose -f docker-compose.local.yml restart
```

**Note**: Mining pools are pre-configured with test credentials:
- ViaBTC: `PYTHIA.001` / `123`
- Braiins: `PYTHAGOROS` / `anything123`

---

## Troubleshooting

### Image Pull Fails

If the image pull fails:

1. Verify your `DOCKERHUB_USERNAME` in `.env.local`
2. Check that the image exists on Docker Hub
3. Ensure you're logged in to Docker Hub:
```bash
docker login
```

### Services Won't Start

Check logs for specific service:
```bash
docker-compose -f docker-compose.local.yml logs backend
docker-compose -f docker-compose.local.yml logs postgres
```

### Evidence Not Writing

Ensure runtime directories exist:
```bash
mkdir -p runtime/evidence
mkdir -p runtime/memos
```

---

## Gordon's Tier 1 Constraints

Per the historic deployment strategy, stop using this tier when:

- Before first commercial customer deployment
- When evidence files exceed 10GB
- When you need geo-redundancy

Upgrade to **Tier 2** (Commercial SaaS) or **Tier 3** (Enterprise & Sovereign) at that point.

---

## Next Steps

1. **Deploy locally**: Run the deployment script
2. **Verify health**: Check `http://localhost:3000/bridge/health`
3. **Review evidence**: Check `./runtime/evidence/`
4. **Monitor metrics**: Access Grafana at `http://localhost:3002`

---

## References

- Gordon's Historic Deployment Strategy: `HYBA_HISTORIC_DEPLOYMENT_STRATEGY.md`
- Docker Cloud Workflow: `.github/workflows/docker-cloud-deploy.yml`
- GitHub Secrets: Configured in repository settings
