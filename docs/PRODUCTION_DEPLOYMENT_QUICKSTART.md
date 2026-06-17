# HYBA Production Deployment Quick Start

## Pre-Flight Checklist ✈️

### 1. Environment Setup

```bash
# Required secrets (minimum 16 characters each)
export JWT_SECRET="your-jwt-secret-min-32-chars-recommended"
export HYBA_OPERATOR_CREDENTIALS="your-operator-auth-credentials"
export POOL_PRIMARY_CREDENTIALS="your-pool-auth-credentials"

# Optional: Development mode (bypasses secret validation)
export HYBA_ALLOW_DEV_FIXTURES="true"  # NEVER use in production
```

### 2. Pool Configuration

Choose one of two methods:

**Method A: Environment Variables**
```bash
# ViaBTC Example
export HYBA_POOL_VIABTC_USERNAME="your_username"
export HYBA_POOL_VIABTC_PASSWORD="your_password"

# NiceHash Example
export HYBA_POOL_NICEHASH_WORKER="your_worker_name"
export HYBA_POOL_NICEHASH_NH_POOL_ID="your_nicehash_pool_id"
```

**Method B: Configuration File**
```bash
# Create mining_pools_config.json in python_backend/
{
  "pools": {
    "viabtc": {
      "username": "your_username",
      "password": "your_password",
      "enabled": true
    }
  }
}
```

### 3. Validate Configuration

```bash
cd /path/to/HYBA_FULLSTACK
python3 scripts/validate_production_hardening.py
```

Expected output:
```
🎯 ALL PRODUCTION HARDENING FIXES VALIDATED
   System ready for testnet deployment
```

---

## Starting the Miner

### Development Mode (Testing)

```bash
export HYBA_ALLOW_DEV_FIXTURES="true"
python3 -m pythia_mining.run_unified_miner
```

### Production Mode

```bash
# Ensure all secrets are configured
python3 -m pythia_mining.run_unified_miner
```

---

## Monitoring & Health Checks

### Log Locations

- **Audit Logs**: `logs/audit/audit_YYYYMMDD.log`
- **Metrics Database**: `data/metrics.db`
- **Pool Configs**: `python_backend/mining_pools_config.json` (0600 permissions)

### Key Metrics to Monitor

1. **Boundary Proximity (ε)**
   - Safe range: ε > 0.01
   - Warning: ε < 0.001
   - Critical: ε < 0.00001

2. **Security Status**
   - `SEC_SECURE`: Production ready ✅
   - `DEV_PASS`: Development mode ⚠️
   - `SEC_FAIL`: Blocked 🛑

3. **Pool Status**
   - Connection attempts
   - Share acceptance rate
   - Average latency

---

## Troubleshooting

### Issue: "SEC_FAIL: Missing or insecure configuration secrets"

**Solution**: Ensure all required environment variables are set with minimum 16 characters:
```bash
echo $JWT_SECRET  # Should output your secret
echo $HYBA_OPERATOR_CREDENTIALS
echo $POOL_PRIMARY_CREDENTIALS
```

### Issue: "No verified stratum pool profiles available"

**Solution**: Configure at least one pool via environment variables or config file:
```bash
export HYBA_POOL_VIABTC_USERNAME="your_username"
export HYBA_POOL_VIABTC_PASSWORD="your_password"
```

### Issue: "Adversarial boundary convergence detected"

**Solution**: This is informational. The system is detecting parameter proposals approaching limits. Monitor logs to ensure ε doesn't remain < 10⁻⁵ continuously.

---

## Production Safety Features

### Automatic Fail-Closed Behavior

The system will automatically halt and refuse to start if:
- Critical secrets are missing or < 16 characters
- Secrets start with "PLACEHOLDER_"
- No pool profiles are configured
- Development fixtures are used in production mode

### Five Quantum Safety Constraints

All reflexive self-analysis proposals must satisfy (note: the controller operates in proposal-only mode and never applies changes to source code or runtime parameters without explicit operator authorization):
1. **Hermiticity**: Density matrix remains Hermitian
2. **PSD**: All eigenvalues non-negative
3. **Natural Scaling**: φ-resonant scaling laws enforced
4. **Energy Conservation**: Power limits respected
5. **Information Integrity**: Compression ratio ≤ 2.0 (hard cap)

### Multi-Pool Failover

Pools are prioritized by the `priority` field (lower = higher priority):
- ViaBTC: priority 10
- Braiins: priority 20
- CKPool: priority 30
- NiceHash: priority 40

---

## Commands Reference

```bash
# Validate production hardening
python3 scripts/validate_production_hardening.py

# Run unified miner (production)
python3 -m pythia_mining.run_unified_miner

# Run test suite
cd python_backend
pytest tests/

# Check pool configuration
python3 -c "from pythia_mining.pool_profiles import load_pool_profiles; print(load_pool_profiles())"
```

---

## Contact & Support

For production deployment issues, consult:
- [Production Hardening Audit Report](PRODUCTION_HARDENING_AUDIT_REPORT.md)
- [Technical Specification](TECHNICAL_SPECIFICATION.md)
- [HYBA Mining Doctrine](HYBA_MINING_DOCTRINE.md)

---

*Last Updated: 2024 — HYBA Production Hardening Release*
