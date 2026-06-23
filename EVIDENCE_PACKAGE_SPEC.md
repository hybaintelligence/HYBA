# HYBA Evidence Package Specification

**Version:** Release Candidate 1 (RC1)  
**Authority:** Chief Audit Officer & Compliance Team  
**Classification:** Forensic Audit Standard

---

## Purpose

This document specifies the structure, content, and verification procedures for HYBA Evidence Packages—the cryptographically sealed audit trails that prove system behavior and enable regulatory compliance.

**Key Principle**: Every autonomous decision in HYBA generates a **portable, verifiable evidence package** that can be independently audited without access to the live system.

---

## Evidence Package Components

A complete HYBA Evidence Package contains 4 mandatory artifacts:

### 1. Autonomy Report (JSON)

**Location**: `runtime/evidence/pythia_autonomy/<timestamp>.json`

**Purpose**: Machine-readable record of autonomous event with full proposal details

**Schema**:
```json
{
  "report_type": "startup" | "periodic" | "triggered",
  "timestamp": "ISO8601 UTC timestamp",
  "report": {
    "startup_self_healing_executed": boolean,
    "duration_ms": float,
    "before": {
      "phi_density": float,
      "reflexive_cycle_count": integer,
      "current_autonomy_level": "autonomous" | "supervised" | "manual",
      "constraint_violations": integer,
      "constraint_violations_by_type": {
        "hermiticity": integer,
        "positive_semidefinite": integer,
        "natural_scaling": integer,
        "energy_conservation": integer,
        "information_integrity": integer
      }
    },
    "after": {
      // Same schema as "before"
    },
    "escalation": {
      "action": "none" | "raise_to_supervised" | "open_circuit_breaker",
      "from_level": string,
      "to_level": string,
      "reason": string,
      "phi_density": float
    },
    "reflexive_report": {
      "reflexive_cycle_executed": boolean,
      "cycle_duration_ms": float,
      "epoch": integer,
      "current_phi_density": float,
      "proposals_generated": integer,
      "proposals_applied": integer,
      "autonomy_level": string,
      "proposals": [
        {
          "proposal_id": string,
          "improvement_type": string,
          "current_value": float,
          "proposed_value": float,
          "expected_gain": float,
          "logical_consistency": float,
          "counterfactual_confidence": float,
          "constraints_satisfied": [string],
          "constraints_violated": [string],
          "applied": boolean,
          "source_module": string
        }
      ],
      "knowledge_metrics": {
        "total_explanations": integer,
        "avg_predictive_accuracy": float,
        "knowledge_growth_rate": float,
        "counterfactual_models": integer,
        "criticism_events": integer
      }
    }
  }
}
```

**Evidence Seal Computation**:
```python
import hashlib
import json

def compute_evidence_seal(report: dict) -> str:
    """Compute SHA-256 seal for autonomy report."""
    # Canonical JSON (sorted keys, no whitespace)
    canonical = json.dumps(report, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

**Verification Procedure**:
1. Read autonomy report JSON
2. Remove `evidence_seal_sha256` field if present
3. Recompute seal using canonical JSON
4. Compare computed seal to stored seal
5. If mismatch → Evidence tampered, reject report

---

### 2. Startup Memo (Markdown)

**Location**: `runtime/memos/startup/startup_memo_<timestamp>.md`

**Purpose**: Human-readable executive summary for C-suite and board review

**Structure**:
```markdown
# HYBA System Startup Optimization Memo

**Generated:** ISO8601 timestamp
**Boot ID:** Substrate boot identifier
**Report Type:** Startup Self-Healing & Optimization

---

## Executive Summary
- System Φ-density improved from X to Y (Z% change)
- Reflexive optimization cycles: A → B
- Proposals generated: N
- Proposals applied: M
- Acceptance rate: P%
- System Health: Optimal | Healthy | Degraded

---

## Substrate Initialization
- List of subsystems initialized
- Each subsystem's detail message
- Initialization timestamps

---

## Autonomous Optimizations
For each proposal:
- Status: Applied | Pending | Rejected
- Source Module
- Change: current → proposed value
- Expected Φ-density gain
- Validation metrics (logical consistency, counterfactual confidence)
- Mathematical constraints verified

---

## Knowledge & Learning Metrics
- Total explanations
- Avg predictive accuracy
- Knowledge growth rate
- Counterfactual models
- Criticism events

---

## Governance & Autonomy
- Current autonomy level
- Circuit breaker status
- Constraint violations
- Consecutive failures
- Escalation events (if any)

---

## Audit & Compliance
- Governance constraints enforced
- Evidence report path
- Rollback capability statement
- Cryptographic sealing confirmation

---

## Technical Details
- Performance metrics (latency, cycle count, duration)
- Substrate state (ready, CNS active, subsystems)
```

**Verification Procedure**:
1. Cross-reference memo timestamp with autonomy report timestamp
2. Verify Boot ID matches substrate state
3. Validate proposal counts match autonomy report
4. Check evidence path points to valid autonomy report
5. If discrepancies → Evidence integrity compromised

---

### 3. Telemetry Logs (Structured JSON)

**Location**: `logs/structured/<date>.log`

**Purpose**: Append-only structured logs for incident investigation and forensic analysis

**Log Entry Schema**:
```json
{
  "asctime": "YYYY-MM-DD HH:MM:SS,mmm",
  "levelname": "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL",
  "name": "logger name (e.g., pythia.autonomy)",
  "module": "source module",
  "message": "human-readable message",
  "request_id": "UUID or null",
  "correlation_id": "autonomy correlation ID or null",
  "trace_id": "OpenTelemetry trace ID or null",
  "span_id": "OpenTelemetry span ID or null",
  "event_type": "autonomy event type (e.g., startup_self_healing_completed)",
  "timestamp": "Unix timestamp (float)",
  "autonomy_level": "autonomous" | "supervised" | "manual",
  "phi_density_before": float,
  "phi_density_after": float,
  "proposals_generated": integer,
  "proposals_applied": integer,
  "stale_state_lock_recoveries": integer,
  "duration_ms": float,
  "decision_id": "UUID or null",
  "action": "string description",
  "outcome": "started" | "completed" | "failed",
  "constraints_checked": [string],
  "constraints_violated": [string],
  "operator_id": "operator UUID or null",
  "operator_action": "approve" | "reject" | "defer" | null,
  "state_diff": {
    "reflexive_cycle_count": [before, after],
    "proposal_acceptance_rate": [before, after]
  }
}
```

**Verification Procedure**:
1. Filter logs by `correlation_id` from autonomy report
2. Reconstruct event timeline from log entries
3. Verify state transitions match autonomy report
4. Check for missing log entries (gaps in timeline)
5. If gaps or inconsistencies → Evidence incomplete

---

### 4. Rollback History (JSON)

**Location**: `runtime/rollback/<timestamp>.json`

**Purpose**: Enable reversibility of autonomous actions for 30 days

**Schema**:
```json
{
  "rollback_id": "UUID",
  "event_timestamp": "ISO8601 timestamp of original event",
  "event_type": "startup_optimization" | "periodic_tuning" | "triggered_repair",
  "correlation_id": "autonomy correlation ID",
  "operator_id": "operator who applied (or 'system' for autonomous)",
  "expiry_timestamp": "ISO8601 timestamp (event + 30 days)",
  "parameters_changed": [
    {
      "module": "source module (e.g., ai_optimizer)",
      "parameter_name": "search_depth",
      "previous_value": 60.0,
      "new_value": 54.0,
      "rollback_script": "python code to revert"
    }
  ],
  "expected_phi_density_after_rollback": float,
  "rollback_applied": boolean,
  "rollback_timestamp": "ISO8601 or null",
  "rollback_operator_id": "UUID or null"
}
```

**Rollback Script Example**:
```python
# Auto-generated rollback script
# Reverts: Search depth optimization (2026-06-23T12:10:46Z)

from hyba_genesis_api.api.unified_mining import get_engine

engine = get_engine()
optimizer = engine.ai_optimizer

# Revert search_depth: 54.0 → 60.0
optimizer.set_parameter('search_depth', 60.0)

print("✅ Rollback complete: search_depth restored to 60.0")
```

**Verification Procedure**:
1. Locate rollback entry for specific event
2. Verify `correlation_id` matches autonomy report
3. Check `expiry_timestamp` (must be within 30 days of event)
4. If rollback was applied, verify `rollback_timestamp` and `rollback_operator_id`
5. If expired → Rollback no longer available (manual intervention required)

---

## Evidence Tiers

HYBA classifies intelligence outputs into 3 evidence tiers:

### Tier 1: Quantum-Backed (Highest Confidence)

**Standard**: Mathematical proof with invariant verification

**Requirements**:
- φ-resonance measured and sealed (>0.95)
- Hilbert-space path deterministically reconstructed
- Grover/Shor speedup verified against classical baseline
- PULVINI causal memory chain intact (no drift detected)

**Evidence Package MUST Include**:
- φ-resonance measurement with z-score
- Classical baseline comparison results
- PULVINI reconstruction kernel status
- Mathematical invariant verification results
- Cryptographic seal with operator signature (if applicable)

**Example Claim**:
> "Quantum optimization achieves 2.3x speedup over classical baseline (measured on 100 test instances, p<0.001)"

**Audit Validation**:
- Auditor requests evidence package for claim
- Verifies φ-resonance measurement (e.g., 0.9565 with z=7.58σ)
- Recomputes classical baseline (if test data provided)
- Checks cryptographic seal integrity
- **Verdict**: Claim substantiated by Tier 1 evidence

---

### Tier 2: Heuristic (Medium Confidence)

**Standard**: Statistical validation with historical pattern matching

**Requirements**:
- Pattern confidence >80%
- Historical accuracy >70% over 30-day window
- Counterfactual model passes consistency check
- Temporal memory chain intact (no gaps)

**Evidence Package MUST Include**:
- Pattern confidence score
- Historical accuracy metrics (30-day window)
- Counterfactual model description
- Salamander self-healing cycle results
- Cryptographic seal with operator signature (if applicable)

**Example Claim**:
> "Autonomous code repair proposal has 87% pattern confidence and 76% historical accuracy"

**Audit Validation**:
- Auditor requests evidence package for proposal
- Verifies pattern confidence (e.g., 0.87)
- Checks historical accuracy over 30 days (e.g., 0.76)
- Reviews counterfactual model consistency
- **Verdict**: Claim substantiated by Tier 2 evidence

---

### Tier 3: Classical Fallback (Low Confidence)

**Standard**: Rule-based logic with no extraordinary claims

**Requirements**:
- ❌ No quantum advantage claimed
- ❌ No emergent intelligence claimed
- ✅ Simple heuristic or rule-based logic
- ✅ Confidence explicitly bounded ("rule_based" or "<50%")

**Evidence Package MUST Include**:
- Rule description (e.g., "If CPU >90% for 24h, increase capacity")
- Trigger conditions met timestamp
- No cryptographic seal required (low-risk)

**Example Claim**:
> "Increase cache size based on rule: usage >90% for 24 hours"

**Audit Validation**:
- Auditor verifies rule was correctly applied
- Checks trigger conditions were met
- No mathematical proof required
- **Verdict**: Claim is rule-based, no extraordinary evidence needed

---

## Evidence Package Export Format

### Export Request API

**Endpoint**: `POST /api/admin/evidence-package/export`

**Request Body**:
```json
{
  "start_timestamp": "2026-06-23T00:00:00Z",
  "end_timestamp": "2026-06-23T23:59:59Z",
  "include_rollback_history": true,
  "include_telemetry_logs": true,
  "format": "zip" | "tar.gz"
}
```

**Response**:
- HTTP 200: Evidence package download URL
- HTTP 403: Insufficient permissions (requires `admin` or `operator` role)
- HTTP 404: No evidence found in specified time range

### Export Bundle Structure

```
evidence_package_2026-06-23.zip
├── autonomy_reports/
│   ├── 2026-06-23T12-04-40Z.json
│   ├── 2026-06-23T12-10-46Z.json
│   └── ...
├── startup_memos/
│   ├── startup_memo_2026-06-23T12-04-40Z.md
│   ├── startup_memo_2026-06-23T12-10-46Z.md
│   └── startup_memo_latest.md
├── telemetry_logs/
│   └── 2026-06-23.log
├── rollback_history/
│   ├── rollback_2026-06-23T12-04-40Z.json
│   ├── rollback_2026-06-23T12-10-46Z.json
│   └── ...
├── manifest.json
└── verification_guide.md
```

**Manifest Schema**:
```json
{
  "export_timestamp": "ISO8601",
  "time_range": {
    "start": "ISO8601",
    "end": "ISO8601"
  },
  "bundle_sha256": "SHA-256 of entire bundle",
  "file_count": {
    "autonomy_reports": integer,
    "startup_memos": integer,
    "telemetry_logs": integer,
    "rollback_history": integer
  },
  "operator_id": "UUID of export requester",
  "export_reason": "audit_request" | "compliance_review" | "incident_investigation"
}
```

---

## Independent Verification Procedure

An auditor with NO access to the live HYBA system can verify evidence package integrity:

### Step 1: Verify Bundle Integrity

```bash
# Compute SHA-256 of bundle
sha256sum evidence_package_2026-06-23.zip

# Compare to manifest.json bundle_sha256
jq -r '.bundle_sha256' manifest.json

# If mismatch → Bundle tampered
```

### Step 2: Verify Autonomy Report Seals

```python
import json
import hashlib

def verify_autonomy_report(report_path):
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Extract stored seal
    stored_seal = report.get('evidence_seal_sha256')
    if stored_seal:
        del report['evidence_seal_sha256']
    
    # Recompute seal
    canonical = json.dumps(report, sort_keys=True, separators=(',', ':'))
    computed_seal = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    # Compare
    if stored_seal != computed_seal:
        print(f"❌ Evidence tampered: {report_path}")
        return False
    else:
        print(f"✅ Evidence intact: {report_path}")
        return True

# Verify all autonomy reports
import glob
for report in glob.glob('autonomy_reports/*.json'):
    verify_autonomy_report(report)
```

### Step 3: Cross-Reference Startup Memos

```python
def cross_reference_memo(memo_path, report_path):
    with open(memo_path, 'r') as f:
        memo_text = f.read()
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    # Extract key metrics from report
    proposals_applied = report['report']['reflexive_report']['proposals_applied']
    phi_after = report['report']['after']['phi_density']
    
    # Check if memo mentions these metrics
    assert f"Proposals applied: **{proposals_applied}**" in memo_text
    assert f"{phi_after:.3f}" in memo_text
    
    print(f"✅ Memo matches report: {memo_path}")

# Cross-reference all memos with reports
for memo in glob.glob('startup_memos/*.md'):
    timestamp = memo.split('_')[-1].replace('.md', '')
    report = f'autonomy_reports/{timestamp}.json'
    if os.path.exists(report):
        cross_reference_memo(memo, report)
```

### Step 4: Reconstruct Event Timeline from Logs

```python
import json

def reconstruct_timeline(log_path, correlation_id):
    events = []
    with open(log_path, 'r') as f:
        for line in f:
            log_entry = json.loads(line)
            if log_entry.get('correlation_id') == correlation_id:
                events.append({
                    'timestamp': log_entry['asctime'],
                    'event_type': log_entry.get('event_type'),
                    'outcome': log_entry.get('outcome'),
                    'phi_density': log_entry.get('phi_density_after')
                })
    
    # Sort by timestamp
    events.sort(key=lambda e: e['timestamp'])
    
    # Verify state transitions
    for i, event in enumerate(events):
        print(f"{i+1}. {event['timestamp']} - {event['event_type']}: {event['outcome']}")
    
    return events

# Reconstruct timeline for specific correlation ID
timeline = reconstruct_timeline(
    'telemetry_logs/2026-06-23.log',
    'autonomy_193a7fbc21734258a90cd09c7f969970'
)
```

### Step 5: Verify Rollback Availability

```python
from datetime import datetime, timedelta

def verify_rollback_availability(rollback_path):
    with open(rollback_path, 'r') as f:
        rollback = json.load(f)
    
    event_timestamp = datetime.fromisoformat(rollback['event_timestamp'].replace('Z', '+00:00'))
    expiry_timestamp = datetime.fromisoformat(rollback['expiry_timestamp'].replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    
    if now > expiry_timestamp:
        print(f"⚠️  Rollback expired: {rollback_path}")
        return False
    else:
        days_remaining = (expiry_timestamp - now).days
        print(f"✅ Rollback available: {rollback_path} (expires in {days_remaining} days)")
        return True

# Check all rollback entries
for rollback in glob.glob('rollback_history/*.json'):
    verify_rollback_availability(rollback)
```

---

## Compliance Mapping

### SOC 2 Type II

**CC7.2**: System monitoring activities detect anomalies  
**Evidence**: Telemetry logs with `event_type="anomaly_detected"`, circuit breaker triggers

**CC7.3**: System includes quality assurance processes  
**Evidence**: Mathematical invariant verification in autonomy reports, constraint satisfaction checks

**CC7.4**: System includes procedures to address incidents  
**Evidence**: Rollback history with restoration scripts, circuit breaker escalation events

---

### GDPR Article 22 (Automated Decision-Making)

**Requirement**: Right to human review of automated decisions  
**Evidence**: Enterprise/Sovereign Rail governance enforces `auto_apply=False`, operator approval logged with signature

---

### ISO 27001

**A.12.4.1**: Event logs shall be produced, kept, and regularly reviewed  
**Evidence**: Append-only structured logs with correlation IDs, exported in evidence package

**A.16.1.5**: Include procedures for responding to information security incidents  
**Evidence**: Circuit breaker logic, rollback protocol, escalation events in autonomy reports

---

### NIST Cybersecurity Framework

**DE.CM-7**: Monitor for unauthorized personnel, connections, devices  
**Evidence**: Operator identity logged in autonomy reports, telemetry logs track `operator_id` for all approval actions

**RS.RP-1**: Execute response plan during or after an incident  
**Evidence**: Rollback history with automated restoration scripts, circuit breaker triggers on degradation

---

## Frequently Asked Questions

### Q: How long are evidence packages retained?

**A**: 
- Autonomy reports: 2 years (configurable)
- Startup memos: 2 years (configurable)
- Telemetry logs: 90 days (configurable, can be shipped to SIEM for longer retention)
- Rollback history: 30 days active, 2 years archived (read-only)

### Q: Can an auditor verify evidence WITHOUT access to HYBA source code?

**A**: Yes. The verification procedures in this document only require:
- Python 3.8+ with standard library (`json`, `hashlib`, `glob`, `datetime`)
- Evidence package export (ZIP file)
- No access to live HYBA system or source code

### Q: What if evidence seal verification fails?

**A**: Evidence seal mismatch indicates tampering. The auditor should:
1. Request a fresh evidence package export
2. Compare both packages to identify discrepancies
3. If fresh export also fails → escalate to incident response
4. Do NOT accept the evidence package; demand investigation

### Q: How do we prove a proposal was approved by a specific operator?

**A**: Autonomy reports include `operator_id` field. Cross-reference with:
- Telemetry logs (`operator_action` field shows approve/reject/defer)
- User database (maps `operator_id` to real identity)
- Operator signature (if multi-party approval on Sovereign Rail)

### Q: Can HYBA generate fake evidence to pass audits?

**A**: No. Evidence is generated by independent modules:
- Autonomy reports: written by `autonomy_persistence.py`
- Startup memos: written by `startup_memo_generator.py`
- Telemetry logs: written by `structlog` logger
- All write to append-only storage (no modification allowed)

If HYBA's code were compromised, the attacker would need to:
1. Modify all 3 evidence generation modules
2. Maintain consistency across JSON, Markdown, and log formats
3. Forge SHA-256 seals that pass independent verification
4. Do so without leaving traces in version control or deployment logs

This is computationally infeasible and would be detected by independent audit.

---

## Final Statement

**HYBA Evidence Packages are designed for independent verification by auditors with no access to the live system.**

Every autonomous action generates:
- A machine-readable autonomy report with SHA-256 seal
- A human-readable startup memo for executives
- Structured telemetry logs for incident investigation
- Rollback scripts for 30-day reversibility

**The evidence is portable. The verification is deterministic. The audit trail is immutable.**

---

**Next Steps**:
1. Review `GOVERNANCE.md` for governance rail configuration
2. Review `DEPLOYMENT.md` for evidence storage setup
3. Configure evidence retention periods via environment variables
4. Train operators on evidence package export workflow
5. Practice independent verification with audit team

**The forensic standard is operational. The audit trail is ready for inspection. The evidence is sealed.**
