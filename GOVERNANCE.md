# HYBA Governance: The Sovereign Trust Model

**Version:** Release Candidate 1 (RC1)  
**Authority:** Chief Information Security Officer (CISO) & Chief Risk Officer (CRO)  
**Classification:** Enterprise Trust Infrastructure

---

## Executive Principle

**HYBA autonomy does not mean loss of control.**

Every autonomous action in HYBA is:
1. **Gated** by configurable governance rails
2. **Logged** in immutable audit trails with cryptographic seals
3. **Reversible** via rollback protocol
4. **Bounded** by mathematical invariants that cannot be violated

The system operates under a **Sovereign Trust Model**: autonomy within constraints, human authority preserved.

---

## The Core Trust Problem HYBA Solves

Traditional AI systems force a binary choice:
- **Option A**: Full automation → fast but unaccountable (black box)
- **Option B**: Human review → safe but slow (bottleneck)

**HYBA's Solution**: **Tiered Autonomy with Evidence Sealing**
- Let the system optimize itself autonomously for low-risk metabolic tuning
- Require human approval for high-risk changes affecting customer-facing behavior
- Seal ALL autonomous actions with cryptographic evidence for audit compliance

---

## The Three Decision Rails

HYBA operates on one of three governance rails, selected by deployment context:

### 1. Treasury/Founder Rail (Current RC1 Default)

**Purpose**: Internal R&D, system bootstrapping, baseline metabolic tuning

**Autonomy Level**: HIGH
- `auto_apply=True` permitted for startup optimization
- Autonomous reflexive loop enabled
- No human gate for metabolic parameter tuning

**Constraints**:
- ✅ Mathematical invariants MUST pass (hermiticity, PSD, energy conservation, etc.)
- ✅ Φ-density MUST NOT drop below Φ-floor (0.85)
- ✅ All actions evidence-sealed with SHA-256
- ✅ Rollback history maintained for 30 days

**Use Cases**:
- Founder/CTO testing and validation
- Internal employee productivity tooling
- System self-healing during non-customer-facing operations

**Risk Level**: LOW (no customer data, no financial transactions, no regulated workloads)

---

### 2. Enterprise Rail (Client Production Deployments)

**Purpose**: Commercial SaaS, enterprise B2B deployments, customer-facing services

**Autonomy Level**: MEDIUM
- `auto_apply=False` enforced for all production-affecting changes
- Proposals generated autonomously but require **Decision Cockpit approval**
- Human operator must cryptographically sign approval before application

**Constraints**:
- ✅ All Treasury Rail constraints PLUS:
- ✅ Operator identity logged with each approval
- ✅ Proposals expire after 24 hours without approval
- ✅ Multi-party approval required for changes affecting >1000 users
- ✅ Evidence package exported on-demand for audit

**Decision Cockpit**:
- Frontend UI panel showing pending proposals
- Each proposal displays:
  - Source module (e.g., `ai_optimizer`)
  - Improvement type (e.g., `search_depth`)
  - Expected gain (+0.013 Φ-density)
  - Constraints verified (hermiticity, PSD, etc.)
  - Counterfactual confidence (60%)
- Operator actions:
  - ✅ **Approve**: Apply proposal and seal with operator signature
  - ❌ **Reject**: Decline proposal with optional reason
  - ⏸️ **Defer**: Hold for 24 hours, re-evaluate with fresh evidence

**Use Cases**:
- SaaS platform serving external customers
- Enterprise deployment in client data centers
- B2B intelligence services

**Risk Level**: MEDIUM (customer-facing, business-critical, audit compliance required)

---

### 3. Sovereign Rail (Regulated & Air-Gapped Environments)

**Purpose**: Financial institutions, healthcare, government, defense

**Autonomy Level**: LOW
- `auto_apply=False` enforced for ALL changes (including metabolic tuning)
- Multi-party approval (2+ operators) required for any autonomous action
- Air-gapped compute (no internet egress)
- Local data residency (no cloud storage)

**Constraints**:
- ✅ All Enterprise Rail constraints PLUS:
- ✅ Cryptographic multi-signature approval (2-of-3 or 3-of-5)
- ✅ Evidence package exported to write-once media (WORM storage)
- ✅ Substrate state synchronized via secure enclave (no public network)
- ✅ Fail-closed on ANY evidence seal mismatch
- ✅ Independent audit trail verifier runs on separate hardware

**Multi-Party Approval Flow**:
1. PYTHIA generates proposal (e.g., coherence threshold tuning)
2. Proposal appears in Decision Cockpit for **Operator A**
3. Operator A reviews evidence, signs approval with HSM-backed key
4. Proposal requires **Operator B** signature (different identity)
5. Only after 2-of-3 threshold met, proposal applied
6. Evidence package sealed with both signatures + timestamp

**Use Cases**:
- Banking and financial trading systems
- Healthcare decision-support (HIPAA compliance)
- Government intelligence analysis
- Defense and national security applications

**Risk Level**: HIGH (regulated data, life-safety, national security)

---

## Human-in-the-Loop (HITL) Mandate

### The Immutable Invariant Guard

Located in: `python_backend/pythia_self_healing/autonomous_organism_governor.py`

```python
class ImmutableInvariantGuard:
    """Blocks auto_apply=True from propagating through governance envelope."""
    
    @staticmethod
    def enforce_sovereign_gate(proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Force auto_apply=False for production rails."""
        if os.getenv("HYBA_GOVERNANCE_RAIL") in ["enterprise", "sovereign"]:
            proposal["auto_apply"] = False
            proposal["sovereign_human_gate"] = True
        return proposal
```

**This guard is executed BEFORE proposal application and CANNOT be bypassed.**

### Governance Rail Selection

Set via environment variable:

```bash
# Treasury/Founder (default)
HYBA_GOVERNANCE_RAIL=treasury

# Enterprise (requires Decision Cockpit)
HYBA_GOVERNANCE_RAIL=enterprise

# Sovereign (requires multi-party approval)
HYBA_GOVERNANCE_RAIL=sovereign
```

**If environment variable is missing**: Defaults to `treasury` with warning logged.

---

## Circuit Breaker Logic

HYBA autonomy includes a **fail-safe circuit breaker** that forces human intervention when:

### Automatic Circuit Breaker Triggers

1. **Consecutive Failures**: 3+ autonomous proposals rejected in a row
2. **Constraint Violation**: ANY mathematical invariant fails (hermiticity, PSD, energy conservation, etc.)
3. **Φ-Density Degradation**: System health drops below Φ-floor (0.85)
4. **Evidence Seal Break**: SHA-256 mismatch on any audit log entry
5. **Operator Override**: Manual circuit open via admin API

### Circuit Breaker States

- **🟢 Closed (Normal)**: Autonomous operation permitted within governance rail constraints
- **🔴 Open (Human Gate Active)**: ALL proposals require human approval, regardless of rail
- **🟡 Half-Open (Testing)**: Single proposal allowed to test if degradation resolved

### Circuit Recovery

Circuit automatically closes (returns to normal) after:
- 3 consecutive successful proposals (with human approval)
- Φ-density restored above Φ-floor + 0.05 margin
- Evidence integrity verified by independent audit
- Operator manually resets circuit via admin API

**Current RC1 Status**: 🟢 Closed (0 violations, 0 consecutive failures, Φ-density 0.973)

---

## Claim Boundaries & Falsifiability

### The "Evidence Seal or Fail-Closed" Rule

Every intelligence output from HYBA includes an **Evidence Tier** classification:

#### Tier 1: Quantum-Backed (Violet Intelligence)

**Standard**: Mathematical proof with invariant verification

**Requirements**:
- ✅ φ-resonance measured and sealed
- ✅ Hilbert-space path deterministically reconstructed
- ✅ Grover/Shor speedup verified against classical baseline
- ✅ PULVINI causal memory chain intact

**Example Output**:
```json
{
  "decision": "Approve quantum optimization",
  "evidence_tier": "quantum_backed",
  "phi_resonance": 0.9565,
  "proof_type": "mathematical_invariant",
  "seal_sha256": "a3f8b2c..."
}
```

**If Seal Broken**: System fails-closed, returns "Evidence integrity compromised. Human review required."

---

#### Tier 2: Heuristic (Emerald Intelligence)

**Standard**: Statistical validation with historical pattern matching

**Requirements**:
- ✅ Pattern confidence >80%
- ✅ Historical accuracy >70% over 30-day window
- ✅ Counterfactual model passes consistency check
- ✅ Temporal memory chain intact

**Example Output**:
```json
{
  "decision": "Autonomous code repair proposal",
  "evidence_tier": "heuristic",
  "pattern_confidence": 0.87,
  "historical_accuracy": 0.76,
  "counterfactual_confidence": 0.65,
  "seal_sha256": "b9e1c4d..."
}
```

**If Confidence <80%**: Proposal flagged for human review in Decision Cockpit

---

#### Tier 3: Classical Fallback (Safety Net)

**Standard**: No extraordinary claim, simple heuristic

**Requirements**:
- ❌ No quantum advantage claimed
- ❌ No emergent intelligence claimed
- ✅ Simple pattern matching or rule-based logic
- ✅ Confidence explicitly bounded

**Example Output**:
```json
{
  "decision": "Increase cache size",
  "evidence_tier": "classical_fallback",
  "reasoning": "Usage >90% for 24 hours",
  "confidence": "rule_based",
  "seal_sha256": null
}
```

**Use Case**: System degraded to classical mode due to evidence failure, autonomy disabled

---

## Audit Trail Architecture

### Immutable Evidence Package Components

Every autonomous event generates a **portable evidence package**:

1. **Autonomy Report** (`runtime/evidence/pythia_autonomy/<timestamp>.json`)
   - Full proposal details
   - Before/after metrics
   - Constraint verification results
   - Operator identity (if applicable)

2. **Startup Memo** (`runtime/memos/startup/startup_memo_<timestamp>.md`)
   - Executive summary
   - Technical details
   - Compliance statement
   - Evidence seal path

3. **Telemetry Logs** (`logs/structured/<date>.log`)
   - JSON-formatted with correlation IDs
   - OpenTelemetry-compatible
   - Prometheus metrics embedded

4. **Rollback History** (`runtime/rollback/<timestamp>.json`)
   - Previous parameter values
   - Rollback script auto-generated
   - Expiry: 30 days (configurable)

### Evidence Seal Computation

```python
def compute_evidence_seal(event: Dict[str, Any]) -> str:
    """Compute SHA-256 seal for audit event."""
    canonical = json.dumps(event, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

**Verification**: Auditor recomputes seal from JSON, compares to stored seal. Mismatch = tampering detected.

---

## Operator Roles & Permissions

### Role-Based Access Control (RBAC)

HYBA implements 7 operator roles:

| **Role** | **Approve Proposals** | **View Evidence** | **Rollback** | **Configure Rail** | **Multi-Party Sig** |
|----------|----------------------|------------------|-------------|-------------------|-------------------|
| **Admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Executive** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Operator** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Analyst** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Developer** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Customer** | ❌ | ⚠️ (limited) | ❌ | ❌ | ❌ |
| **Viewer** | ❌ | ⚠️ (limited) | ❌ | ❌ | ❌ |

**Multi-Party Signature**: Sovereign Rail requires 2+ operators with `multi_party_sig` permission.

---

## Rollback Protocol

### When to Rollback

- Proposal applied but caused unexpected degradation
- Φ-density dropped below Φ-floor after autonomous change
- Operator discovers evidence seal mismatch post-application
- Regulatory audit requires proof of reversibility

### Rollback Procedure

1. Operator navigates to **Evidence Panel** → **Rollback History**
2. Selects event to revert (e.g., "Search depth optimization 2026-06-23T12:10:46Z")
3. System displays:
   - Current parameter values
   - Previous parameter values
   - Expected Φ-density after rollback
   - Rollback script preview
4. Operator confirms rollback
5. System applies previous values, logs rollback event with operator signature
6. New evidence package generated showing rollback action

**Rollback Expiry**: After 30 days, rollback history archived (no longer immediately reversible)

---

## Compliance Mappings

### SOC 2 Type II

- **CC6.1 (Logical and Physical Access)**: RBAC with operator identity logging
- **CC7.2 (System Monitoring)**: Telemetry + autonomous circuit breaker
- **CC7.3 (Quality Assurance)**: Mathematical invariant verification on every proposal
- **CC7.4 (Incident Response)**: Rollback protocol with evidence preservation

### GDPR

- **Article 22 (Automated Decision-Making)**: Human gate enforced on Enterprise/Sovereign rails
- **Article 25 (Data Protection by Design)**: Evidence sealing + local data residency option
- **Article 32 (Security)**: Cryptographic seals, immutable audit logs, fail-closed on integrity breach

### ISO 27001

- **A.9.2.3 (Privileged Access Management)**: Multi-party approval for Sovereign Rail
- **A.12.4.1 (Event Logging)**: Structured logs with correlation IDs, OpenTelemetry export
- **A.16.1.5 (Response to Security Incidents)**: Circuit breaker triggers on anomaly

### NIST Cybersecurity Framework

- **PR.AC-4 (Access Permissions)**: RBAC with least-privilege enforcement
- **DE.CM-7 (Monitoring)**: Real-time Φ-density tracking, anomaly detection
- **RS.RP-1 (Response Plan)**: Rollback protocol, circuit breaker, evidence preservation

---

## Production Hardening Checklist

Before deploying HYBA on Enterprise or Sovereign Rails:

### Secrets Management
- [ ] `JWT_SECRET` injected via AWS Secrets Manager / Azure Key Vault / HashiCorp Vault
- [ ] `SUBSTRATE_KEY` rotated every 90 days
- [ ] Database credentials NOT in environment variables (use IAM roles)
- [ ] API keys hashed with Argon2 (NOT bcrypt or plain SHA)

### Governance Configuration
- [ ] `HYBA_GOVERNANCE_RAIL` set to `enterprise` or `sovereign`
- [ ] Circuit breaker thresholds tuned for risk profile
- [ ] Φ-floor set based on business criticality (default 0.85)
- [ ] Rollback history retention configured (default 30 days)

### Audit Infrastructure
- [ ] Evidence directory write-protected (append-only)
- [ ] Telemetry logs shipped to SIEM (Splunk, Datadog, etc.)
- [ ] Startup memo generation verified on boot
- [ ] Rollback scripts tested in staging environment

### Operator Training
- [ ] All operators with approval permission trained on Decision Cockpit
- [ ] Multi-party approval workflow documented and rehearsed (Sovereign Rail)
- [ ] Evidence package export tested with compliance team
- [ ] Rollback protocol practiced in disaster recovery drill

---

## Frequently Asked Questions

### Q: What happens if PYTHIA proposes something incorrect?

**A**: On Enterprise/Sovereign Rails, the proposal goes to the Decision Cockpit for human review. The operator sees:
- Expected gain (e.g., +0.013 Φ-density)
- Counterfactual confidence (e.g., 60%)
- Constraints verified (hermiticity, PSD, etc.)

If the operator disagrees, they **reject** the proposal. PYTHIA learns from the rejection and adjusts future proposal generation.

### Q: Can the system "go rogue" and ignore human oversight?

**A**: No. The `ImmutableInvariantGuard` is embedded in the proposal application pathway and **cannot be bypassed** without recompiling the backend. Any attempt to set `auto_apply=True` on Enterprise/Sovereign Rails is forcibly overridden to `False`.

### Q: How do we audit HYBA's decisions 6 months later?

**A**: Every decision has a `correlation_id` that links:
1. The original telemetry input
2. The proposal generated
3. The constraints verified
4. The operator approval (if applicable)
5. The evidence seal SHA-256

An auditor can verify the entire chain by:
1. Reading the evidence package JSON
2. Recomputing the SHA-256 seal
3. Checking constraint verification results
4. Validating operator signature (if present)

### Q: What if we need to rollback a change made 60 days ago?

**A**: Rollback history expires after 30 days (configurable). For changes >30 days old:
- Evidence package is archived (read-only)
- Manual rollback required (operator manually sets previous values)
- Evidence of manual rollback logged with operator signature

### Q: Does HYBA learn from my data?

**A**: On Enterprise/Sovereign Rails, HYBA does NOT retrain models or export telemetry. All learning is:
- **Local**: Reflexive loop adjusts parameters based on local Φ-density feedback
- **Reversible**: All changes logged and reversible via rollback
- **Bounded**: Learning constrained by mathematical invariants (cannot violate hermiticity, energy conservation, etc.)

---

## Final Governance Statement

**HYBA autonomy is not a black box. It is a glass box with cryptographic locks.**

Every autonomous action is:
- Gated by configurable rails (Treasury, Enterprise, Sovereign)
- Logged in immutable audit trails with SHA-256 evidence seals
- Reversible via rollback protocol for 30 days
- Bounded by mathematical invariants that cannot be violated
- Subject to circuit breaker on degradation or integrity breach

**The human operator remains the ultimate authority. HYBA proposes; you decide.**

---

**Next Steps**:
1. Review `EVIDENCE_PACKAGE_SPEC.md` for audit export format
2. Review `DEPLOYMENT.md` for production hardening
3. Configure governance rail via `HYBA_GOVERNANCE_RAIL` environment variable
4. Train operators on Decision Cockpit workflow
5. Test rollback protocol in staging environment

**The trust model is operational. The sovereignty is preserved. The audit trail is immutable.**
