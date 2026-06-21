# HYBA Internal Mining Operations - Quick Start Guide

## Purpose
Internal substrate validation for CIaaS/QaaS commercial offerings using φ-resonance mathematical primitives.

**Commercial Products:**
- Quantum-as-a-Service (QaaS)
- Computational Intelligence as a Service (CIaaS)

**Mining Role:** Internal validation only, not a customer-facing product

## Prerequisites
- Python 3.12+
- Virtual environment activated
- ViaBTC pool credentials: PYTHIA.001 / 123

## Quick Start

### Terminal 1: Start Backend
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Activate virtual environment
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Start API server
PYTHONPATH=python_backend python -m uvicorn hyba_genesis_api.main:app --host 127.0.0.1 --port 3001
```

Wait for: `Application startup complete`

### Terminal 2: Start Mining Operations
```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK

# Run comprehensive startup script
python scripts/start_internal_mining_ops.py
```

This will:
1. ✓ Check backend availability
2. ✓ Configure ViaBTC pool (PYTHIA.001)
3. ✓ Connect to pool
4. ✓ Start mining daemon
5. ✓ Verify mining status
6. ✓ Show operational summary

## Alternative: Quick ViaBTC Start
```bash
python scripts/start_viabtc_mining.py
```

## Monitoring

### API Endpoints
```bash
# Mining status
curl http://127.0.0.1:3001/api/mining/status

# Pool metrics
curl http://127.0.0.1:3001/api/mining/pools

# Statistics
curl http://127.0.0.1:3001/api/mining/stats

# Health check
curl http://127.0.0.1:3001/api/mining/health
```

### Log Files
- Backend: Terminal running uvicorn
- Audit logs: `logs/audit/audit_*.log`
- Mining sessions: `python_backend/artifacts/mining_sessions/`

## Expected Output

```
HYBA CIAAS/QAAS INTERNAL MINING OPERATIONS
================================================================================

COMMERCIAL OFFERING: Quantum-as-a-Service (QaaS) & Computational Intelligence
MINING ROLE:         Internal substrate validation only

Mathematical Stack:
  - φ-resonance primitives (golden ratio computational structures)
  - PULVINI memory compression (2.0x lossless boundary)
  - HENDRIX-Φ solver (structured nonce traversal)
  - IIT 4.0 Φ computation (coherence diagnostics)
  - Yang-Mills mass gap (anti-simulation shield)

Pool: ViaBTC (PYTHIA.001)
Purpose: Validate mathematical substrate for CIaaS/QaaS customers
================================================================================

[1/6] Checking backend availability...
  ✓ Backend is running

[2/6] Configuring ViaBTC pool...
  ✓ ViaBTC pool already configured
    Username: PYTHIA.001
    Worker: hendrix_phi

[3/6] Connecting to ViaBTC pool...
  ✓ Connected to ViaBTC BTC
    Worker: PYTHIA.001
    Capacity: 1.0 EH/s
    Cap: 1.0 EH/s (PULVINI boundary)

[4/6] Starting mining daemon...
  ✓ Mining daemon started
    PID: <process_id>

[5/6] Verifying mining status...
  Status: running
  Daemon: running
  Pool: viabtc
  Hashrate: 1.0 EH/s
  ✓ Mining operational

[6/6] Operational Summary
--------------------------------------------------------------------------------
Active Pool:      viabtc
Total Hashrate:   1.0 EH/s
Hashrate Cap:     1.0 EH/s (PULVINI)
Shares (24h):     0
Acceptance Rate:  0.0%
Daemon Running:   True
MIDAS State:      running

Purpose:
  This mining infrastructure validates φ-resonance mathematical primitives
  that power HYBA's commercial CIaaS/QaaS offerings.

Commercial Services:
  - Quantum-as-a-Service (QaaS): Fault-tolerant quantum compute
  - Computational Intelligence (CIaaS): Optimization & solver services

Mining is internal validation only, not a customer-facing product.
--------------------------------------------------------------------------------
```

## Troubleshooting

### Backend Not Responding
```bash
# Check if port 3001 is in use
lsof -i :3001

# Kill existing process
kill -9 <PID>

# Restart backend
PYTHONPATH=python_backend python -m uvicorn hyba_genesis_api.main:app --host 127.0.0.1 --port 3001
```

### Pool Connection Failed
```bash
# Verify pool configuration
curl http://127.0.0.1:3001/api/mining/pool-config

# Reconfigure if needed
python scripts/start_internal_mining_ops.py
```

### Redis Connection Issues
Redis is optional. Backend automatically falls back to in-memory mode if Redis is unavailable.

To use Redis (optional):
```bash
# Install and start Redis
brew install redis  # macOS
redis-server
```

### Daemon Not Starting
Check:
1. Python path is correct
2. Virtual environment is activated
3. All dependencies installed: `pip install -r python_backend/requirements.txt`
4. No conflicting Python processes

## Configuration Files

- Pool config: `config/mining_pools_live.json`
- Runtime state: `python_backend/pythia_state.json`
- Mining config: `python_backend/mining_config.json`

## MIDAS State Machine

The mining controller follows strict state transitions:

```
IDLE → STARTING → RUNNING → STOPPING → STOPPED
         ↓            ↓
      [error]      PAUSED
```

States:
- **IDLE**: No pool connection
- **STARTING**: Connecting to pool
- **RUNNING**: Active mining
- **PAUSED**: Connected but not hashing
- **STOPPING**: Disconnecting
- **STOPPED**: Clean shutdown

## Safety Constraints

1. **Hashrate Cap**: 1.0 EH/s (PULVINI boundary)
2. **Rate Limiting**: 10 requests/second per endpoint
3. **Backpressure**: Max 100 concurrent operations
4. **Idempotency**: All state-changing operations are idempotent
5. **Circuit Breaker**: Automatic failover after 5 heal attempts

## Next Steps

1. Monitor share submissions in audit logs
2. Verify φ-resonance metrics in `/api/mining/stats`
3. Track acceptance rate in pool metrics
4. Use mining validation for CIaaS/QaaS substrate testing

## Support

For issues:
1. Check backend logs (Terminal 1)
2. Review `/api/mining/health` endpoint
3. Verify MIDAS state in `/api/mining/status`
4. Consult `docs/MINING_OPERATIONS.md` for detailed documentation

---

**Version**: 4.0-Prime  
**Status**: Production-ready internal infrastructure  
**Commercial Focus**: CIaaS/QaaS substrate validation  
**Last Updated**: 2026-06-20
