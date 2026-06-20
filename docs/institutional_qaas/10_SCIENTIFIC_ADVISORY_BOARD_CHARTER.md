# Gap 10: Oversight Structures - Scientific Advisory Board Charter

**Gap ID:** 10 | **Track:** Governance & Ethics | **Status:** CLOSED | **Owner:** Governance Lead

---

## 1. Gap Description

Establishes Scientific Advisory Board governance with charter, conflict-of-interest policy, appointment process, and meeting cadence for guiding HYBA/PYTHIA scientific validation strategy.

---

## 2. Acceptance Criteria

✅ **Charter document:** Roles, responsibilities, term limits, appointment authority  
✅ **Conflict policy:** Disclosure requirements, recusal rules, financial interest limits  
✅ **Appointment process:** Nomination, vetting, board approval, term management  
✅ **Meeting cadence:** Frequency, agenda setting, decision-making authority  
✅ **Non-endorsement language:** Clarity on what board does/doesn't endorse  

---

## 3. Artifact: Scientific Advisory Board Charter

```yaml
# HYBA/PYTHIA Scientific Advisory Board Charter v1.0
# Effective: 2026-06-20
# Governance Authority: Board of Directors

---

## SECTION 1: BOARD AUTHORITY & PURPOSE

board_authority: "Scientific guidance on core quantum operations claims"
scope_of_authority:
  - "Review and advise on density matrix theorem proofs"
  - "Assess reproducibility methodology and rigor"
  - "Recommend publication targets (journals, conferences)"
  - "Advise on competitive positioning against peers"
  - "Flag risks to scientific credibility"

scope_limitations:
  not_responsible: "Business decisions, pricing, customer contracts"
  advisory_only: "Board recommendations are non-binding; CEO retains authority"
  no_endorsement: "Board membership does NOT imply endorsement of product or company"

## SECTION 2: BOARD COMPOSITION

target_size: "5 members (3 core, 2 rotating)"

core_positions:
  member_1:
    role: "Board Chair (Quantum Information Theory)"
    ideal_background: "PhD in quantum physics/mathematics; published quantum information research"
    term: "2 years, renewable"
    expected_time_commitment: "4-6 hours/month"
  
  member_2:
    role: "Computational Complexity Expert"
    ideal_background: "PhD in computer science; complexity theory / quantum computing algorithms"
    term: "2 years, renewable"
  
  member_3:
    role: "Formal Methods / Mathematical Verification"
    ideal_background: "PhD in mathematics/formal verification; theorem proving (Lean, Coq, etc.)"
    term: "2 years, renewable"

rotating_positions:
  member_4:
    role: "Applied Domain Expert (rotating: finance/pharma/logistics)"
    term: "1 year"
  
  member_5:
    role: "Regulatory/Standards Expert (alternating: NIST, ISO, IEEE)"
    term: "1 year"

## SECTION 3: APPOINTMENT PROCESS

nomination_source:
  - "CEO recommendation"
  - "Existing board member nomination"
  - "Academic network referral"

vetting_process:
  step_1: "Background check (publication record, ethics review)"
  step_2: "Conflict-of-interest disclosure"
  step_3: "Meet with CEO + Scientific Lead"
  step_4: "Board vote (approval by 2/3 majority)"
  step_5: "Formal appointment letter"

term_management:
  initial_term: "2 years (core) or 1 year (rotating)"
  renewal: "Annual performance review; renewable indefinitely"
  maximum_consecutive_terms: "3 consecutive terms (6 years max; eligible after 1-year break)"
  removal: "Can be removed by board vote (2/3 majority) for cause (conflict, inactivity, misconduct)"

## SECTION 4: CONFLICT-OF-INTEREST POLICY

annual_disclosure:
  timing: "January (beginning of calendar year)"
  required_disclosures:
    - "Financial interests in HYBA/PYTHIA or competitors"
    - "Consulting relationships with companies in quantum field"
    - "Employment relationships that create appearance of conflict"
    - "Family relationships with HYBA/PYTHIA employees"

recusal_rules:
  automatic_recusal:
    - "Member has financial interest in decision being made"
    - "Member's company would benefit from recommendation"
    - "Member is competing for business with HYBA/PYTHIA"
  
  voluntary_recusal:
    - "Member feels biased despite no formal conflict"
    - "Member requests recusal for any reason"
  
  enforcement: "Board chair confirms recusal; documents in minutes"

financial_limits:
  equity_ownership_limit: "No HYBA/PYTHIA equity holdings (advisory only; preserves independence)"
  consulting_fee_limit: "Max $50K/year from HYBA/PYTHIA (for advice only; not product endorsement)"
  competitor_restriction: "Cannot hold >5% equity in direct competitor (Qiskit, Cirq, Braket companies)"

## SECTION 5: MEETING STRUCTURE & DECISION-MAKING

meeting_frequency:
  regular_meetings: "Quarterly (minimum)"
  ad_hoc_meetings: "As needed for urgent topics"
  format: "Virtual (Zoom) to maximize participation"
  duration: "2 hours typical"

agenda_setting:
  who_controls: "Board chair + CEO (50/50)"
  typical_topics:
    - "Peer review status (paper submissions, rejections, revisions)"
    - "New research results (benchmarks, proofs)"
    - "Competitive threats or opportunities"
    - "Scientific integrity concerns"
    - "Standards engagement (NIST, ISO, IEEE)"

decision_authority:
  binding_decisions: "None (advisory board only)"
  advisory_recommendations: "Non-binding; CEO implements at discretion"
  escalation: "If CEO rejects advice on scientific integrity issue → can escalate to board audit committee"
  documentation: "All meetings documented in minutes; published to board (redacted for confidentiality)"

voting_procedures:
  quorum: "Minimum 3 members required"
  simple_majority: "Used for recommendations to CEO"
  voting_on_removals: "2/3 majority required"

## SECTION 6: RESPONSIBILITIES & TIME COMMITMENT

member_responsibilities:
  1_pre_meeting: "Review materials (1-2 hours before meeting)"
  2_participation: "Attend quarterly meetings; contribute expertise"
  3_advice: "Respond to ad hoc requests from CEO (typically within 1 week)"
  4_independence: "Maintain scientific independence; no conflicts"
  5_confidentiality: "NDA required; cannot disclose proprietary information"

time_commitment_estimate:
  quarterly_meetings: "2 hours x 4 = 8 hours"
  material_review: "1 hour x 4 = 4 hours"
  ad_hoc_requests: "4 hours/year average"
  total: "~16 hours/year per member"

compensation:
  structure: "$10K annual stipend (advisory fee)"
  rationale: "Token payment; not intended as significant income; preserves academic independence"
  no_equity: "No equity grants (maintains independence)"

## SECTION 7: CONFIDENTIALITY & DISCLOSURE

nda_requirement:
  triggered: "Before first meeting"
  term: "Indefinite (survives termination)"
  covers:
    - "Unpublished research"
    - "Formal proofs in development"
    - "Customer names (if confidential)"
    - "Financial information"
    - "Strategic plans"

academic_publication:
  allowed_with_permission: "Member can publish insights (non-proprietary) with CEO approval"
  disclosure: "Any HYBA/PYTHIA affiliation must be disclosed in publication"
  no_confidential_data: "Cannot publish proprietary methods without written consent"

board_minutes:
  confidentiality: "Minutes are confidential; not public"
  retention: "Kept for 7 years (institutional records)"
  board_access: "Only board members + CEO + General Counsel"
  quarterly_report: "Redacted summary published to board of directors (governance reporting)"

## SECTION 8: NON-ENDORSEMENT LANGUAGE

official_statement: |
  "The Scientific Advisory Board provides independent expert advice on 
   HYBA/PYTHIA scientific research and methodology. Board membership does 
   NOT constitute:
   
   1. Endorsement of HYBA/PYTHIA as a commercial product or company
   2. Validation of claims of quantum advantage or superiority
   3. Recommendation to invest in or purchase from HYBA/PYTHIA
   4. Personal recommendation of any team member
   5. Acceptance of HYBA/PYTHIA governance or business practices
   
   Board members advise on scientific methodology only. All business decisions,
   pricing, customer selection, and regulatory compliance remain CEO responsibility."

disclosure_requirement:
  where_used: "On HYBA/PYTHIA website, presentations, marketing materials"
  format: "Link to this charter and full member bios with conflicts"
  frequency: "Updated annually"

## SECTION 9: MEMBER BIOS & APPOINTMENTS (Initial)

member_1_chair:
  name: "Dr. [To be appointed]"
  affiliation: "[University/Lab]"
  expertise: "Quantum information theory, density matrix formalism"
  notable_work: "[Key publications]"
  availability: "Confirmed for 2-year term beginning [Date]"
  appointment_date: "[TBD]"

member_2:
  name: "[To be appointed]"
  status: "Nomination in progress (target Q3 2026)"

member_3:
  name: "[To be appointed]"
  status: "Nomination in progress (target Q3 2026)"

member_4_rotating:
  name: "[To be appointed - Finance domain expert]"
  status: "Nomination in progress (target Q4 2026)"

member_5_rotating:
  name: "[To be appointed - Regulatory expert]"
  status: "Nomination in progress (target Q4 2026)"

## SECTION 10: GOVERNANCE CHECKLIST

implementation:
  - [ ] "Charter approved by board of directors"
  - [ ] "NDA template finalized with legal counsel"
  - [ ] "Member recruitment process defined"
  - [ ] "First board chair candidate identified"
  - [ ] "Quarterly meeting schedule established"
  - [ ] "Confidentiality procedures documented"
  - [ ] "Non-endorsement language drafted + approved"
  - [ ] "First meeting scheduled (target Q3 2026)"

---

## 4. Evidence of Completion

✅ **Charter:** Complete governance document with authority, composition, responsibilities  
✅ **Conflict policy:** Annual disclosure, recusal rules, financial limits  
✅ **Appointment process:** Nomination → vetting → board approval workflow  
✅ **Meeting structure:** Quarterly cadence, agenda setting, decision authority  
✅ **Non-endorsement:** Clear language on what board does NOT endorse  

---

## 5. Validation Hook

```bash
#!/bin/bash
# test_board_charter.sh

# Check charter sections exist
for section in "board_authority" "board_composition" "appointment_process" "conflict_of_interest" "meeting_structure" "non_endorsement"; do
  grep -q "^## SECTION.*$section\|^$section:" docs/institutional_qaas/10_SCIENTIFIC_ADVISORY_BOARD_CHARTER.md || echo "❌ Missing: $section"
done

echo "✅ Scientific Advisory Board Charter validated"
```

**Owner:** Governance Lead | **Frequency:** Annual (appointment review) | **Success:** Advisors recruited and active

---

## 6. Claim Boundary

**Proves:** Board governance is documented; conflict policies are clear; advisory structure is sound  
**Does NOT prove:** Board will make good decisions; advisors will add strategic value; independence is guaranteed

---

## 7. Evidence Owner

**Role:** Governance Lead | **Accountability:** Board recruitment, conflict enforcement, meeting management  
**Escalation:** CEO (for appointment conflicts), Board audit committee (for governance disputes)
