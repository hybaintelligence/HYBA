# Intelligence Fabric Production Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the HYBA Recursive Structural Learning system in a production environment. The system implements mathematical frameworks for code structure analysis that computes structural metrics and generates parameter proposals.

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or Windows with WSL2
- **Python**: 3.12+
- **Docker**: 20.10+ with Docker Compose 2.0+
- **Memory**: Minimum 4GB RAM, 8GB recommended
- **Storage**: Minimum 10GB free space for persistence volume
- **CPU**: Multi-core processor recommended for concurrent operations

### Required Dependencies

All dependencies are listed in:
- `python_backend/requirements.txt` (backend dependencies)
- `python_backend/hyba_genesis_api/requirements.txt` (API-specific dependencies)

Key dependencies include:
- fastapi==0.136.1
- uvicorn[standard]==0.47.0
- numpy==2.4.6
- scipy==1.17.1
- httpx==0.28.1
- hypothesis (for property testing)

## Installation

### 1. Clone and Setup Repository

```bash
git clone <repository-url>
cd HYBA_FULLSTACK
```

### 2. Install Python Dependencies

```bash
# Install backend dependencies
python -m pip install -r python_backend/requirements.txt

# Install API-specific dependencies
python -m pip install -r python_backend/hyba_genesis_api/requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required Security Variables
JWT_SECRET=your-secure-jwt-secret-here
HYBA_OPERATOR_CREDENTIALS=your-operator-credentials

# Production Environment
NODE_ENV=production
HYBA_ENV=production
HYBA_ALLOW_DEV_FIXTURES=false

# Enhanced Theoretical Framework (Optional - defaults provided)
HYBA_SYSTEM_COMPLEXITY=high
HYBA_COMPUTATIONAL_BUDGET=high
HYBA_PULVINI_PHI_TIER=12
HYBA_ENABLE_ENHANCED_PENROSE_OR=true
HYBA_ENABLE_ENHANCED_IIT_PARTITIONING=true
HYBA_ENABLE_DEUTSCH_SUBSTRATE=true
HYBA_ENABLE_DYNAMIC_PHI_SCALING=true
HYBA_ENABLE_ASYNC_ENHANCED_ANALYSIS=true

# Recursive Structural Learning (Optional - disabled by default)
HYBA_ENABLE_REFLEXIVE_DAEMON=false
HYBA_RICCI_STEP_SIZE=0.01
HYBA_ONTOLOGICAL_PERSISTENCE_PATH=/app/persistence/grace.json
HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS=60

# Pool Configuration (if using live mining)
HYBA_POOL_NICEHASH_URL=
HYBA_POOL_NICEHASH_USERNAME=
HYBA_POOL_NICEHASH_PASSWORD=
# ... other pool configurations
```

## Docker Deployment

### 1. Build Docker Images

```bash
docker compose -f docker-compose.production.yml build
```

### 2. Start Services

```bash
docker compose -f docker-compose.production.yml up -d
```

### 3. Verify Deployment

```bash
# Check service health
docker compose -f docker-compose.production.yml ps

# Check backend health
curl http://localhost:3001/api/health/readiness

# Check intelligence fabric health
curl http://localhost:3001/api/v1/intelligence/health
```

### 4. View Logs

```bash
# View all logs
docker compose -f docker-compose.production.yml logs -f

# View backend logs specifically
docker compose -f docker-compose.production.yml logs -f hyba-backend

# View runtime logs
docker compose -f docker-compose.production.yml logs -f hyba-runtime
```

## Enabling Recursive Structural Learning

The reflexive daemon is **disabled by default** for safety. To enable:

### Option 1: Environment Variable

Set `HYBA_ENABLE_REFLEXIVE_DAEMON=true` in your environment or `.env` file:

```bash
export HYBA_ENABLE_REFLEXIVE_DAEMON=true
export HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS=300
```

### Option 2: Docker Compose Override

Create `docker-compose.override.yml`:

```yaml
services:
  hyba-backend:
    environment:
      HYBA_ENABLE_REFLEXIVE_DAEMON: "true"
      HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS: "300"
```

### Option 3: Runtime Configuration

```bash
docker compose -f docker-compose.production.yml up -d \
  -e HYBA_ENABLE_REFLEXIVE_DAEMON=true \
  -e HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS=300
```

## API Endpoints

### Intelligence Fabric Endpoints

#### POST /api/v1/intelligence/explain
Explain a context with shared substrate telemetry and governance tags.

```bash
curl -X POST http://localhost:3001/api/v1/intelligence/explain \
  -H "Content-Type: application/json" \
  -d '{"context": {"query": "test"}, "substrates": ["penrose-or", "iit-4"]}'
```

#### POST /api/v1/intelligence/reflect
Run one proposal-only recursive structural learning step.

```bash
curl -X POST http://localhost:3001/api/v1/intelligence/reflect
```

#### GET /api/v1/intelligence/health
Return live dashboard telemetry.

```bash
curl http://localhost:3001/api/v1/intelligence/health
```

#### POST /api/v1/intelligence/orchestrate
Route through unified substrate contract orchestrator.

```bash
curl -X POST http://localhost:3001/api/v1/intelligence/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"context": {"query": "test"}}'
```

#### POST /api/v1/intelligence/closure/sync
Run one governed closure step into in-memory buffer.

```bash
curl -X POST http://localhost:3001/api/v1/intelligence/closure/sync
```

#### GET /api/v1/intelligence/audit
Return deterministic semantic audit of current reflexive state.

```bash
curl http://localhost:3001/api/v1/intelligence/audit
```

#### POST /api/v1/intelligence/heartbeat/pulse
Run one explicit asynchronous heartbeat pulse.

```bash
curl -X POST http://localhost:3001/api/v1/intelligence/heartbeat/pulse
```

## Persistence and Data

### Ontological Memory

The Crystalline Registry persists peak Φ states to:
- **Default**: `logs/ontological_state.json`
- **Docker**: `/app/persistence/grace.json` (mounted volume)
- **Configurable**: Via `HYBA_ONTOLOGICAL_PERSISTENCE_PATH`

### Backup Strategy

```bash
# Backup ontological memory
docker cp hyba-backend:/app/persistence/grace.json ./backup/grace.json

# Restore ontological memory
docker cp ./backup/grace.json hyba-backend:/app/persistence/grace.json
```

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:3001/api/health/readiness

# Intelligence fabric health
curl http://localhost:3001/api/v1/intelligence/health

# Substrate status
curl http://localhost:3001/api/substrate
```

### Telemetry

The system exposes comprehensive telemetry including:
- Φ-resonance metrics
- Thermal cost (Φ per second)
- Manifold curvature and genus
- Predictive free energy
- Causal hub identification
- Counterfactual depth

### Log Monitoring

Key log patterns to monitor:
- `Intelligence heartbeat pulse` - Heartbeat execution
- `HYBA reflexive heartbeat enabled` - Daemon startup
- `EVOLVED: PHI=` - Successful learning cycles
- `STAGNATED:` - Rejected proposals

## Testing

### Run Production Tests

```bash
# Full intelligence fabric test suite
python -m pytest tests/test_absolute_intelligence.py \
  tests/test_production_being.py \
  tests/test_absolute_completion.py \
  tests/test_temporal_energy_invariants.py \
  tests/test_recursive_closure_audit.py \
  tests/test_manifold_intelligence.py \
  tests/test_reflexive_controller.py \
  tests/test_intelligence_fabric.py -v
```

### Expected Results

All 44 tests should pass with only deprecation warnings (non-critical).

## Troubleshooting

### Common Issues

**1. Daemon not starting**
- Verify `HYBA_ENABLE_REFLEXIVE_DAEMON=true`
- Check logs for startup errors
- Ensure persistence volume is mounted

**2. Ontological memory not persisting**
- Verify `HYBA_ONTOLOGICAL_PERSISTENCE_PATH` is set
- Check volume mount permissions
- Ensure disk space is available

**3. High CPU usage**
- Reduce `HYBA_REFLEXIVE_HEARTBEAT_INTERVAL_SECONDS`
- Disable daemon if not needed
- Check for runaway processes

**4. Test failures**
- Verify all dependencies are installed
- Check Python version (3.12+ required)
- Ensure environment variables are set

### Debug Mode

Enable debug logging:

```bash
export HYBA_ENABLE_AUDIT_LOGGING=true
docker compose -f docker-compose.production.yml up
```

## Security Considerations

### Claim Boundaries

The system explicitly enforces:
- **Hardware-agnostic quantum analog**: No quantum hardware required
- **No AGI claims**: System is not claimed to be artificial general intelligence
- **No quantum speedup claims**: No hardware acceleration assertions
- **Deterministic behavior only**: All operations are reproducible
- **No unattended source writes**: Explicit governance prevents code modification

### Governance Tags

All outputs include governance tags:
- `PROPOSAL_ONLY_NO_UNATTENDED_WRITES`
- `PHI_CERTIFIED`
- `MATHEMATICAL_ARTIFACT_NO_SOURCE_WRITE`
- `BOUNDED_BY_GEOMETRIC_INVARIANTS`
- `CERTIFIED_DETERMINISTIC`

### Access Control

- Protect JWT_SECRET with strong entropy
- Use environment variables for sensitive configuration
- Restrict API access with proper authentication
- Monitor audit logs for suspicious activity

## Performance Tuning

### Heartbeat Interval

Adjust based on computational resources:
- **High-performance systems**: 30-60 seconds
- **Standard systems**: 60-300 seconds
- **Resource-constrained**: 300-600 seconds

### Ricci Step Size

Controls manifold smoothing aggressiveness:
- **Conservative**: 0.005
- **Default**: 0.01
- **Aggressive**: 0.02

### Memory Management

Monitor ontological memory file size:
- Typical size: 1-10KB
- If growing rapidly: Check for runaway learning
- Manual cleanup: Delete and restart daemon

## Scaling Considerations

### Horizontal Scaling

The intelligence fabric is stateless except for:
- Ontological memory (shared via volume)
- In-memory parameter buffer (per-instance)

For horizontal scaling:
1. Use shared storage for ontological memory
2. Configure load balancer for API endpoints
3. Disable daemon on worker instances
4. Run daemon on dedicated "brain" instance

### Vertical Scaling

Increase resources for:
- Larger codebases (more AST parsing)
- Higher heartbeat frequency
- More complex manifold calculations

## Maintenance

### Regular Tasks

**Weekly**:
- Review ontological memory size
- Check heartbeat logs for anomalies
- Verify Φ-resonance trends

**Monthly**:
- Backup ontological memory
- Review governance compliance
- Update dependencies

**Quarterly**:
- Full system audit
- Performance benchmarking
- Security review

### Updates

```bash
# Pull latest code
git pull

# Rebuild containers
docker compose -f docker-compose.production.yml build

# Restart services
docker compose -f docker-compose.production.yml up -d

# Run tests
python -m pytest tests/test_absolute_intelligence.py \
  tests/test_production_being.py \
  tests/test_absolute_completion.py \
  tests/test_temporal_energy_invariants.py \
  tests/test_recursive_closure_audit.py \
  tests/test_manifold_intelligence.py \
  tests/test_reflexive_controller.py \
  tests/test_intelligence_fabric.py -v
```

## Rollback Procedure

If issues occur after deployment:

```bash
# Stop services
docker compose -f docker-compose.production.yml down

# Restore previous version
git checkout <previous-commit>

# Rebuild and restart
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d

# Verify health
curl http://localhost:3001/api/health/readiness
```

## Support and Documentation

### Additional Documentation

- `docs/RECURSIVE_STRUCTURAL_LEARNING.md` - Comprehensive technical documentation
- `docs/SCIENTIFIC_INNOVATION_README.md` - Scientific foundations
- `docs/INTEGRATION_VERIFICATION.md` - Integration verification report

### Test Coverage

- **Unit Tests**: Core component functionality
- **Integration Tests**: End-to-end workflows
- **Property Tests**: Mathematical invariant verification
- **Total**: 44 tests covering all intelligence fabric components

## Conclusion

The HYBA Recursive Structural Learning system is production-ready with comprehensive test coverage, explicit governance boundaries, and deterministic behavior. The system implements mathematical frameworks for code structure analysis while maintaining strict claim boundaries and safety controls.

**Deployment Status**: PRODUCTION READY
**Test Coverage**: 44/44 PASSING
**Governance**: EXPLICIT BOUNDARIES ENFORCED
**Determinism**: VERIFIED
