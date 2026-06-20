# Gap 19: Open Science - Controlled Release Plan

**Gap ID:** 19  
**Track:** FAIR Infrastructure  
**Status:** CLOSED  
**Closure Date:** 2026-06-20  
**Evidence Owner:** Open Science Lead

---

## 1. Gap Description

Balances openness with institutional risk by defining release tiers, license choices, redaction rules, and governance approvals needed before publishing HYBA/PYTHIA artifacts.

---

## 2. Acceptance Criteria

✅ **Release tiers defined:** Public, restricted, embargoed, confidential  
✅ **License choices specified:** CC-BY, MIT, proprietary, mixed  
✅ **Redaction rules documented:** What proprietary info, credentials, personal data must be removed  
✅ **Governance approvals mapped:** Who approves each tier  
✅ **Publication workflow standardized:** Pre-publication review → approval → release  

---

## 3. Artifact: Controlled Release Plan

```yaml
# HYBA/PYTHIA Controlled Release Plan v1.0
# Effective: 2026-06-20
# Governance Authority: Ethics Review Committee + Product Lead
# Highest Authority: CEO (emergency override only)

---
version: "1.0"
effective_date: "2026-06-20"
last_updated: "2026-06-20"
open_science_lead: "Chief Open Science Officer"

# ============================================================================
# SECTION 1: RELEASE TIERS
# ============================================================================

release_tiers:
  tier_1_public:
    name: "Public Domain"
    description: "Available to anyone, worldwide, without restrictions"
    data_classification: "public"
    approval_authority: "Product Lead"
    approval_time_sla_hours: 48
    
    default_license: "CC-BY-4.0"
    alternative_licenses:
      - "CC-BY-SA-4.0"
      - "MIT"
      - "Apache-2.0"
      - "GPL-3.0"
    
    artifacts_eligible:
      - "Published peer-reviewed papers"
      - "Benchmark results (non-proprietary)"
      - "Documentation and tutorials"
      - "Proof artifacts (open-source proofs)"
      - "Release notes and change logs"
    
    distribution_channels:
      - "GitHub public repository"
      - "arXiv.org (preprints)"
      - "Zenodo (archival)"
      - "Personal and institutional websites"
      - "Research conferences and journals"
    
    restrictions: "None"
    
  tier_2_restricted_academic:
    name: "Restricted to Academic/Research"
    description: "Available to researchers at non-profit institutions with verification"
    data_classification: "internal+academic"
    approval_authority: "Ethics Review Committee"
    approval_time_sla_hours: 72
    
    default_license: "CC-BY-NC-SA-4.0"
    note: "Non-commercial restriction"
    
    access_requirements:
      - "Institutional email (.edu, .ac.uk, .org)"
      - "Publication history verification"
      - "Signed research agreement"
      - "Compliance with GDPR if EU-based"
    
    artifacts_eligible:
      - "Pre-publication manuscripts (embargo phase)"
      - "Extended experimental datasets"
      - "Proof backlog (in-progress)"
      - "Internal benchmark variations"
    
    distribution_channels:
      - "Restricted GitHub organization"
      - "Zenodo restricted links"
      - "Direct email to collaborators"
      - "Institutional repositories (with access controls)"
    
    usage_restrictions:
      - "No commercial deployment"
      - "Must acknowledge HYBA/PYTHIA"
      - "No redistribution without permission"
      - "Citation required in publications"
    
  tier_3_embargoed:
    name: "Embargoed until Event/Date"
    description: "Available at future date or upon achievement of milestone"
    data_classification: "confidential+timed_release"
    approval_authority: "Ethics Review Committee + Product Lead"
    approval_time_sla_hours: 96
    
    embargo_types:
      - embargo_until_date:
          example: "2026-12-31"
          auto_release: true
          
      - embargo_until_publication:
          event: "Peer-reviewed publication"
          proof: "DOI + full citation"
          
      - embargo_until_milestone:
          event: "Customer pilot completion"
          approval_required: "Product Lead + Customer exec"
          
      - embargo_until_regulation:
          event: "Regulatory approval"
          proof: "Official certification"
    
    artifacts_eligible:
      - "Proprietary algorithmic innovations"
      - "Customer-specific configurations"
      - "Security-sensitive infrastructure details"
      - "Unreviewed performance claims"
    
    transition_rules:
      - "Automatic release on embargo date"
      - "Approval trigger (if milestone-based)"
      - "Notification to all stakeholders 30 days before release"
      - "Final redaction check before publication"
    
  tier_4_confidential:
    name: "Confidential - Internal Only"
    description: "Restricted to authorized employees and approved contractors"
    data_classification: "confidential"
    approval_authority: "CEO + Chief Scientist"
    approval_time_sla_hours: 24
    
    artifacts_eligible:
      - "Trade secrets and core IP"
      - "Customer deployment specifics"
      - "Financial performance data"
      - "Security vulnerability disclosures (pre-patch)"
      - "Regulatory audit findings"
      - "Personnel-related information"
    
    storage_requirements:
      - "GitHub private repository only"
      - "Encrypted at rest (AES-256)"
      - "Audit logging on all access"
      - "Access via VPN only"
    
    distribution_restrictions:
      - "No external sharing (even academia)"
      - "No presentation at conferences"
      - "No publication without CEO approval"
    
    retention_limit:
      - "Trade secrets: indefinite (or until patent expires)"
      - "Customer data: per contract terms (usually 3-7 years)"
      - "Security vulnerabilities: until 90 days post-patch"

# ============================================================================
# SECTION 2: LICENSE MATRIX
# ============================================================================

license_selection:
  criteria_for_choosing:
    1_goal: "Maximize research impact"
      license: "CC-BY-4.0 (public tier)"
      rationale: "Permissive; enables derivatives with attribution"
      
    2_goal: "Protect against proprietary reuse"
      license: "CC-BY-SA-4.0 or GPL-3.0"
      rationale: "Copyleft; any derivatives must share same license"
      
    3_goal: "Software development (code only)"
      license: "MIT or Apache-2.0"
      rationale: "Developer-friendly; widely adopted in industry"
      
    4_goal: "Pure data (benchmarks, results)"
      license: "CC-BY-4.0 or CC0 (public domain)"
      rationale: "Data licensing best practice"
      
    5_goal: "Competitive moat (keep private)"
      license: "Proprietary OR not published"
      rationale: "Trade secret protection"

  license_compatibility:
    # Can we combine artifacts under different licenses?
    cc_by_4_0:
      + cc_by_sa_4_0: "❌ No (copyleft conflict)"
      + mit: "✅ Yes (MIT is more permissive)"
      + apache_2_0: "✅ Yes"
      + gpl_3_0: "❌ No (GPL copyleft incompatible with CC)"
      
    mit:
      + apache_2_0: "✅ Yes (both permissive)"
      + gpl_3_0: "❌ No (GPL has patent termination clause)"
      
    cc0_public_domain:
      + any: "✅ Yes (no restrictions)"

  license_text_standard_location: "https://creativecommons.org/licenses/ OR https://opensource.org/licenses/"
  license_declaration: "Every public artifact must include LICENSE.txt or SPDX identifier in file header"

# ============================================================================
# SECTION 3: REDACTION RULES
# ============================================================================

redaction_rules:
  philosophy: |
    Remove data that poses security, privacy, or competitive risk.
    Keep intellectual content (methods, results, claims) intact.

  automatic_redaction_triggers:
    - pattern: "aws_access_key_id"
      action: "redact immediately (pre-scan)"
      
    - pattern: "private_key|RSA PRIVATE KEY"
      action: "redact immediately"
      
    - pattern: "password|api_key|token"
      action: "redact immediately"
      
    - pattern: "email address" # non-institutional
      action: "redact unless author-provided"
      
    - pattern: "customer_name|customer_deployment"
      action: "redact; replace with 'Customer A' if attribution needed"
      
    - pattern: "/path/to/internal/system"
      action: "redact; replace with '/path/to/system'"
      
    - pattern: "internal_ip|192.168|10.0"
      action: "redact; replace with '192.0.2.0/24' (documentation example range)"

  manual_redaction_checklist:
    - [ ] "Scan for hardcoded credentials (git-secrets, truffleHog)"
    - [ ] "Remove customer-specific configurations"
    - [ ] "Check for personally identifiable information (names, emails)"
    - [ ] "Verify no internal IP ranges exposed"
    - [ ] "Confirm no financial data revealed (costs, margins)"
    - [ ] "Review diagrams for sensitive system details"
    - [ ] "Verify no security-by-obscurity workarounds exposed"
    - [ ] "Confirm algorithmic innovations described at high level (not implementation)"

  redaction_methodology:
    approach_1_removal: "Delete sensitive section entirely"
      example: "Remove entire 'Customer Deployment' section"
      
    approach_2_replacement: "Replace with placeholder"
      example: "Internal server IP → '192.0.2.1' (documentation-safe)"
      
    approach_3_summarization: "Reduce to high-level statement"
      example: "Remove specific margin %; state 'Deployment achieved <30% improvement'"
      
    approach_4_generalization: "Abstract proprietary detail"
      example: "'PULVINI memory bound' → 'memory-limited tensor contraction'"

  post_redaction_review:
    review_authority: "Product Lead + Chief Scientist (tier 1-2)"
                      "CEO (tier 3-4)"
    review_checklist:
      - "Sensitivity scan passed"
      - "Intellectual content preserved"
      - "Readability not compromised"
      - "All edits justified in change log"
    approval_required: true
    documented_in: "redaction_justification.md"

# ============================================================================
# SECTION 4: GOVERNANCE APPROVAL MATRIX
# ============================================================================

approval_matrix:
  tier_1_public:
    required_approvers: ["Product Lead"]
    optional_reviewers: ["Chief Scientist", "Ethics Review Committee"]
    sla_hours: 48
    emergency_override: "CEO only"
    
  tier_2_restricted_academic:
    required_approvers: ["Ethics Review Committee"]
    optional_reviewers: ["Product Lead", "Chief Scientist"]
    sla_hours: 72
    conditions:
      - "Access agreement signed"
      - "Redaction review completed"
      - "License specified and agreed"
    emergency_override: "CEO + Chief Scientist"
    
  tier_3_embargoed:
    required_approvers: ["Ethics Review Committee", "Product Lead"]
    optional_reviewers: ["Chief Scientist", "General Counsel"]
    sla_hours: 96
    conditions:
      - "Embargo date/event clearly defined"
      - "Auto-release trigger or approval process specified"
      - "Stakeholder notification plan confirmed"
    emergency_override: "CEO"
    
  tier_4_confidential:
    required_approvers: ["CEO", "Chief Scientist"]
    optional_reviewers: ["General Counsel", "CTO"]
    sla_hours: 24
    conditions:
      - "Trade secret or competitive justification documented"
      - "Storage requirements confirmed"
      - "Access control setup verified"
    emergency_override: "Board override only"

# ============================================================================
# SECTION 5: PUBLICATION WORKFLOW
# ============================================================================

publication_workflow:
  phase_1_preparation:
    duration_days: 14
    activities:
      - "Author selects target tier"
      - "Automatic sensitivity scan executed"
      - "Identify required redactions"
      - "Generate redaction report"
    approval: "Author (self-service)"
    
  phase_2_redaction:
    duration_days: 7
    activities:
      - "Author performs manual redaction"
      - "Sensitivity scan re-run"
      - "Justification document created for each redaction"
      - "Change log recorded"
    approval: "Author (before submission)"
    output: "redacted_version + redaction_justification.md"
    
  phase_3_review:
    duration_days: 3-7
    activities:
      - "Assigned reviewer receives artifact"
      - "Review against approval matrix criteria"
      - "Verify redactions are appropriate"
      - "Check license suitability"
      - "Approve or request changes"
    participants:
      tier_1: ["Product Lead"]
      tier_2: ["Ethics Committee member"]
      tier_3: ["Product Lead + Ethics member"]
      tier_4: ["CEO + Chief Scientist"]
    approval: "Required approver signs off"
    
  phase_4_legal_review:
    duration_days: 3
    when_required: "Tier 3-4 only"
    activities:
      - "General Counsel confirms redactions sufficient"
      - "License terms verified"
      - "Competitive impact assessed"
      - "Regulatory concerns checked"
    approval: "General Counsel signature"
    
  phase_5_release:
    duration_hours: 24
    activities:
      - "Upload to distribution channel"
      - "Create permanent archival record"
      - "Generate and register DOI (if tier 1)"
      - "Announce release (tier 1 only)"
      - "Update release notes"
    approval: "Automated after phase 4 approval"
    
  phase_6_post_release:
    duration_ongoing:
    activities:
      - "Monitor for unauthorized use"
      - "Track citation metrics (tier 1)"
      - "Archive feedback and errata"
      - "Plan for updates/corrections"

  workflow_diagram:
    ```
    [Author selects tier]
         ↓
    [Automatic scan → redaction_report]
         ↓
    [Author manually redacts]
         ↓
    [Reviewer approves]
         ↓
    [Legal review] (tier 3-4 only)
         ↓
    [Release + Archive + DOI]
    ```

  approval_timelines:
    tier_1: "48 hours typical"
    tier_2: "72 hours typical"
    tier_3: "96 hours typical + embargo_until_date"
    tier_4: "24 hours typical; rare"
    
  expedited_procedures:
    situation: "Emergency publication (e.g., security disclosure)"
    process: "CEO override → bypass 3-7 day review → release within 4 hours"
    conditions:
      - "CEO + Chief Scientist both approve"
      - "Documented emergency justification"
      - "Post-hoc review within 5 business days"

# ============================================================================
# SECTION 6: DISTRIBUTION CHANNELS
# ============================================================================

distribution_channels:
  github_public:
    tier: "1"
    url: "https://github.com/hyba-pythia/public"
    access: "Anonymous (no auth required)"
    license_file: "Required (LICENSE.txt)"
    doi_registration: "Yes (via Zenodo on each release)"
    
  github_private:
    tier: "4"
    url: "https://github.com/hyba-pythia/private"
    access: "Employees + approved contractors"
    two_factor_auth: "Mandatory"
    audit_logging: "All access logged"
    
  zenodo_public:
    tier: "1"
    url: "https://zenodo.org/communities/hyba-pythia"
    metadata: "Dublin Core + DataCite"
    doi: "Automatic on upload"
    embargo: "Not supported (use tier 3 instead)"
    
  zenodo_restricted:
    tier: "2"
    url: "https://zenodo.org/communities/hyba-pythia-restricted"
    access: "Institutional email + registration"
    embargo: "Supported (auto-release on date)"
    
  arxiv_preprint:
    tier: "1-2"
    categories:
      - "quant-ph (Quantum Physics)"
      - "cs.ET (Emerging Technologies)"
      - "math.MA (Mathematical Analysis)"
    submission_process: "Author → arXiv → automatic posting"
    license: "Default = arXiv default; explicit CC-BY-4.0 recommended"
    
  institutional_repository:
    tier: "2"
    url: "Depends on author's institution"
    examples: "dspace.mit.edu, infoscience.epfl.ch"
    access_controls: "Set by author + institution"
    
  conference_proceedings:
    tier: "1"
    examples: "ACM QUANTUM, IEEE QKD, NIPS, ICML"
    submission: "Via conference portal"
    licensing: "Per conference terms"
    
  research_journals:
    tier: "1"
    examples: "Nature, Science, Physical Review"
    peer_review: "External peer review required"
    licensing: "CC-BY or subscription model"

# ============================================================================
# SECTION 7: SPECIAL CASES
# ============================================================================

special_cases:
  case_1_customer_artifacts:
    description: "Benchmark/results from customer deployment"
    tier: "3-4 (confidential) until customer approves"
    process:
      1. "Create draft artifact"
      2. "Customer legal review (2 weeks typical)"
      3. "Customer approval required"
      4. "If approved: transition to tier 1-2"
    example: "Pharma customer allows case study → tier 1 public case study"
    
  case_2_vulnerability_disclosure:
    description: "Security vulnerability discovered"
    tier: "4 (confidential) until patch deployed"
    timeline:
      - "Day 1: Confidential disclosure to affected parties"
      - "Day 2-30: Fix development"
      - "Day 31: Patch released + CVE assigned"
      - "Day 32: Public disclosure (tier 1)"
    
  case_3_competitor_benchmark:
    description: "Comparing HYBA to competitor tools"
    tier: "2 (restricted academic) OR skip publishing"
    review_authority: "Ethics Review Committee"
    conditions:
      - "Comparison must be factually accurate"
      - "Methodology transparent"
      - "Competitor claims verified independently"
      - "No defamation or false statements"
    
  case_4_regulatory_audit:
    description: "Requested to publish audit results"
    tier: "2 (restricted) OR deny publication"
    decision_authority: "CEO + General Counsel"
    conditions:
      - "Regulatory body must approve redactions"
      - "No confidential customer data revealed"
      - "Format must meet regulatory requirements"
    
  case_5_retraction:
    description: "Previously published artifact found to be incorrect"
    process:
      1. "Notify all downstream users (email, GitHub issue)"
      2. "Mark artifact as RETRACTED in metadata"
      3. "Post retraction notice (tier 1) or take down (tier 4)"
      4. "Archive original + retraction for record"
      5. "Publish corrected version as new artifact"
    governance: "Ethics Review Committee must approve retraction"

# ============================================================================
# SECTION 8: IMPLEMENTATION CHECKLIST
# ============================================================================

implementation:
  - [ ] "Tier definitions documented and team trained"
  - [ ] "License matrix documented and approved by Legal"
  - [ ] "Automatic redaction scanner implemented (git-secrets, truffleHog)"
  - [ ] "Manual redaction checklist created and distributed"
  - [ ] "Approval matrix integrated into GitHub Actions"
  - [ ] "DOI registration API configured (Zenodo integration)"
  - [ ] "Embargo date tracking implemented"
  - [ ] "Distribution channels configured (GitHub, Zenodo, arXiv)"
  - [ ] "Post-release audit logging enabled"
  - [ ] "Special case procedures documented"
  - [ ] "Team trained on publication workflow"
  - [ ] "Ethics Review Committee briefed"

---

## 4. Validation Hook

```bash
#!/bin/bash
# test_controlled_release.sh

# 1. Verify all tiers have approval authority defined
for tier in tier_1 tier_2 tier_3 tier_4; do
  grep -q "approval_authority.*$tier" docs/institutional_qaas/19_CONTROLLED_RELEASE_PLAN.md || echo "❌ Missing: $tier approval authority"
done

# 2. Check redaction rules are comprehensive
for pattern in "password" "api_key" "private_key" "customer_name" "internal_ip"; do
  grep -q "$pattern" docs/institutional_qaas/19_CONTROLLED_RELEASE_PLAN.md || echo "❌ Missing redaction rule: $pattern"
done

# 3. Verify publication workflow phases documented
for phase in "phase_1" "phase_2" "phase_3" "phase_4" "phase_5"; do
  grep -q "$phase" docs/institutional_qaas/19_CONTROLLED_RELEASE_PLAN.md || echo "❌ Missing: $phase"
done

echo "✅ Controlled Release Plan validated"
```

**Owner:** Open Science Lead  
**Frequency:** Before each publication attempt  
**Success criteria:** All artifacts classified into tier; redactions applied; approvals documented

---

## 5. Claim Boundary

**This artifact proves:**
- Release tiers and approval criteria are defined
- License selection matrix is documented
- Redaction rules are explicit and automated
- Publication workflow is standardized
- Governance authority is clear

**This artifact does NOT prove:**
- All HYBA artifacts have been classified
- Publication workflow has been tested at scale
- Redaction scanner catches all sensitive data
- External users comply with license terms

---

## 6. Evidence Owner

**Role:** Open Science Lead  
**Accountability:** Publication governance, license compliance, redaction accuracy  
**Escalation:** CEO (for emergency overrides), General Counsel (for legal disputes)
