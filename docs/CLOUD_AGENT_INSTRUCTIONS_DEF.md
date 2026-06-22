# Cloud Agent Instructions: Vectors D, E, F
**Status:** Ready for autonomous execution  
**Duration:** 5-7 days  
**Success Metric:** Production infrastructure tested locally and ready for deployment

---

## 🎯 Mission

Transform the validated HYBA fault-tolerant quantum computing platform from a **local development system** into a **production-grade, scalable platform** by implementing:

1. **Vector D:** Docker containerization + Kubernetes manifests
2. **Vector E:** GitHub Actions CI/CD automation
3. **Vector F:** PostgreSQL persistence + audit logging

**Result:** A system that can scale from 10 to 1000 concurrent customers with zero downtime deployments and complete operational auditability.

---

## 📖 Complete Instructions

All implementation details are in:

```
.devin/workflows/implement-def-production-infrastructure.md
```

This document contains:
- ✅ Complete code for all files
- ✅ Step-by-step implementation sequence
- ✅ Checkpoint validation at each stage
- ✅ Integration testing procedures
- ✅ Acceptance criteria

---

## ⚡ Quick Start for Cloud Agent

### Prerequisites Verification
```bash
# Verify baseline system
python -m pytest tests/test_fault_tolerant_quantum.py \
  tests/test_quantum_as_a_service_api.py \
  tests/test_computational_intelligence_service_api.py \
  tests/test_commercial_public_api.py -q

# Should show: 31 passed
# If not: stop and debug before proceeding
```

### Phase 1: Docker & Kubernetes (D)
```bash
# Follow section D.1, D.2, D.3 in the instructions
# Create files:
#   - Dockerfile
#   - docker-compose.yml
#   - k8s/ directory with 5 manifests

# Checkpoint:
docker-compose up -d
docker-compose ps  # Verify all healthy
docker-compose down
```

### Phase 2: CI/CD Pipeline (E)
```bash
# Follow section E.1, E.2, E.3 in the instructions
# Create/update files:
#   - .github/workflows/ci.yml
#   - .github/workflows/docker-build.yml
#   - .github/workflows/deploy.yml

# Checkpoint:
git tag v0.1.0-test
git push origin v0.1.0-test
# Check GitHub Actions tab for successful run
```

### Phase 3: Data Persistence (F)
```bash
# Follow section F.1, F.2, F.3 in the instructions
# Create files:
#   - scripts/init-db.sql
#   - python_backend/hyba_genesis_api/models/database.py
#   - python_backend/hyba_genesis_api/services/database_service.py

# Checkpoint:
docker-compose up -d
docker-compose exec backend python -m pytest tests/test_def_integration.py -v
docker-compose down
```

---

## 📋 Detailed Workflow for Cloud Agent

### Step 1: Read Full Instructions
```
READ: .devin/workflows/implement-def-production-infrastructure.md
(Understand the architecture before starting code)
```

### Step 2: Execute in Sequence
```
1. Create D.1 (Dockerfile)
   └─ Run checkpoint: docker build

2. Create D.2 (docker-compose.yml)
   └─ Run checkpoint: docker-compose up -d

3. Create D.3 (K8s manifests)
   └─ Run checkpoint: kubectl apply --dry-run

4. Create E.1 (CI workflow)
   └─ Run checkpoint: commit to branch, check Actions

5. Create E.2 (Docker build workflow)
   └─ Run checkpoint: commit to main, verify image push

6. Create E.3 (Deployment workflow)
   └─ Run checkpoint: tag v*, verify deployment

7. Create F.1 (Database schema)
   └─ Run checkpoint: docker-compose exec postgres psql

8. Create F.2 (ORM models)
   └─ Run checkpoint: python -c "import models"

9. Create F.3 (Database service)
   └─ Run checkpoint: python -c "from services import DatabaseService"

10. Create Integration Tests
    └─ Run checkpoint: docker-compose up && pytest
```

### Step 3: Validation
```
Run full integration suite:
docker-compose up -d
docker-compose exec backend python -m pytest tests/test_def_integration.py -v
docker-compose down

Verify checklist in implementation guide completes 100%
```

### Step 4: Commit & Cleanup
```bash
git add .
git commit -m "feat: production infrastructure (DEF)

- Vector D: Docker/K8s containerization
- Vector E: GitHub Actions CI/CD pipeline  
- Vector F: PostgreSQL persistence & audit logging

Tested: All integration tests passing
Status: Ready for production deployment"

git push origin main
```

---

## 🔍 Key Decision Points

### If Docker Build Fails
**Action:** Check `python_backend/` directory structure matches imports in Dockerfile.  
**Resolution:** Adjust COPY paths in Dockerfile or refactor imports.  
**Don't proceed** until `docker build` succeeds.

### If K8s Manifests Don't Apply
**Action:** Run `kubectl apply -f k8s/ --dry-run=client -o yaml` for detailed errors.  
**Resolution:** Fix YAML syntax or missing ConfigMap references.  
**Don't proceed** until `kubectl apply --dry-run` succeeds.

### If PostgreSQL Won't Initialize
**Action:** Check `scripts/init-db.sql` syntax.  
**Resolution:** Test schema locally with `psql -U hyba -d hyba -f init-db.sql`.  
**Don't proceed** until schema initializes without errors.

### If CI Pipeline Fails
**Action:** Check GitHub Actions logs for specific error.  
**Resolution:** Common issues:
- Missing environment variables (set in repo Settings > Secrets)
- Test dependency not installed (add to `requirements.test.txt`)
- Path incorrect in workflow (adjust relative paths)

**Don't proceed** until CI passes on a test commit.

---

## 📊 Success Metrics

### After Vector D
```
✅ docker-compose up -d runs without errors
✅ All services report "healthy" status
✅ Backend API responds to /api/health
✅ PostgreSQL initialized
✅ Redis accepting connections
✅ docker-compose down cleans up properly
```

### After Vector E
```
✅ PR blocks if tests fail
✅ Merge to main auto-builds Docker image
✅ Image appears in ghcr.io
✅ Tag triggers deployment workflow
✅ Approval gate prevents unauthorized deployments
```

### After Vector F
```
✅ Database schema created on first run
✅ Workload executions recorded with cost
✅ Audit log captures all operations
✅ Quota tracking enforces limits
✅ All integration tests pass
✅ Database service layer accessible from API
```

---

## ⏱️ Time Estimate

| Phase | Component | Time | Status |
|-------|-----------|------|--------|
| D | Dockerfile | 1-2 hrs | - |
| D | docker-compose.yml | 2-3 hrs | - |
| D | K8s manifests | 3-4 hrs | - |
| E | CI workflow | 2-3 hrs | - |
| E | Docker build workflow | 2-3 hrs | - |
| E | Deployment workflow | 3-4 hrs | - |
| F | Database schema | 2-3 hrs | - |
| F | ORM models | 2-3 hrs | - |
| F | Database service | 2-3 hrs | - |
| Integration | Testing + verification | 3-4 hrs | - |
| **TOTAL** | | **23-32 hrs** | - |

**Recommended:** Spread across 5-7 business days with 4-6 hours per day.

---

## 🚨 Blockers & Escalation

### If You Encounter
| Issue | Resolution | Escalate If |
|-------|-----------|------------|
| `docker build` fails | Check Dockerfile COPY paths | Still fails after 2 attempts |
| `docker-compose ps` shows unhealthy | Check service logs with `docker-compose logs` | Service won't become healthy after 5 min |
| PostgreSQL won't accept connections | Verify `DATABASE_URL` environment variable | Still can't connect after checking env |
| GitHub Actions secret doesn't inject | Verify secret name matches workflow | Secrets configured but workflow can't access |
| K8s manifests invalid YAML | Run `kubectl apply --dry-run` for errors | YAML errors persist after fixes |

**Escalation Path:** If blocked > 2 hours, document the issue and request human engineer review.

---

## 📚 Reference Files

**Implementation Guide:**
```
.devin/workflows/implement-def-production-infrastructure.md
```

**Key Files to Create:**
```
Dockerfile
docker-compose.yml
k8s/namespace.yaml
k8s/configmap.yaml
k8s/secret.yaml
k8s/postgres-deployment.yaml
k8s/redis-deployment.yaml
k8s/backend-deployment.yaml
.github/workflows/ci.yml
.github/workflows/docker-build.yml
.github/workflows/deploy.yml
scripts/init-db.sql
python_backend/hyba_genesis_api/models/database.py
python_backend/hyba_genesis_api/services/database_service.py
tests/test_def_integration.py
```

---

## ✅ Final Checklist Before Starting

- [ ] Read entire `implement-def-production-infrastructure.md` document
- [ ] All 31 baseline tests passing
- [ ] Docker Desktop running
- [ ] GitHub repo has Actions enabled
- [ ] kubectl installed (optional but recommended)
- [ ] Understand the three vectors (D, E, F)
- [ ] Understand the dependencies between vectors

**Ready to start?** Begin with Vector D, section D.1.

---

## 🎓 Learning Outcomes

By completing this task, you will:
1. **Understand containerization** (Docker, image build, registry)
2. **Understand orchestration** (Kubernetes manifests, deployments, services)
3. **Understand CI/CD** (GitHub Actions workflows, artifact promotion)
4. **Understand persistence** (PostgreSQL, ORM, migrations)
5. **Understand auditing** (Immutable logs, compliance, forensics)

This is enterprise-grade infrastructure knowledge. Use it wisely.

---

**Status:** ✅ Ready for cloud agent execution  
**Next Phase After DEF:** Vectors G, H, I (Customer Portal, Multi-Cloud, Analytics)  
**Estimated Timeline:** 5-7 days to production-ready infrastructure
