# 🚀 HYBA Quick Start: Production Deployment

**Last Updated:** June 20, 2026  
**Target Audience:** Operators, DevOps Engineers  
**Time to Deploy:** 5 minutes

---

## Prerequisites

- Python 3.12+
- Bitcoin mining pool account (ViaBTC, Braiins, etc.)
- Linux/macOS system with 4GB+ RAM

---

## Step 1: Environment Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/hybaanalytics1/HYBA_FULLSTACK.git
cd HYBA_FULLSTACK

# Generate secure mining environment
python3 scripts/create_mining_env.py \
  --viabtc-user YOUR_WORKER_NAME \
  --viabtc-password YOUR_POOL_PASSWORD

# Output:
# ✅ Generated .env.mining.local
# ✅ JWT_SECRET: wX7k... (32 bytes)
# ✅ HEALTH_TOKEN: pQ9m... (32 bytes)
# ✅ OPERATOR_CREDS: operator:rT8n... (16 bytes)
# ✅ File permissions: 0600

# Validate configuration
python3 scripts/validate_production_env.py
# ✅ All secrets valid
```

---

## Step 2: Test Suite Validation (3 minutes)

```bash
# Run comprehensive test suite
./scripts/run_comprehensive_test_suite.sh

# Expected output:
# ✅ Core tests: 104/104 PASS
# ✅ Operational tests: PASS
# ⚠️  Extended tests: See output
# ========================================
# ✅ COMPREHENSIVE TEST SUITE COMPLETE
# ========================================
```

---

## Step 3: Deploy Supervised Mode (immediate)

```bash
# Start supervised production mining
HYBA_AUTONOMY_LEVEL=supervised \
HYBA_OPERATOR_APPROVAL_REQUIRED=true \
HYBA_ENV=production \
python3 scripts/start_live_mining_to_braiins.py

# Expected output:
# ✅ Autonomous controller initialized
# ✅ Connected to pool: stratum+tcp://...
# ✅ Subscribed to pool: subscribe_id=...
# ✅ Authorized: worker=PYTHIA.001
# ⏳ Waiting for mining.notify...
# ✅ Job received: job_id=...
# 🔄 Mining search started...
```

---

## Monitoring Dashboards

### **Prometheus Metrics**
```bash
# Metrics endpoint (scrape every 15s)
curl http://localhost:8000/metrics

# Key metrics:
# - hyba_phi_density (target: ≥0.70)
# - hyba_consecutive_failures (target: 0)
# - hyba_autonomous_circuit_open (target: 0)
# - hyba_constraint_violations_total (target: 0)
```

### **Health Check**
```bash
# System health
curl http://localhost:8000/health

# Expected:
# {"status": "healthy", "autonomy_level": "supervised"}
```

### **Autonomy Status**
```bash
# Real-time autonomy metrics
curl http://localhost:8000/api/autonomy/status

# Returns:
# {
#   "autonomy_level": "supervised",
#   "phi_density": 0.984,
#   "consecutive_failures": 0,
#   "circuit_open": false,
#   "proposals_applied": 5,
#   "reflexive_cycles": 202
# }
```

---

## Operational Procedures

### **Hour 1 Checkpoint**

```bash
# Check system health
curl http://localhost:8000/api/autonomy/status | jq '.'

# Verify:
# ✅ phi_density ≥ 0.70
# ✅ circuit_open == false
# ✅ consecutive_failures == 0

# Check pool responses
curl http://localhost:8000/api/mining/status | jq '.pool_responses[-10:]'

# Verify pool connectivity and responses
```

### **Hour 3 Checkpoint**

```bash
# Check proposal acceptance rate
curl http://localhost:8000/api/autonomy/metrics | jq '.proposal_acceptance_rate'

# Target: ≥0.80 (80% of proposals accepted)

# Check target evidence
curl http://localhost:8000/api/autonomy/target-evidence | jq '.'

# Verify Thompson posteriors converging
```

### **Hour 6 Checkpoint**

```bash
# Export 6-hour evidence snapshot
python3 scripts/export_evidence_snapshot.py \
  --duration-hours 6 \
  --output artifacts/evidence_6hr.json

# Review snapshot
cat artifacts/evidence_6hr.json | jq '.summary'

# Verify:
# - Zero circuit trips
# - Phi density sustained ≥0.70
# - Pool responses accumulating
```

---

## Troubleshooting

### **Problem: Circuit Breaker Opens**

```bash
# Check reason
curl http://localhost:8000/api/autonomy/status | jq '.circuit_breaker'

# Manual reset (if safe)
curl -X POST http://localhost:8000/api/autonomy/circuit/reset \
  -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  -d '{"operator_id": "ops_team", "reason": "manual_inspection_complete"}'
```

### **Problem: Low Phi Density (<0.70)**

```bash
# Check component health
curl http://localhost:8000/api/consciousness/status | jq '.regime'

# If regime == "FRAGMENTED":
# - System will automatically enter conservative mode (120s timeout)
# - No action needed, monitor for recovery

# If sustained >30 min:
# - Check logs for errors
# - Verify pool connectivity
# - Consider restart
```

### **Problem: High Consecutive Failures**

```bash
# Check failure reasons
curl http://localhost:8000/api/autonomy/audit-log | jq '.[-10:] | .[] | select(.event_type == "failure")'

# Common causes:
# - Pool connectivity issues → check network
# - Constraint violations → review proposals
# - Resource exhaustion → check CPU/memory
```

---

## Promote to Unattended Autonomous Mode

### **Prerequisites** (After 24 Hours Supervised)

```bash
# 1. Verify 24-hour evidence pack exists
ls -lh artifacts/supervised_24hr_evidence_pack.json

# 2. Verify testnet validation complete
ls -lh artifacts/testnet_validation_latest.json

# 3. Check readiness gate
python3 -c "
from pythia_mining.autonomous_mining_controller import AutonomousMiningController
ctrl = AutonomousMiningController(None)
status = ctrl._supervised_production_ready()
print('Unattended ready:', status['unattended_mode_ready'])
"

# Expected: True
```

### **Deploy Unattended Mode**

```bash
# Promote to unattended autonomous
HYBA_AUTONOMY_LEVEL=autonomous \
HYBA_OPERATOR_APPROVAL_REQUIRED=false \
HYBA_ENV=production \
python3 scripts/start_live_mining_to_braiins.py

# ⚠️  WARNING: This mode requires no operator approval
# ⚠️  Only deploy after 24hr supervised evidence validated
```

---

## Emergency Procedures

### **Emergency Shutdown**

```bash
# Graceful shutdown
curl -X POST http://localhost:8000/api/autonomy/emergency-shutdown \
  -H "Authorization: Bearer ${OPERATOR_TOKEN}" \
  -d '{"operator_id": "ops_team", "reason": "emergency_maintenance"}'

# Or kill process
pkill -SIGTERM -f "start_live_mining"

# Verify state saved
ls -lh artifacts/autonomous_mining/reflexive_state.json
```

### **Rollback to Previous State**

```bash
# List available backups
ls -lt artifacts/autonomous_mining/backups/

# Rollback to specific backup
python3 scripts/autonomous_mining_rollback.py \
  --backup artifacts/autonomous_mining/backups/reflexive_state_NNNN.json \
  --operator-id ops_team \
  --reason "rollback_after_incident"

# Dry-run first (recommended)
python3 scripts/autonomous_mining_rollback.py --dry-run --backup ...
```

---

## Performance Benchmarks

### **Expected Performance**

| Metric | Target | Typical | Concern If |
|--------|--------|---------|------------|
| **Phi Density** | ≥0.70 | 0.85-0.98 | <0.50 for >1hr |
| **Circuit Breaker Trips** | 0 | 0 | >1 per 24hr |
| **Proposal Acceptance** | ≥80% | 95-100% | <70% sustained |
| **Pool Response Rate** | ≥90% | 98-99% | <80% (check network) |
| **Reflexive Cycle Time** | <5s | 0.4-0.5ms | >10s |
| **Metrics Generation** | <100ms | <1ms | >500ms |

---

## Documentation Links

- **Comprehensive Test Strategy:** `docs/COMPREHENSIVE_TEST_STRATEGY.md`
- **Capabilities Manifest:** `docs/HYBA_CAPABILITIES_MANIFEST.md`
- **Technology Pivot Playbook:** `docs/TECHNOLOGY_PIVOT_PLAYBOOK.md`
- **Production Certification:** `PRODUCTION_READY_CERTIFICATION.md`
- **Supervised Evidence Gate:** `docs/PYTHIA_SUPERVISED_PRODUCTION_EVIDENCE_GATE.md`

---

## Support

### **Community**
- GitHub Issues: `https://github.com/hybaanalytics1/HYBA_FULLSTACK/issues`
- Discord: `[Coming Soon]`

### **Enterprise Support**
- Email: `support@hyba.ai` [Coming Soon]
- SLA: 24/7 for production incidents

---

**Quick Start Complete! Your system is now mining autonomously in supervised mode.** 🎉

**Next Steps:**
1. Monitor for 24 hours
2. Collect evidence pack
3. Promote to unattended autonomous mode

**Questions?** Check `docs/` folder for comprehensive documentation.
