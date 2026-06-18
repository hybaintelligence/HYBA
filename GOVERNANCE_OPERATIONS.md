# HYBA Governance Operations Manual

**Classification:** Sealed Foundation Governance  
**Last Updated:** June 18, 2026  
**Custodian:** HYBA Research  
**Status:** Active Operational

---

## Executive Summary

HYBA is operating as private sovereign-grade mathematical compute infrastructure under sealed institutional governance. This document establishes operational procedures for:

- Access control and operator management
- Proof verification and evidence sealing
- Capability limits and extraction capping
- Information compartmentalization
- Strategic communication protocol

---

## Access Control Framework

### Operator Classification

**Tier 0: Core Research**
- HYBA Research leadership
- System architects
- Access: Full system, all evidence, all code
- Clearance: Highest institutional level

**Tier 1: Operational**
- Mining operators
- Pool integration engineers
- Access: Live system, operator logs, performance metrics
- Clearance: Operational need-to-know
- Limit: 25% daily extraction cap (enforced in code)

**Tier 2: Strategic Partners**
- Qualified institutional reviewers
- Legal / governance advisors
- Access: Integration fence proof (25/25 tests), sealed evidence, public documentation
- Clearance: Compartmented briefings only
- Limit: No system access, evidence only

**Tier 3: Public**
- General stakeholders
- Academic researchers
- Access: Public documentation, positioning statements
- Clearance: General marketing materials
- Limit: No technical detail, no capability disclosure

### Operator Onboarding

1. **Clearance Review** — Institutional assessment (30 days)
2. **NDA Execution** — Sealed information agreement
3. **Role Assignment** — Tier-specific access grant
4. **Audit Trail** — All system access logged and reviewed
5. **Renewal Cycle** — Annual clearance re-verification

### Revocation Protocol

Any operator with expired clearance loses access immediately:
- System access disabled
- API credentials revoked
- Evidence access removed
- Audit notification issued

---

## Proof Verification Framework

### Integration Fence as Governance Boundary

**Verification Command:**
```bash
npm run test:integration-fence
```

**Expected Result:**
```
======================== 25 passed in 0.69s ========================
```

**What This Proves:**
- ✓ 14 Frontend/Backend Contracts (system architecture integrity)
- ✓ 5 Pool Handshake Contracts (Stratum protocol correctness)
- ✓ 6 True E2E Tests (runtime mining path verified)

**Access Level:** Tier 2+ (Strategic partners can verify independently)

### Live Share Submission Proof

**Verification Method:**
```bash
# Start 20-minute mining session
bash scripts/START_LIVE_MINING_20MIN.sh

# Evidence file generated
/tmp/hyba_live_miner_20min.log

# Collect verifiable evidence
python3 scripts/evidence_collection_live_mining.py \
  --log-file /tmp/hyba_live_miner_20min.log
```

**Evidence Collected:**
- Real Stratum connection (pool name, timestamp)
- Share submissions to actual pools
- Pool acceptance/rejection feedback
- Hash rate calculations
- Performance metrics
- No fabricated data

**Access Level:** Tier 2+ (Sealed evidence only, no real-time)

### Sealed Evidence Protocol

**Procedures:**
1. Evidence collected to `/tmp/hyba_live_miner_*.log`
2. Evidence extracted to `artifacts/evidence/{SESSION_ID}/`
3. Report generated: `mining_evidence.json`
4. Compartmented briefing: `report.txt`
5. Archive sealed: Evidence stored, access controlled

**Distribution:**
- Tier 0: Full technical detail
- Tier 1: Performance summaries only
- Tier 2: Sealed evidence (compartmented)
- Tier 3: None (public positioning only)

---

## Capability Limits and Extraction Capping

### Deliberate 25% Daily Cap

**Implementation:** Code enforces limit
```python
HYBA_EXTRACT_LIMIT_PCT = 0.25  # 25% daily maximum
```

**Enforcement:**
- Mining session stops at 25% of capacity
- Enforced in `UnifiedMiner._run_structured_search_batch()`
- Logged to audit trail
- No override available

**Rationale:**
- Demonstrates deliberate control
- Prevents competitive advantage disclosure
- Maintains strategic reserve
- Limits capability extraction

### Extraction Monitoring

**Daily Report:**
```
Session Date: 2026-06-18
Extraction Percentage: 22.3%
Capacity Remaining: 77.7%
Status: Within limits
Audit: OK
```

**Quarterly Review:**
- Total extraction vs. deliberate limit
- Trend analysis
- Strategic adjustment if needed

---

## Information Compartmentalization

### Classification Matrix

| Information | Public | Tier 1 | Tier 2 | Tier 0 |
|---|---|---|---|---|
| System exists | ✓ | ✓ | ✓ | ✓ |
| Bitcoin mining use | ✓ | ✓ | ✓ | ✓ |
| Integration fence (25/25) | - | ✓ | ✓ | ✓ |
| Live share data (sealed) | - | - | ✓ | ✓ |
| Stratum protocol details | - | ✓ | - | ✓ |
| Performance metrics | - | ✓ | - | ✓ |
| PULVINI methods | - | - | - | ✓ |
| φ-scaling doctrine | - | - | - | ✓ |
| Blockchain structure evidence | - | - | - | ✓ |
| Deterministic mechanism | - | - | - | ✓ |

### Document Handling

**Public Documents:**
- No classification marking
- Can be freely shared
- Example: `SOVEREIGN_ASSET_POSTURE.md`

**Restricted Documents:**
- Marked "RESTRICTED — Tier 2"
- Require clearance to access
- Digital only, no printing
- Example: Sealed evidence reports

**Classified Documents:**
- Marked "CLASSIFIED — Tier 0"
- Research custody only
- No external access
- Example: PULVINI compression methods

---

## Strategic Communication Protocol

### Official Positioning Statement

**For All External Communications:**

> "HYBA is a private sovereign compute asset owned by HYBA, HYBA Foundation, and HYBA Research. Bitcoin mining is the first externally priced proof boundary, not the business model. HYBA operates at the level of the mathematical substrate beneath mining."

### By Audience

**Government / Strategic Actors:**
- "Sovereign-grade mathematical compute infrastructure"
- "Proof is sealed and compartmented"
- "Governance is institutional"
- "Capability is deliberately capped at 25%"

**Academic / Research:**
- "Integration fence: 25/25 tests verify system"
- "Evidence is reproducible"
- "Deterministic substrate under research custody"
- "Details available under clearance"

**Qualified Technical Partners:**
- "Integration fence available for independent verification"
- "Live proof available through Stratum monitoring"
- "Evidence compartmented by clearance level"
- "Technical briefings by appointment only"

**General Market / Press:**
- "HYBA is private infrastructure"
- "Bitcoin mining is proof boundary"
- "Governance structure is sealed"
- "No further comment at this time"

### What NOT to Communicate

❌ Specific hash rates or performance advantages  
❌ Deterministic mechanism details  
❌ PULVINI compression methods  
❌ Φ-scaling doctrine or mathematics  
❌ Blockchain structure evidence  
❌ Autonomous governance specifics  
❌ Capability limitations or extraction caps  
❌ Strategic implications or valuation  

---

## Institutional Review Procedure

### Request Process

1. **Inquiry Received** — Routed to HYBA Research
2. **Classification** — Determine information tier needed
3. **Clearance Assessment** — Institutional suitability review
4. **NDA Negotiation** — Legal review and execution
5. **Access Grant** — Compartmented to specific information
6. **Briefing** — Technical presentation if appropriate
7. **Follow-up** — Document feedback, assess disclosure risk

### Types of Reviews

**Technical Validation:**
- Independent verification of integration fence
- Review of live share submission proof
- Assessment of evidence collection methodology
- Duration: 1-2 weeks
- Access: Tier 2 (sealed evidence)

**Strategic Assessment:**
- Institutional evaluation of capability implications
- Geopolitical impact analysis
- Competitive positioning assessment
- Duration: 2-4 weeks
- Access: Tier 2 (compartmented briefing)

**Partnership Exploration:**
- Capability alignment review
- Governance fit assessment
- Control and oversight discussion
- Duration: 4-8 weeks
- Access: Tier 2-3 escalation after institutional review

---

## Audit and Compliance

### Monthly Audit

1. **Access Log Review** — All operator access verified
2. **Extraction Compliance** — 25% cap enforced
3. **Evidence Integrity** — No fabrication detected
4. **Operator Status** — Clearances current
5. **Communication Compliance** — No unauthorized disclosure

### Annual Governance Review

1. **Ownership Structure** — Verify HYBA / Foundation / Research separation
2. **Access Control** — Audit all clearance levels
3. **Information Compartmentalization** — Classification compliance
4. **Strategic Communication** — Public messaging review
5. **Capability Limits** — Extraction capping effectiveness

### External Audit (Quarterly)

- Independent verification of integration fence
- Spot-check evidence sealing procedures
- Governance compliance assessment
- Auditor: Qualified third party (Tier 2 clearance)

---

## Escalation Matrix

| Situation | Response | Timeline | Authority |
|---|---|---|---|
| Operator clearance expired | Immediate revocation | 24 hours | Tier 0 |
| Unauthorized disclosure attempt | Investigation + action | 48 hours | Legal + Tier 0 |
| Government inquiry | Assessment + response | 5 days | Strategic review |
| Acquisition approach | Internal review | 10 days | Board level |
| Technical anomaly | Investigation | 3 days | Research |
| Evidence integrity concern | Forensic review | 24 hours | Tier 0 |

---

## Strategic Reserve Management

### Capability Preservation

The 25% daily extraction cap is deliberate. Remaining 75% capacity is strategic reserve:

- **Defensive:** Prevents competitive advantage leakage
- **Offensive:** Maintains capability advantage
- **Strategic:** Protects valuation floor
- **Institutional:** Demonstrates control

### Reserve Activation

Reserve capability activated only by:
- HYBA Research strategic decision
- Foundation board approval
- Documented geopolitical justification

---

## Endpoint: Sealed Status

HYBA operates under **sealed governance** effective immediately:

- ✓ Access controlled and audited
- ✓ Proof verified through integration fence
- ✓ Evidence sealed and compartmented
- ✓ Capability capped at 25%
- ✓ Information compartmented
- ✓ Communication protocol standardized
- ✓ Governance documented

This is not a company operating under normal business rules.
This is private sovereign infrastructure under institutional control.

**Status: Sealed. Governance: Active. Proof: Verified.**
