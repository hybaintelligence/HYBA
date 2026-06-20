# Production Infrastructure Implementation: Vectors D, E, F
**Agent Task:** Implement Docker/K8s (D), CI/CD (E), Data Persistence (F)  
**Duration:** 5-7 days  
**Execution Model:** Autonomous with checkpoint validation

---

## 🎯 Executive Summary

Transform a validated core engine into a **production-grade, scalable platform** by implementing:
- **Vector D:** Docker containerization + Kubernetes manifests (deploy anywhere)
- **Vector E:** GitHub Actions CI/CD pipeline (continuous deployment)
- **Vector F:** PostgreSQL database + audit logging (permanent record keeping)

**Success Metric:** Full infrastructure testable locally via docker-compose, deployable to K8s cluster, with automated tests on every commit.

---

## 📋 Prerequisites & Assumptions

Before starting, verify:
```
✅ Python 3.12.7 available (pyenv)
✅ Node.js v22 + npm installed
✅ Docker Desktop running (if testing locally)
✅ kubectl installed (if testing K8s)
✅ GitHub account + repo access
✅ All 31 tests passing (commit: verified baseline)
```

---

## VECTOR D: Docker Containerization & Kubernetes
**Estimated Time:** 2-3 days

### D.1: Create Backend Dockerfile

**File:** `Dockerfile` (root of repo)

```dockerfile
FROM python:3.12.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY python_backend/requirements.txt .
COPY python_backend/requirements.test.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY python_backend/ /app/
COPY config/ /config/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"

# Run backend
CMD ["uvicorn", "hyba_genesis_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Rationale:**
- Minimal base image (slim) reduces attack surface
- Health check enables K8s liveness probes
- Multi-stage would optimize further (optional for Phase 2)

---

### D.2: Create docker-compose.yml

**File:** `docker-compose.yml` (root of repo)

This enables **local testing** of full stack (backend + Redis + Postgres + Prometheus + Grafana).

Instructions continue in next section...


### D.2: Create docker-compose.yml

**File:** `docker-compose.yml` (root of repo)

```yaml
version: '3.8'

services:
  # Backend API
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://hyba:hyba@postgres:5432/hyba
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - hyba-network
    volumes:
      - ./config:/config:ro
    restart: unless-stopped

  # Redis (state management)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - hyba-network
    restart: unless-stopped

  # PostgreSQL (persistence)
  postgres:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=hyba
      - POSTGRES_PASSWORD=hyba
      - POSTGRES_DB=hyba
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hyba"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - hyba-network
    restart: unless-stopped

  # Prometheus (metrics)
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - hyba-network
    restart: unless-stopped

  # Grafana (dashboards)
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./config/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
    depends_on:
      - prometheus
    networks:
      - hyba-network
    restart: unless-stopped

volumes:
  redis-data:
  postgres-data:
  prometheus-data:
  grafana-data:

networks:
  hyba-network:
    driver: bridge
```

**Checkpoint D.2:**
```bash
# Test docker-compose startup
docker-compose up -d
docker-compose ps  # All services should be "healthy"
curl http://localhost:8000/api/health
curl http://localhost:3000  # Grafana login
docker-compose down
```

---

### D.3: Create Kubernetes Manifests

**Directory:** `k8s/` (new directory at repo root)

Create these files in `k8s/`:

**File:** `k8s/namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: hyba-production
  labels:
    environment: production
```

**File:** `k8s/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hyba-config
  namespace: hyba-production
data:
  LOG_LEVEL: INFO
  REDIS_URL: redis://redis-service:6379
  DATABASE_URL: postgresql://hyba:hyba@postgres-service:5432/hyba
  API_WORKERS: "4"
```

**File:** `k8s/secret.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: hyba-secrets
  namespace: hyba-production
type: Opaque
stringData:
  postgres-password: "CHANGE_ME_IN_PRODUCTION"
  redis-password: "CHANGE_ME_IN_PRODUCTION"
  admin-api-key: "CHANGE_ME_IN_PRODUCTION"
```

**File:** `k8s/postgres-deployment.yaml`
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: hyba-production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 50Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: hyba-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_USER
          value: hyba
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hyba-secrets
              key: postgres-password
        - name: POSTGRES_DB
          value: hyba
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        livenessProbe:
          exec:
            command: ["pg_isready", "-U", "hyba"]
          initialDelaySeconds: 10
          periodSeconds: 10
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: hyba-production
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  type: ClusterIP
```

**File:** `k8s/redis-deployment.yaml`
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: hyba-production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: hyba-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
          - redis-server
          - "--appendonly"
          - "yes"
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        livenessProbe:
          exec:
            command: ["redis-cli", "ping"]
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: hyba-production
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
  type: ClusterIP
```

**File:** `k8s/backend-deployment.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hyba-backend
  namespace: hyba-production
  labels:
    app: hyba-backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
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
        image: hyba-backend:latest
        imagePullPolicy: Always
        ports:
        - name: http
          containerPort: 8000
        envFrom:
        - configMapRef:
            name: hyba-config
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hyba-secrets
              key: postgres-password
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: hyba-secrets
              key: redis-password
        livenessProbe:
          httpGet:
            path: /api/health
            port: http
          initialDelaySeconds: 15
          periodSeconds: 20
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/health
            port: http
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 2
          failureThreshold: 2
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi

---
apiVersion: v1
kind: Service
metadata:
  name: hyba-backend-service
  namespace: hyba-production
  labels:
    app: hyba-backend
spec:
  type: LoadBalancer
  selector:
    app: hyba-backend
  ports:
  - name: http
    port: 80
    targetPort: http
    protocol: TCP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hyba-backend-hpa
  namespace: hyba-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hyba-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Checkpoint D.3:**
```bash
# Validate K8s manifests
kubectl apply -f k8s/ --dry-run=client -o yaml
# Or deploy to local cluster (if minikube/kind available)
kubectl apply -f k8s/
kubectl get pods -n hyba-production
```



---

## VECTOR E: GitHub Actions CI/CD Pipeline
**Estimated Time:** 2-3 days

### E.1: Create CI Workflow

**File:** `.github/workflows/ci.yml` (already exists, update it)

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: hyba
          POSTGRES_PASSWORD: hyba
          POSTGRES_DB: hyba
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12.7'
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r python_backend/requirements.txt
        pip install -r python_backend/requirements.test.txt

    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 python_backend --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 python_backend --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

    - name: Type check with mypy
      run: |
        pip install mypy
        mypy python_backend --ignore-missing-imports || true

    - name: Run pytest
      env:
        DATABASE_URL: postgresql://hyba:hyba@localhost:5432/hyba
        REDIS_URL: redis://localhost:6379
      run: |
        python -m pytest tests/test_fault_tolerant_quantum.py \
          tests/test_quantum_as_a_service_api.py \
          tests/test_computational_intelligence_service_api.py \
          tests/test_commercial_public_api.py -v --cov=python_backend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: false
```

**Checkpoint E.1:**
```bash
# Test locally
act -j test  # Requires act tool (GitHub Actions locally)
# Or commit to branch and watch GitHub Actions tab
```

### E.2: Create Docker Build & Push Workflow

**File:** `.github/workflows/docker-build.yml` (new)

```yaml
name: Docker Build & Push

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      packages: write
      contents: read

    steps:
    - uses: actions/checkout@v4

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./Dockerfile
        push: true
        tags: |
          ghcr.io/${{ github.repository }}/backend:latest
          ghcr.io/${{ github.repository }}/backend:${{ github.sha }}
          ${{ startsWith(github.ref, 'refs/tags/') && format('ghcr.io/{0}/backend:{1}', github.repository, github.ref_name) || '' }}
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - name: Create deployment artifact
      if: startsWith(github.ref, 'refs/tags/')
      run: |
        echo "Version: ${{ github.ref_name }}" > deployment-info.txt
        echo "Image: ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }}" >> deployment-info.txt

    - name: Upload artifact
      if: startsWith(github.ref, 'refs/tags/')
      uses: actions/upload-artifact@v3
      with:
        name: deployment-info
        path: deployment-info.txt
```

**Checkpoint E.2:**
```bash
# Commit to main branch triggers build
# Check GitHub Actions > Docker Build & Push
# Verify image appears in ghcr.io (Container Registry)
```

### E.3: Create Deployment Workflow

**File:** `.github/workflows/deploy.yml` (new)

```yaml
name: Deploy to Kubernetes

on:
  push:
    tags: ['v*']

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
    - uses: actions/checkout@v4

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3
      with:
        version: 'v1.27.0'

    - name: Configure kubeconfig
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > $HOME/.kube/config
        chmod 600 $HOME/.kube/config

    - name: Update image in K8s
      run: |
        kubectl set image deployment/hyba-backend \
          backend=ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }} \
          -n hyba-production

    - name: Wait for rollout
      run: |
        kubectl rollout status deployment/hyba-backend \
          -n hyba-production --timeout=5m

    - name: Run smoke tests
      run: |
        BACKEND_URL=$(kubectl get service hyba-backend-service \
          -n hyba-production -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        curl -f http://$BACKEND_URL/api/health || exit 1

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
    - uses: actions/checkout@v4

    - name: Set up kubectl
      uses: azure/setup-kubectl@v3

    - name: Configure kubeconfig
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBE_CONFIG_PROD }}" | base64 -d > $HOME/.kube/config
        chmod 600 $HOME/.kube/config

    - name: Update image in K8s
      run: |
        kubectl set image deployment/hyba-backend \
          backend=ghcr.io/${{ github.repository }}/backend:${{ github.ref_name }} \
          -n hyba-production

    - name: Wait for rollout
      run: |
        kubectl rollout status deployment/hyba-backend \
          -n hyba-production --timeout=5m

    - name: Verify deployment
      run: |
        kubectl get pods -n hyba-production
        kubectl logs -n hyba-production -l app=hyba-backend --tail=20
```

**Checkpoint E.3:**
```bash
# Create a release tag
git tag v0.1.0
git push origin v0.1.0
# GitHub Actions deploys to staging first, then waits for approval
# Check Actions tab for manual approval UI
```



---

## VECTOR F: Data Persistence & Audit Logging
**Estimated Time:** 2-3 days

### F.1: Create Database Schema

**File:** `scripts/init-db.sql` (new)

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tenants table
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  billing_tier VARCHAR(50) DEFAULT 'starter',
  monthly_quota_units INTEGER DEFAULT 100000,
  cost_per_unit DECIMAL(10, 4) DEFAULT 0.0001,
  active BOOLEAN DEFAULT TRUE
);

-- API Keys table (immutable, append-only)
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  key_hash VARCHAR(64) NOT NULL UNIQUE,
  name VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_used_at TIMESTAMP,
  revoked_at TIMESTAMP,
  CONSTRAINT not_revoked CHECK (revoked_at IS NULL)
);

CREATE INDEX idx_api_keys_tenant ON api_keys(tenant_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- Workload Executions table
CREATE TABLE workload_executions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  instance_id UUID NOT NULL,
  workload_type VARCHAR(50) NOT NULL,
  circuit_depth INTEGER NOT NULL,
  defect_count INTEGER NOT NULL,
  pairing_weight DECIMAL(10, 4) NOT NULL,
  compute_units INTEGER NOT NULL,
  estimated_cost DECIMAL(12, 6) NOT NULL,
  actual_cost DECIMAL(12, 6) NOT NULL,
  status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'failed', 'cancelled')),
  error_message TEXT,
  logical_error_rate DECIMAL(20, 18),
  executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  duration_ms INTEGER
);

CREATE INDEX idx_workload_tenant ON workload_executions(tenant_id);
CREATE INDEX idx_workload_executed_at ON workload_executions(executed_at);
CREATE INDEX idx_workload_status ON workload_executions(status);

-- Audit Log table (immutable)
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('admin', 'customer', 'system')),
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(50),
  resource_id VARCHAR(255),
  details JSONB,
  ip_address INET,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);

-- Usage Summary table (materialized view refreshed daily)
CREATE TABLE usage_summary (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
  year INT NOT NULL,
  month INT NOT NULL,
  total_executions INTEGER DEFAULT 0,
  total_compute_units INTEGER DEFAULT 0,
  total_cost DECIMAL(12, 6) DEFAULT 0,
  avg_logical_error_rate DECIMAL(20, 18),
  success_rate DECIMAL(5, 2),
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT valid_month CHECK (month >= 1 AND month <= 12)
);

CREATE INDEX idx_usage_summary_tenant_month ON usage_summary(tenant_id, year, month);

-- Quota Tracking table (real-time)
CREATE TABLE quota_tracking (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
  month INT NOT NULL,
  year INT NOT NULL,
  units_consumed INTEGER DEFAULT 0,
  units_available INTEGER NOT NULL,
  last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT valid_month CHECK (month >= 1 AND month <= 12)
);

CREATE INDEX idx_quota_tenant_month ON quota_tracking(tenant_id, year, month);

-- Functions for audit logging
CREATE OR REPLACE FUNCTION audit_log_event(
  p_tenant_id UUID,
  p_actor_type VARCHAR,
  p_action VARCHAR,
  p_resource_type VARCHAR,
  p_resource_id VARCHAR,
  p_details JSONB DEFAULT NULL,
  p_ip_address INET DEFAULT NULL
) RETURNS void AS $$
BEGIN
  INSERT INTO audit_log (tenant_id, actor_type, action, resource_type, resource_id, details, ip_address)
  VALUES (p_tenant_id, p_actor_type, p_action, p_resource_type, p_resource_id, p_details, p_ip_address);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate quota tracking
CREATE OR REPLACE FUNCTION update_quota_tracking()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE quota_tracking
  SET units_consumed = units_consumed + NEW.compute_units
  WHERE tenant_id = NEW.tenant_id
    AND month = EXTRACT(MONTH FROM NEW.executed_at)
    AND year = EXTRACT(YEAR FROM NEW.executed_at);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_workload_quota
AFTER INSERT ON workload_executions
FOR EACH ROW
EXECUTE FUNCTION update_quota_tracking();

-- Insert sample tenant
INSERT INTO tenants (name, email, billing_tier, monthly_quota_units, cost_per_unit)
VALUES ('Demo Customer', 'demo@hyba.io', 'starter', 100000, 0.0001);

COMMIT;
```

**Checkpoint F.1:**
```bash
# Test schema in docker-compose
docker-compose exec postgres psql -U hyba -d hyba -c "\dt"
# Should list: tenants, api_keys, workload_executions, audit_log, etc.
```

### F.2: Create Python ORM Models

**File:** `python_backend/hyba_genesis_api/models/database.py` (new)

```python
"""SQLAlchemy ORM models for HYBA production database."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, ForeignKey, 
    DECIMAL, Index, CheckConstraint, Enum, JSON, INET, BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
import enum

Base = declarative_base()


class BillingTier(str, enum.Enum):
    """Billing tiers for customers."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class WorkloadStatus(str, enum.Enum):
    """Workload execution status."""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActorType(str, enum.Enum):
    """Types of actors in audit log."""
    ADMIN = "admin"
    CUSTOMER = "customer"
    SYSTEM = "system"


class Tenant(Base):
    """Multi-tenant customer."""
    __tablename__ = "tenants"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    billing_tier = Column(String(50), default="starter")
    monthly_quota_units = Column(Integer, default=100000)
    cost_per_unit = Column(DECIMAL(10, 4), default=Decimal("0.0001"))
    active = Column(Boolean, default=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    workloads = relationship("WorkloadExecution", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")


class APIKey(Base):
    """API keys for tenant authentication."""
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_api_keys_tenant", "tenant_id"),
        Index("idx_api_keys_hash", "key_hash"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    key_hash = Column(String(64), nullable=False, unique=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime)
    revoked_at = Column(DateTime)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")


class WorkloadExecution(Base):
    """Fault-tolerant workload execution records."""
    __tablename__ = "workload_executions"
    __table_args__ = (
        Index("idx_workload_tenant", "tenant_id"),
        Index("idx_workload_executed_at", "executed_at"),
        Index("idx_workload_status", "status"),
        CheckConstraint("status IN ('success', 'failed', 'cancelled')"),
    )

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    workload_type = Column(String(50), nullable=False)
    circuit_depth = Column(Integer, nullable=False)
    defect_count = Column(Integer, nullable=False)
    pairing_weight = Column(DECIMAL(10, 4), nullable=False)
    compute_units = Column(Integer, nullable=False)
    estimated_cost = Column(DECIMAL(12, 6), nullable=False)
    actual_cost = Column(DECIMAL(12, 6), nullable=False)
    status = Column(String(50), nullable=False, default="success")
    error_message = Column(String, nullable=True)
    logical_error_rate = Column(DECIMAL(20, 18), nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_ms = Column(Integer, nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="workloads")


class AuditLog(Base):
    """Immutable audit trail of all operations."""
    __tablename__ = "audit_log"
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id"),
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_action", "action"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    actor_type = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(INET, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")


class QuotaTracking(Base):
    """Real-time quota tracking per tenant per month."""
    __tablename__ = "quota_tracking"
    __table_args__ = (
        Index("idx_quota_tenant_month", "tenant_id", "year", "month"),
        CheckConstraint("month >= 1 AND month <= 12"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    units_consumed = Column(Integer, default=0)
    units_available = Column(Integer, nullable=False)
    last_reset = Column(DateTime, default=datetime.utcnow)
```

**Checkpoint F.2:**
```bash
# Test imports
python3 -c "from python_backend.hyba_genesis_api.models.database import Tenant, WorkloadExecution, AuditLog; print('✅ Models imported successfully')"
```

### F.3: Create Database Service Layer

**File:** `python_backend/hyba_genesis_api/services/database_service.py` (new)

```python
"""Database service for HYBA production operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import create_engine, func, and_
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from ..models.database import (
    Base, Tenant, APIKey, WorkloadExecution, AuditLog, QuotaTracking,
    WorkloadStatus, ActorType
)


class DatabaseService:
    """Manages database connections and operations."""

    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            poolclass=NullPool,  # Important for production reliability
            echo=False,
            connect_args={"connect_timeout": 10}
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def log_audit_event(
        self,
        tenant_id: UUID,
        actor_type: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log an audit event."""
        session = self.get_session()
        try:
            log = AuditLog(
                tenant_id=tenant_id,
                actor_type=actor_type,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
            )
            session.add(log)
            session.commit()
        finally:
            session.close()

    def record_workload_execution(
        self,
        tenant_id: UUID,
        instance_id: UUID,
        workload_type: str,
        circuit_depth: int,
        defect_count: int,
        pairing_weight: Decimal,
        compute_units: int,
        estimated_cost: Decimal,
        actual_cost: Decimal,
        status: str,
        logical_error_rate: Optional[float] = None,
        duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> UUID:
        """Record a workload execution."""
        session = self.get_session()
        try:
            execution = WorkloadExecution(
                tenant_id=tenant_id,
                instance_id=instance_id,
                workload_type=workload_type,
                circuit_depth=circuit_depth,
                defect_count=defect_count,
                pairing_weight=pairing_weight,
                compute_units=compute_units,
                estimated_cost=estimated_cost,
                actual_cost=actual_cost,
                status=status,
                logical_error_rate=logical_error_rate,
                duration_ms=duration_ms,
                error_message=error_message,
            )
            session.add(execution)
            session.commit()
            return execution.id
        finally:
            session.close()

    def get_tenant_usage(self, tenant_id: UUID, year: int, month: int) -> dict:
        """Get tenant usage for a specific month."""
        session = self.get_session()
        try:
            result = session.query(
                func.count(WorkloadExecution.id).label("total_executions"),
                func.sum(WorkloadExecution.compute_units).label("total_units"),
                func.sum(WorkloadExecution.actual_cost).label("total_cost"),
                func.avg(WorkloadExecution.logical_error_rate).label("avg_error_rate"),
            ).filter(
                and_(
                    WorkloadExecution.tenant_id == tenant_id,
                    func.extract('year', WorkloadExecution.executed_at) == year,
                    func.extract('month', WorkloadExecution.executed_at) == month,
                )
            ).first()

            return {
                "total_executions": result.total_executions or 0,
                "total_compute_units": result.total_units or 0,
                "total_cost": float(result.total_cost or 0),
                "avg_logical_error_rate": float(result.avg_error_rate or 0),
            }
        finally:
            session.close()

    def check_quota(self, tenant_id: UUID, units_needed: int) -> bool:
        """Check if tenant has quota available."""
        session = self.get_session()
        try:
            quota = session.query(QuotaTracking).filter(
                QuotaTracking.tenant_id == tenant_id
            ).first()
            
            if not quota:
                return False
            
            return (quota.units_consumed + units_needed) <= quota.units_available
        finally:
            session.close()

    def close(self):
        """Close all database connections."""
        self.engine.dispose()
```

**Checkpoint F.3:**
```bash
# Test database service
python3 << 'EOF'
from python_backend.hyba_genesis_api.services.database_service import DatabaseService
db = DatabaseService("postgresql://hyba:hyba@localhost:5432/hyba")
print("✅ DatabaseService initialized")
db.close()
EOF
```



---

## 🔄 Integration & End-to-End Testing

### Integration Test: Full DEF Stack

**File:** `tests/test_def_integration.py` (new)

```python
"""Integration test: Vectors D (Docker), E (CI/CD), F (Persistence)."""

import pytest
import os
from uuid import uuid4
from decimal import Decimal

# These tests run against docker-compose stack
SKIP_IF_NO_DOCKER = pytest.mark.skipif(
    os.getenv("CI") != "true" and not os.path.exists("/.dockerenv"),
    reason="Requires Docker environment"
)


@SKIP_IF_NO_DOCKER
def test_backend_health_check():
    """Verify backend health endpoint responds."""
    import requests
    response = requests.get("http://backend:8000/api/health", timeout=5)
    assert response.status_code == 200


@SKIP_IF_NO_DOCKER
def test_postgres_connectivity():
    """Verify PostgreSQL is accessible."""
    from sqlalchemy import create_engine
    engine = create_engine("postgresql://hyba:hyba@postgres:5432/hyba")
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        assert result.fetchone()[0] == 1


@SKIP_IF_NO_DOCKER
def test_redis_connectivity():
    """Verify Redis is accessible."""
    import redis
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    assert r.ping()


@SKIP_IF_NO_DOCKER
def test_audit_logging():
    """Test audit log records operations."""
    from python_backend.hyba_genesis_api.services.database_service import DatabaseService
    
    db = DatabaseService("postgresql://hyba:hyba@postgres:5432/hyba")
    tenant_id = uuid4()
    
    db.log_audit_event(
        tenant_id=tenant_id,
        actor_type="test",
        action="test_operation",
        details={"test": "data"}
    )
    
    # Verify it was recorded
    session = db.get_session()
    from python_backend.hyba_genesis_api.models.database import AuditLog
    log = session.query(AuditLog).filter_by(tenant_id=tenant_id).first()
    session.close()
    db.close()
    
    assert log is not None
    assert log.action == "test_operation"


@SKIP_IF_NO_DOCKER
def test_workload_execution_recording():
    """Test workload execution records with cost tracking."""
    from python_backend.hyba_genesis_api.services.database_service import DatabaseService
    
    db = DatabaseService("postgresql://hyba:hyba@postgres:5432/hyba")
    tenant_id = uuid4()
    
    execution_id = db.record_workload_execution(
        tenant_id=tenant_id,
        instance_id=uuid4(),
        workload_type="surface_code_cycle",
        circuit_depth=10,
        defect_count=5,
        pairing_weight=Decimal("2.5"),
        compute_units=125,
        estimated_cost=Decimal("0.01250"),
        actual_cost=Decimal("0.01250"),
        status="success",
        logical_error_rate=1.5e-8,
        duration_ms=1500,
    )
    
    # Verify it was recorded
    session = db.get_session()
    from python_backend.hyba_genesis_api.models.database import WorkloadExecution
    execution = session.query(WorkloadExecution).filter_by(id=execution_id).first()
    session.close()
    db.close()
    
    assert execution is not None
    assert execution.compute_units == 125
    assert float(execution.actual_cost) == 0.01250


@SKIP_IF_NO_DOCKER
def test_quota_tracking():
    """Test quota enforcement."""
    from python_backend.hyba_genesis_api.services.database_service import DatabaseService
    
    db = DatabaseService("postgresql://hyba:hyba@postgres:5432/hyba")
    tenant_id = uuid4()
    
    # Assume quota exists
    session = db.get_session()
    from python_backend.hyba_genesis_api.models.database import QuotaTracking
    quota = QuotaTracking(
        tenant_id=tenant_id,
        month=6,
        year=2026,
        units_available=1000,
    )
    session.add(quota)
    session.commit()
    session.close()
    
    # Should pass with sufficient quota
    assert db.check_quota(tenant_id, 500) is True
    
    # Should fail with exceeded quota
    assert db.check_quota(tenant_id, 1001) is False
    
    db.close()
```

**Checkpoint Integration:**
```bash
# Run with docker-compose
docker-compose up -d
docker-compose exec backend python -m pytest tests/test_def_integration.py -v
docker-compose down
```

---

## 📊 Deployment Verification Checklist

### Local Testing (docker-compose)
- [ ] `docker-compose up -d` completes without errors
- [ ] All services report "healthy" status
- [ ] Backend responds to `/api/health`
- [ ] PostgreSQL schema initialized
- [ ] Redis accepts connections
- [ ] Prometheus scrapes metrics
- [ ] Grafana dashboard loads
- [ ] All integration tests pass

### Kubernetes Staging
- [ ] `kubectl apply -f k8s/` succeeds
- [ ] All pods reach "Running" state
- [ ] Services get LoadBalancer IPs
- [ ] Health checks pass
- [ ] Smoke tests pass against LB IP
- [ ] Logs show no errors
- [ ] Metrics appear in Prometheus

### CI/CD Pipeline
- [ ] PR triggers test job (passes)
- [ ] Merge to main triggers Docker build
- [ ] Docker image appears in ghcr.io
- [ ] Tag `v*` triggers deployment workflow
- [ ] Staging deployment succeeds
- [ ] Production deployment requires approval
- [ ] Rollback mechanism works

---

## 🎯 Acceptance Criteria

### Vector D (Docker/K8s): COMPLETE when
```
✅ docker-compose.yml exists and runs locally
✅ All K8s manifests validate via kubectl
✅ Backend Dockerfile builds without warnings
✅ HPA scales replicas 3-10 based on CPU
✅ Service mesh (or basic LB) routes traffic correctly
```

### Vector E (CI/CD): COMPLETE when
```
✅ PR blocks if tests fail
✅ Merge to main auto-builds Docker image
✅ Tag v* auto-deploys to staging + production
✅ Approval gate prevents unreviewed prod deployments
✅ Rollback command reverts to previous version
```

### Vector F (Persistence): COMPLETE when
```
✅ PostgreSQL schema initialized on startup
✅ All workload executions recorded with cost
✅ Audit log captures all operations
✅ Quota tracking prevents overage
✅ Usage queries return accurate data
✅ ORM models pass type checking
```

---

## 🚀 Execution Timeline for Cloud Agent

**Recommended parallelization:**

```
DAY 1-2: Vector D (Docker/K8s)
├─ D.1: Dockerfile (4 hours)
├─ D.2: docker-compose.yml (4 hours)
└─ D.3: K8s manifests (4 hours)

DAY 2-3: Vector E (CI/CD) [can start mid-Day 1]
├─ E.1: CI workflow (3 hours)
├─ E.2: Docker build workflow (3 hours)
└─ E.3: Deployment workflow (4 hours)

DAY 3-4: Vector F (Persistence) [can start mid-Day 2]
├─ F.1: Database schema (3 hours)
├─ F.2: ORM models (3 hours)
└─ F.3: Database service layer (4 hours)

DAY 5: Integration & Testing
├─ Integration tests (2 hours)
├─ Local testing via docker-compose (2 hours)
├─ K8s local testing (minikube) (2 hours)
└─ Documentation + checklist review (2 hours)

RESULT: Production-grade infrastructure ready for deployment
```

---

## 📝 Handoff to DevOps

Once D, E, F complete, provide to DevOps/SRE team:

1. **docker-compose.yml** - Local development stack
2. **k8s/** - Production Kubernetes manifests
3. **.github/workflows/** - Automated deployment pipeline
4. **Database schema** - PostgreSQL initialization script
5. **ORM models** - Python SQLAlchemy layer
6. **Deployment runbook** - How to scale, rollback, update
7. **Monitoring dashboard** - Grafana queries for observability

---

## ⚠️ Critical Notes for Cloud Agent

### Before Starting
- Verify all 31 tests pass on current commit
- Ensure Docker Desktop is running
- Confirm kubectl/minikube available (optional but recommended)
- Check GitHub repo has Actions enabled

### During Implementation
- Commit each major component (D.1, D.2, D.3, E.1, E.2, E.3, F.1, F.2, F.3)
- Run checkpoints after each section
- If checkpoint fails, diagnose before proceeding
- Don't skip testing phases

### After Completion
- Run full integration test suite
- Document any deviations from this plan
- Identify blockers for next phase (G, H, I)
- Recommend timeline for production launch

---

**Next Phase After DEF:** Vectors G, H, I (Customer Portal, Multi-Cloud, Analytics)

**Estimated Total Timeline:** 5-7 days to production-ready infrastructure.
