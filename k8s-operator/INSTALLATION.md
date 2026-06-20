# HYBA Kubernetes Operator Installation Guide

## Prerequisites

- Kubernetes 1.24+ cluster
- kubectl installed and configured
- Helm 3.0+ (optional but recommended)
- Go 1.21+ (for building from source)

## Installation Methods

### Method 1: Using Helm (Recommended)

#### 1. Add the HYBA Helm Repository

```bash
helm repo add hyba https://charts.hyba.ai
helm repo update
```

#### 2. Create a Namespace

```bash
kubectl create namespace hyba-system
```

#### 3. Install the Operator

```bash
helm install hyba-operator hyba/hyba-operator \
  --namespace hyba-system \
  --create-namespace \
  --set image.tag=latest
```

#### 4. Verify Installation

```bash
kubectl get deployment -n hyba-system
kubectl get pods -n hyba-system
```

### Method 2: Using Kubectl (Manual YAML)

#### 1. Build and Push the Docker Image

```bash
cd k8s-operator
docker build -t your-registry/hyba-operator:latest .
docker push your-registry/hyba-operator:latest
```

#### 2. Create CRD

```bash
kubectl apply -f api/v1/ciaasservice_types.go  # Apply CRD manifest
```

#### 3. Create RBAC Resources

```bash
kubectl apply -f rbac.yaml
```

#### 4. Deploy the Operator

```bash
kubectl apply -f operator-deployment.yaml
```

### Method 3: Building from Source

#### 1. Clone the Repository

```bash
git clone https://github.com/hyba-ai/k8s-operator.git
cd k8s-operator
```

#### 2. Install Dependencies

```bash
go mod download
go mod tidy
```

#### 3. Build the Binary

```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o manager main.go
```

#### 4. Build Docker Image

```bash
docker build -t hyba-operator:latest .
docker push your-registry/hyba-operator:latest
```

#### 5. Deploy with Helm

```bash
helm install hyba-operator ./helm/hyba-operator \
  --namespace hyba-system \
  --create-namespace
```

## Configuration

### Environment Variables

```bash
ENABLE_WEBHOOKS=true              # Enable admission webhooks
LEADER_ELECTION=false             # Enable leader election for HA
LOG_LEVEL=info                    # Log level (debug, info, warn, error)
```

### Helm Values

Override default values during installation:

```bash
helm install hyba-operator hyba/hyba-operator \
  --namespace hyba-system \
  --set replicaCount=2 \
  --set leaderElection.enabled=true \
  --set resources.limits.memory=256Mi
```

## Verification

### Check Operator Status

```bash
# Check operator pods
kubectl get pods -n hyba-system

# Check operator logs
kubectl logs -n hyba-system -l app.kubernetes.io/name=hyba-operator -f

# Check CRDs are registered
kubectl get crds | grep hyba.ai
```

### Create a Sample Service

```bash
kubectl apply -f examples/basic-service.yaml
kubectl get ciaasservices
kubectl describe ciaasservice sample-ml-service
```

## Monitoring

### Enable Prometheus Metrics

```bash
# Port forward to metrics endpoint
kubectl port-forward -n hyba-system svc/hyba-operator 8080:8080

# Access metrics at http://localhost:8080/metrics
```

### Logs

```bash
# View operator logs
kubectl logs -n hyba-system deployment/hyba-operator

# Stream logs in real-time
kubectl logs -n hyba-system deployment/hyba-operator -f

# View pod events
kubectl describe pod -n hyba-system -l app.kubernetes.io/name=hyba-operator
```

## Troubleshooting

### Operator Pod Not Starting

```bash
# Check pod status
kubectl describe pod -n hyba-system -l app.kubernetes.io/name=hyba-operator

# Check events
kubectl get events -n hyba-system --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n hyba-system -l app.kubernetes.io/name=hyba-operator
```

### CRD Registration Issues

```bash
# Verify CRD exists
kubectl get crds | grep ciaasservice

# Describe CRD
kubectl describe crd ciaasservices.hyba.ai

# Apply CRD directly if needed
kubectl apply -f config/crd/bases/hyba.ai_ciaasservices.yaml
```

### Service Not Creating

```bash
# Check operator logs for errors
kubectl logs -n hyba-system -l app.kubernetes.io/name=hyba-operator | grep -i error

# Check events on the service
kubectl describe ciaasservice <service-name>

# Verify RBAC permissions
kubectl auth can-i create deployments --as=system:serviceaccount:hyba-system:hyba-operator
```

## Uninstallation

### Using Helm

```bash
helm uninstall hyba-operator -n hyba-system
kubectl delete namespace hyba-system
```

### Manual Cleanup

```bash
kubectl delete -f operator-deployment.yaml
kubectl delete -f rbac.yaml
kubectl delete crd ciaasservices.hyba.ai
```

## Advanced Configuration

### High Availability

```bash
helm install hyba-operator hyba/hyba-operator \
  --namespace hyba-system \
  --set replicaCount=3 \
  --set leaderElection.enabled=true \
  --set affinity.podAntiAffinity.preferredDuringSchedulingIgnoredDuringExecution[0].weight=100
```

### Custom Resource Limits

```bash
helm install hyba-operator hyba/hyba-operator \
  --namespace hyba-system \
  --set resources.limits.cpu=1000m \
  --set resources.limits.memory=512Mi \
  --set resources.requests.cpu=200m \
  --set resources.requests.memory=128Mi
```

### Node Affinity

```bash
helm install hyba-operator hyba/hyba-operator \
  --namespace hyba-system \
  --set nodeSelector."kubernetes\.io/hostname"=operator-node
```

## Support

For issues and support:
- GitHub Issues: https://github.com/hyba-ai/k8s-operator/issues
- Documentation: https://docs.hyba.ai
- Slack: https://hyba.ai/slack
