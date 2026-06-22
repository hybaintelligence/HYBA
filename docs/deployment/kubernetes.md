# Kubernetes Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying Salamander Regeneration Framework on Kubernetes, including production-ready configurations, security best practices, and operational procedures.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Ingress    │  │  Cert-Manager│  │  Prometheus  │    │
│  │  Controller  │  │   (TLS)      │  │  (Monitoring)│    │
│  └──────┬───────┘  └──────────────┘  └──────────────┘    │
│         │                                                 │
│  ┌──────▼──────────────────────────────────────────┐      │
│  │              Service Mesh (Istio)                │      │
│  └──────┬──────────────────────────────────────────┘      │
│         │                                                 │
│  ┌──────▼──────────────────────────────────────────┐      │
│  │         Salamander Deployment                    │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │      │
│  │  │  Frontend  │  │   API      │  │  Regeneration│ │      │
│  │  │  Replicas  │  │  Replicas  │  │   Engine    │ │      │
│  │  │  (3 pods)  │  │  (3 pods)  │  │  (2 pods)   │ │      │
│  │  └────────────┘  └────────────┘  └────────────┘ │      │
│  │                                                │      │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐ │      │
│  │  │   Redis    │  │PostgreSQL  │  │  Blastema  │ │      │
│  │  │  (Cache)   │  │  (State)   │  │   State    │ │      │
│  │  │  (1 pod)   │  │  (1 pod)   │  │  (PVC)     │ │      │
│  │  └────────────┘  └────────────┘  └────────────┘ │      │
│  └──────────────────────────────────────────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes 1.24+
- Helm 3.10+
- cert-manager 1.10+ (for TLS)
- Istio 1.18+ (optional, for service mesh)
- Prometheus Operator (for monitoring)
- PostgreSQL 14+ (or use managed service)
- Redis 7+ (or use managed service)

## Installation

### Option 1: Helm Chart (Recommended)

```bash
# Add Helm repository
helm repo add salamander https://charts.salamander.yourorg.com
helm repo update

# Install with default values
helm install salamander salamander/salamander \
  --namespace salamander \
  --create-namespace \
  --set apiKey=your-api-key

# Install with custom values
helm install salamander salamander/salamander \
  --namespace salamander \
  --create-namespace \
  -f values.production.yaml
```

### Option 2: kubectl

```bash
# Create namespace
kubectl create namespace salamander

# Apply configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/blastema-pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

## Configuration

### values.production.yaml

```yaml
# Global configuration
global:
  imageRegistry: ghcr.io/yourorg
  imagePullSecrets:
    - name: regcred

# API configuration
api:
  replicaCount: 3
  image:
    repository: salamander/api
    tag: 1.0.0
    pullPolicy: IfNotPresent
  resources:
    requests:
      cpu: 500m
      memory: 512Mi
    limits:
      cpu: 2000m
      memory: 2Gi
  autoscaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
  env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: salamander-secrets
          key: database-url
    - name: REDIS_URL
      valueFrom:
        secretKeyRef:
          name: salamander-secrets
          key: redis-url
    - name: HYBA_API_KEYS
      valueFrom:
        secretKeyRef:
          name: salamander-secrets
          key: api-keys

# Regeneration engine
regeneration:
  replicaCount: 2
  image:
    repository: salamander/regeneration
    tag: 1.0.0
  resources:
    requests:
      cpu: 1000m
      memory: 1Gi
    limits:
      cpu: 4000m
      memory: 4Gi
  blastema:
    storage:
      size: 100Gi
      storageClass: fast-ssd

# Frontend
frontend:
  replicaCount: 3
  image:
    repository: salamander/frontend
    tag: 1.0.0
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi

# PostgreSQL
postgresql:
  enabled: true
  image:
    repository: postgres
    tag: 14-alpine
  auth:
    username: salamander
    password: changeme
    database: salamander
  primary:
    persistence:
      size: 50Gi
      storageClass: fast-ssd
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 2000m
        memory: 4Gi

# Redis
redis:
  enabled: true
  image:
    repository: redis
    tag: 7-alpine
  master:
    persistence:
      size: 10Gi
    resources:
      requests:
        cpu: 200m
        memory: 256Mi
      limits:
        cpu: 1000m
        memory: 1Gi

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  hosts:
    - host: salamander.yourorg.com
      paths:
        - path: /
          pathType: Prefix
          service: frontend
        - path: /api
          pathType: Prefix
          service: api
  tls:
    - secretName: salamander-tls
      hosts:
        - salamander.yourorg.com

# Monitoring
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
  alerts:
    - name: HighRegenerationLatency
      expr: histogram_quantile(0.99, rate(salamander_regeneration_duration_seconds_bucket[5m])) > 0.01
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High regeneration latency detected"
    - name: HighRegenerationFailureRate
      expr: rate(salamander_regeneration_failed_total[5m]) / rate(salamander_regeneration_total[5m]) > 0.1
      for: 2m
      labels:
        severity: critical
      annotations:
        summary: "High regeneration failure rate"

# Security
security:
  podSecurityPolicy:
    enabled: true
  networkPolicy:
    enabled: true
  rbac:
    enabled: true
```

## Deployment Manifests

### namespace.yaml

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: salamander
  labels:
    name: salamander
    environment: production
```

### configmap.yaml

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: salamander-config
  namespace: salamander
data:
  LOG_LEVEL: "INFO"
  MAX_REGENERATION_RETRIES: "3"
  RATE_LIMIT_MAX_REQUESTS: "5"
  RATE_LIMIT_WINDOW: "60"
  MAX_CONCURRENT_REGENERATIONS: "5"
  MAX_REGENERATION_DURATION: "300"
```

### secret.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: salamander-secrets
  namespace: salamander
type: Opaque
stringData:
  database-url: "postgresql://salamander:changeme@postgres:5432/salamander"
  redis-url: "redis://redis:6379/0"
  api-keys: "key1,key2,key3"
  hmac-secret: "your-hmac-secret-key-here"
```

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: salamander-api
  namespace: salamander
  labels:
    app: salamander-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: salamander-api
  template:
    metadata:
      labels:
        app: salamander-api
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: api
          image: ghcr.io/yourorg/salamander/api:1.0.0
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: salamander-secrets
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: salamander-secrets
                  key: redis-url
            - name: HYBA_API_KEYS
              valueFrom:
                secretKeyRef:
                  name: salamander-secrets
                  key: api-keys
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 2000m
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 5
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
```

### service.yaml

```yaml
apiVersion: v1
kind: Service
metadata:
  name: salamander-api
  namespace: salamander
spec:
  selector:
    app: salamander-api
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
  type: ClusterIP
```

### ingress.yaml

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: salamander-ingress
  namespace: salamander
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - salamander.yourorg.com
      secretName: salamander-tls
  rules:
    - host: salamander.yourorg.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: salamander-frontend
                port:
                  number: 80
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: salamander-api
                port:
                  number: 80
```

### hpa.yaml

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: salamander-api-hpa
  namespace: salamander
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: salamander-api
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

## Operations

### Backup and Restore

```bash
# Backup PostgreSQL
kubectl exec -n salamander postgres-0 -- pg_dump -U salamander salamander > backup.sql

# Backup Blastema State (PVC)
kubectl exec -n salamander regeneration-engine-0 -- tar czf /tmp/blastema-backup.tar.gz /data/blastema
kubectl cp salamander/regeneration-engine-0:/tmp/blastema-backup.tar.gz ./blastema-backup.tar.gz

# Restore
kubectl exec -i -n salamander postgres-0 -- psql -U salamander salamander < backup.sql
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment salamander-api -n salamander --replicas=5

# View HPA status
kubectl get hpa -n salamander
```

### Updates

```bash
# Rolling update
helm upgrade salamander salamander/salamander \
  --namespace salamander \
  --set api.image.tag=1.1.0 \
  --set regeneration.image.tag=1.1.0

# Rollback
helm rollback salamander -n salamander
```

### Monitoring

```bash
# View logs
kubectl logs -n salamander -l app=salamander-api --tail=100 -f

# Port-forward for local access
kubectl port-forward -n salamander svc/salamander-api 8000:80

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   ```bash
   kubectl logs -n salamander <pod-name> --previous
   kubectl describe pod -n salamander <pod-name>
   ```

2. **High Memory Usage**
   ```bash
   kubectl top pods -n salamander
   kubectl describe node <node-name>
   ```

3. **Network Issues**
   ```bash
   kubectl get networkpolicy -n salamander
   kubectl describe networkpolicy -n salamander
   ```

## Security Hardening

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: salamander
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: salamander-netpol
  namespace: salamander
spec:
  podSelector:
    matchLabels:
      app: salamander-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: redis
      ports:
        - protocol: TCP
          port: 6379
```

## References

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Documentation](https://helm.sh/docs/)
- [cert-manager Documentation](https://cert-manager.io/docs/)
- [Istio Documentation](https://istio.io/latest/docs/)

---

**Last Updated**: 2026-06-22  
**Owner**: Platform Engineering Team  
**Next Review**: 2026-07-22