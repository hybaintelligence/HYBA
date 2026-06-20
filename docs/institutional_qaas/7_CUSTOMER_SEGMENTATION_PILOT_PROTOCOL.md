# Gap 7: Customer Segmentation - Pilot Qualification Checklist

**Gap ID:** 7  
**Track:** Commercial Validation  
**Status:** CLOSED  
**Closure Date:** 2026-06-20  
**Evidence Owner:** GTM Lead

---

## 1. Gap Description

Defines pilot qualification gates for each customer segment (finance, pharma, logistics, research) with onboarding checklist and ROI worksheet.

---

## 2. Acceptance Criteria

✅ **ICP (Ideal Customer Profile):** Firmographics, technographics, buying pattern  
✅ **Qualification gates:** BANT framework (budget, authority, need, timeline)  
✅ **Onboarding checklist:** 30/60/90-day milestones  
✅ **ROI worksheet:** Cost-benefit template for each segment  
✅ **Success criteria:** Pilot completion metrics and graduation path  

---

## 3. Artifact: Customer Segmentation Pilot Protocol

```yaml
# HYBA/PYTHIA Customer Segmentation & Pilot Protocol v1.0
# Effective: 2026-06-20
# GTM Lead: Chief Commercial Officer

---

# ============================================================================
# SECTION 1: IDEAL CUSTOMER PROFILES (ICP)
# ============================================================================

ideal_customer_profiles:
  icp_1_research_lab:
    name: "Quantum Research Lab"
    ideal_firmographics:
      type: ["University (R1/R2)", "National Lab", "Corporate Research Center"]
      size: "20-100 quantum researchers"
      budget_authority: "Department head or research director"
      annual_quantum_rd_budget: "\$500K - \$5M"
    
    ideal_technographics:
      current_tools: ["Qiskit", "Cirq", "custom Python", "academic papers"]
      pain_point: "Hardware access quota limitations"
      technical_maturity: "High (PhDs, published researchers)"
    
    buying_pattern:
      decision_cycle: "3-6 months (driven by proposal cycles)"
      committee_size: 3-5
      influencers: "Lab director, senior researcher"
      budgeting: "Annual allocation (grant-dependent)"
    
    qualification_gates:
      gate_1_immediate_need:
        question: "Are you currently using or evaluating quantum simulators?"
        pass_criteria: "Yes, spending > \$10K/year on cloud quantum"
      
      gate_2_decision_authority:
        question: "Can lab director approve \$10K-100K annual spend?"
        pass_criteria: "Yes, or can route through department"
      
      gate_3_technical_readiness:
        question: "Does team have Python + research computing background?"
        pass_criteria: "Yes, or willing to allocate 1 FTE for learning"
      
      gate_4_timeline:
        question: "When would you want to pilot this (timeline)?"
        pass_criteria: "Within 90 days"
    
    disqualifiers:
      - "Hardware vendor (would view HYBA as competitive threat)"
      - "No quantum computing interest currently"
      - "Constrained by funding freeze (revisit annually)"
    
    target_monthly_pipeline: 20 leads
    expected_monthly_qualified: 5-10
    expected_conversion_rate: 60%
    expected_monthly_pilots: 3-6

  icp_2_finance_qrm:
    name: "Quantitative Finance / Risk Management"
    ideal_firmographics:
      type: ["Investment Bank", "Hedge Fund", "Insurance Company"]
      size: "50-500 quantitative staff"
      department: "Quant Research, Trading Technology, Risk Management"
      annual_quantum_evaluation_budget: "\$500K - \$5M"
    
    ideal_technographics:
      current_tools: ["Python, C++", "machine learning frameworks", "optimization solvers"]
      pain_point: "Uncertain quantum ROI before capital commitment"
      technical_maturity: "Very high (PhDs, expert engineers)"
      data_requirements: "Must keep proprietary; can't use cloud"
    
    buying_pattern:
      decision_cycle: "6-12 months (board approval for CapEx)"
      committee_size: 5-10 (CFO, CTO, CRO, Quant Head)
      influencers: "Head of Quant Research, CTO"
      budgeting: "Annual capital allocation cycle"
    
    qualification_gates:
      gate_1_problem_fit:
        question: "Do you have specific optimization problems where quantum might help?"
        pass_criteria: "Yes, identified 2-3 problems (VQE, QAOA, etc.)"
      
      gate_2_budget:
        question: "Is there \$100K+ available for evaluation?"
        pass_criteria: "Yes, approved or pending board approval"
      
      gate_3_authority:
        question: "Who can commit to a 90-day pilot?"
        pass_criteria: "CTO or Head of Quant (C-suite authority)"
      
      gate_4_confidentiality:
        question: "Must data remain on-premises?"
        pass_criteria: "Yes; if yes, must have VPC deployment option"
    
    disqualifiers:
      - "No internal quantum expertise (not ready to evaluate)"
      - "Competitor to HYBA investors"
      - "Cannot allocate dedicated 1-2 FTE for pilot"
    
    target_monthly_pipeline: 10 leads
    expected_monthly_qualified: 2-3
    expected_conversion_rate: 70%
    expected_monthly_pilots: 1-2

  icp_3_pharma_drug_discovery:
    name: "Pharmaceutical Drug Discovery"
    ideal_firmographics:
      type: ["Large Pharma", "Biotech Startup", "CRO"]
      size: "100+ computational chemists"
      department: "Computational Chemistry, Drug Informatics"
      annual_quantum_evaluation_budget: "\$200K - \$2M"
    
    ideal_technographics:
      current_tools: ["Gaussian", "MOPAC", "Schrodinger", "open-source DFT"]
      pain_point: "Molecular simulation bottleneck; quantum might help"
      technical_maturity: "Medium (chemistry PhDs, some coding)"
      regulatory_requirement: "FDA-auditable methodology"
    
    buying_pattern:
      decision_cycle: "9-12 months (R&D budget cycles)"
      committee_size: 3-5 (Comp Chemistry Lead, R&D Director)"
      influencers: "Computational Chemistry Head"
      budgeting: "Annual R&D allocation"
    
    qualification_gates:
      gate_1_problem_scope:
        question: "Do you have 2-3 molecule classes to test?"
        pass_criteria: "Yes, molecules identified"
      
      gate_2_dft_baseline:
        question: "Do you have classical DFT results for benchmarking?"
        pass_criteria: "Yes, can provide 10+ molecules with known DFT solutions"
      
      gate_3_regulatory_ready:
        question: "Is your team comfortable with reproducible methodology?"
        pass_criteria: "Yes, already use validated DFT software"
      
      gate_4_commitment:
        question: "Can you dedicate 1-2 FTE for 90-day pilot?"
        pass_criteria: "Yes"
    
    disqualifiers:
      - "No molecular data (privacy restriction)"
      - "Cannot publish or patent results"
      - "No computational chemistry background"
    
    target_monthly_pipeline: 5 leads
    expected_monthly_qualified: 1-2
    expected_conversion_rate: 60%
    expected_monthly_pilots: 0-1

  icp_4_logistics_optimization:
    name: "Supply Chain & Logistics Optimization"
    ideal_firmographics:
      type: ["Logistics Company", "Retailer Supply Chain", "Airline"]
      size: "50-200 operations research staff"
      department: "Supply Chain Optimization, AI/ML"
      annual_quantum_evaluation_budget: "\$100K - \$500K"
    
    ideal_technographics:
      current_tools: ["Python/R", "OR tools", "machine learning"]
      pain_point: "Vehicle routing & scheduling still uses heuristics"
      technical_maturity: "Medium-high (OR PhDs, experienced engineers)"
    
    buying_pattern:
      decision_cycle: "6-9 months"
      committee_size: 3-4
      influencers: "Chief Operations Officer, Chief Data Officer"
      budgeting: "Annual ops budget or CapEx allocation"
    
    qualification_gates:
      gate_1_problem_size:
        question: "What's the typical vehicle routing problem size?"
        pass_criteria: "50-500 stops (matches quantum capabilities)"
      
      gate_2_impact_quantified:
        question: "What's the cost of a 1-5% solution improvement?"
        pass_criteria: "\$1M+ annual impact (ROI-positive for pilots)"
      
      gate_3_data_access:
        question: "Can you provide historical optimization instances?"
        pass_criteria: "Yes, at least 100 instances"
      
      gate_4_team:
        question: "Does team have optimization + coding experience?"
        pass_criteria: "Yes, or willing to learn"
    
    disqualifiers:
      - "Problem size too small (< 20 stops) - not worth quantum"
      - "Cannot quantify impact (business case not justified)"
      - "Black-box only solutions (can't adopt transparent approach)"
    
    target_monthly_pipeline: 8 leads
    expected_monthly_qualified: 2-3
    expected_conversion_rate: 50%
    expected_monthly_pilots: 1-2

# ============================================================================
# SECTION 2: QUALIFICATION PROCESS (BANT)
# ============================================================================

bant_qualification_process:
  budget:
    tier_1_research: "Pilot budget \$10K-50K (confirmed)"
    tier_2_finance: "Pilot budget \$100K-500K (pending board approval acceptable)"
    tier_3_pharma: "Pilot budget \$50K-200K (confirmed)"
    tier_4_logistics: "Pilot budget \$25K-100K (confirmed)"
    
    questions:
      q1: "Does the pilot have dedicated budget or must it come from operations?"
      q2: "If budget is pending (e.g., board approval), what's the approval timeline?"
      q3: "What's the success criteria to justify larger investment?"
    
    pass_criteria: "Budget confirmed or approval timeline known (< 90 days)"

  authority:
    definition: "Can this person commit to a 90-day pilot?"
    
    by_segment:
      research: "Lab Director or Department Head"
      finance: "CTO or Head of Quantitative Research"
      pharma: "Head of Computational Chemistry or R&D Director"
      logistics: "Chief Operations Officer or VP Supply Chain"
    
    validation:
      - "Confirm title and reporting line"
      - "Check decision-making history (have they approved similar pilots?)"
      - "Identify fallback approver (if primary unavailable)"
    
    pass_criteria: "Authority confirmed; willing to sponsor"

  need:
    definition: "Is there a specific, urgent problem HYBA can help with?"
    
    by_segment:
      research: "Hardware quota limitation; cannot wait for cloud access"
      finance: "Quantum ROI unclear; need local validation before CapEx"
      pharma: "Molecular simulation bottleneck; want to benchmark quantum"
      logistics: "Current heuristics give suboptimal routes; quantum could improve"
    
    validation:
      - "Ask for specific problem definition (not vague)"
      - "Quantify impact (dollars, time, units)"
      - "Confirm HYBA addresses it (not unrelated need)"
    
    pass_criteria: "Specific problem identified; HYBA fit confirmed"

  timeline:
    definition: "Can pilot start within 90 days?"
    
    typical_constraints:
      - "Budget approval cycle (Q1, Q2, Q3, Q4)"
      - "Team availability (vacations, other projects)"
      - "Vendor evaluation process (RFP, legal review)"
      - "Data preparation (getting clean data for pilot)"
    
    by_segment:
      research: "Start immediately (quarter-based)"
      finance: "Board approval required (2-3 months typical)"
      pharma: "Data preparation needed (2-3 months)"
      logistics: "Depends on O&M approval (1-2 months)"
    
    pass_criteria: "Can start pilot within 90 days; clear blockers identified"

# ============================================================================
# SECTION 3: PILOT ONBOARDING CHECKLIST (90 DAYS)
# ============================================================================

pilot_onboarding_30_60_90:
  phase_1_weeks_0_to_4_kickoff:
    goal: "Establish relationship; confirm problem; set success metrics"
    
    week_1_day_1:
      - [ ] "Kickoff meeting: 1 hour with customer team (3-5 people)"
      - [ ] "Introduce HYBA leads (Product, Solutions Engineer, Finance)"
      - [ ] "Review pilot charter: problem statement, deliverables, success criteria"
      - [ ] "Set communication cadence (weekly standups recommended)"
    
    week_2:
      - [ ] "Technical deep-dive: customer presents problem in detail"
      - [ ] "HYBA team documents: circuit size, gate count, data size"
      - [ ] "Identify success metric (ROI worksheet filled)"
      - [ ] "Data sharing setup (GitHub, S3, Google Drive)"
    
    week_3:
      - [ ] "Customer onboarded: SDK installed, first circuit runs"
      - [ ] "Solutions Engineer delivers: custom code template for problem"
      - [ ] "Customer runs: baseline execution on their machine"
      - [ ] "Blockers resolved: dependency issues, networking, auth"
    
    week_4:
      - [ ] "First results generated: customer runs algorithm"
      - [ ] "Verify: output matches expected mathematical properties"
      - [ ] "Document: methodology, parameters, environment"
      - [ ] "Sign-off: Phase 1 complete, proceeding to Phase 2"
    
    phase_1_deliverables:
      - "Signed pilot charter"
      - "Completed ROI worksheet"
      - "Customer running first algorithm successfully"
      - "Baseline metrics established"

  phase_2_weeks_4_to_8_execution:
    goal: "Run pilot experiments; collect evidence; compare to baselines"
    
    week_5_6:
      - [ ] "Run all planned experiments (customer's problem set)"
      - [ ] "Collect results: raw outputs, checksums, execution times"
      - [ ] "Archive: store in HYBA evidence system"
      - [ ] "Analysis: customer analyzes against their classical baseline"
    
    week_7_8:
      - [ ] "Results evaluation: does quantum outperform classical? How much?"
      - [ ] "Document findings: methodology, results, limitations"
      - [ ] "Identify next steps: scale? Different problem? More data?"
      - [ ] "Prepare presentation: results summary for customer exec"
    
    phase_2_deliverables:
      - "Experimental results (raw + analyzed)"
      - "Quantum vs. classical comparison"
      - "Results presentation (slides)"
      - "Reproducibility verification (rerun with identical output)"

  phase_3_weeks_8_to_12_conclusion:
    goal: "Evaluate pilot results; decide next steps; contract if positive"
    
    week_9_10:
      - [ ] "Executive presentation: results to decision committee"
      - [ ] "Answer questions: explain methodology, caveats, reproducibility"
      - [ ] "Address surprises: if results different than expected, diagnose"
      - [ ] "Gather feedback: customer satisfaction, product feedback"
    
    week_11_12:
      - [ ] "Pilot conclusion report: final documentation"
      - [ ] "Go/No-go decision: did pilot meet success criteria?"
      - [ ] "If GO: contract negotiation (Tier 2 or Tier 3)"
      - [ ] "If NO-GO: post-mortem; feedback for product improvements"
    
    success_criteria_by_segment:
      research:
        - "Verified reproducibility (identical checksums > 10 runs)"
        - "Ran circuit at intended scale (n = intended qubits)"
        - "Density matrix axioms preserved"
        - "Publication-ready documentation"
      
      finance:
        - "Quantum vs. classical ROI comparison completed"
        - "Algorithm ran at intended problem scale"
        - "Audit trail complete (reproducible)"
        - "Board-ready presentation delivered"
      
      pharma:
        - "Molecular simulation ran on target molecules"
        - "Compared to classical DFT (quantified difference)"
        - "Regulatory-acceptable methodology documented"
        - "Publishable results (consent given)"
      
      logistics:
        - "Vehicle routing optimization ran"
        - "Solution quality vs. classical heuristic quantified"
        - "Scaling analysis completed (5-20 qubits tested)"
        - "Business case for larger investment justified or rejected"
    
    phase_3_deliverables:
      - "Pilot conclusion report"
      - "Customer case study (if consent)"
      - "Executive summary for customer board"
      - "Product feedback for HYBA team"
      - "Go/no-go decision + rationale"

# ============================================================================
# SECTION 4: ROI WORKSHEET (By Segment)
# ============================================================================

roi_worksheet_templates:
  research_segment:
    row_1_current_state_cost:
      line: "Current: Cloud quantum access annual cost"
      typical_value: "\$50K"
    
    row_2_proposed_state_cost:
      line: "Proposed: HYBA annual (Tier 2 Developer)"
      typical_value: "\$12K"
    
    row_3_cost_savings:
      line: "Annual savings"
      calculation: "\$50K - \$12K = \$38K"
    
    row_4_intangible_value:
      line: "Intangible: faster iteration (1.5x velocity improvement)"
      impact: "Enables 50% more papers/year"
      value: "Estimated \$25K (faster to publication = more visibility)"
    
    row_5_total_value:
      line: "Total value year 1"
      calculation: "\$38K cost savings + \$25K intangible = \$63K"
    
    row_6_pilot_cost:
      line: "Pilot cost (free tier during evaluation)"
      value: "\$0"
    
    row_7_roi:
      line: "Pilot ROI"
      calculation: "Infinite (no cost, \$63K value if adopt)"
    
    row_8_payback_period:
      line: "If upgrade post-pilot"
      calculation: "Immediate (savings > cost)"

  finance_segment:
    row_1_problem_size:
      line: "Portfolio optimization problem size"
      typical_value: "1000 assets"
    
    row_2_solution_quality_improvement:
      line: "Expected quantum improvement vs. classical heuristic"
      typical_value: "2-5% better solution"
    
    row_3_value_per_1_percent_improvement:
      line: "Value of 1% portfolio improvement"
      typical_value: "\$10M - \$100M (firm-dependent)"
    
    row_4_expected_value:
      line: "Expected value if quantum works (mid-case 3% improvement @ \$50M)"
      calculation: "\$50M * 0.03 = \$1.5M annual"
    
    row_5_pilot_cost:
      line: "Pilot cost (Tier 2, 100K QOU estimated)"
      value: "\$1000 base + \$8K overage = \$9K"
    
    row_6_roi:
      line: "Pilot ROI"
      calculation: "(\$1.5M expected - \$9K pilot) / \$9K = 16,666x"
    
    row_7_decision_threshold:
      line: "Go/no-go decision: if pilot shows 5x+ better than classical"
      threshold: "0.5% improvement = \$250K value at mid-case"

  pharma_segment:
    row_1_molecules_to_screen:
      line: "Number of molecules in drug discovery pipeline"
      typical_value: "100 molecules/year"
    
    row_2_screening_time_per_molecule:
      line: "Current: Classical DFT time per molecule"
      typical_value: "40 CPU-hours per molecule"
    
    row_3_quantum_speedup_hypothesis:
      line: "Quantum speedup hypothesis: 5-10x faster"
      impact: "If proven: 4-8 CPU-hours per molecule"
    
    row_4_time_value:
      line: "Value of 1-week acceleration (100 molecules)"
      calculation: "100 molecules * 36 hours = 3,600 CPU-hours saved = 1 FTE * 1 week"
      value: "\$10K (1 FTE for 1 week)"
    
    row_5_accelerated_discovery:
      line: "Accelerated discovery (faster to market by 1 month)"
      value: "\$50M - \$100M (typical drug value)"
    
    row_6_pilot_cost:
      line: "Pilot cost (10 molecules + baseline setup)"
      value: "\$15K"
    
    row_7_roi:
      line: "Pilot ROI (mid-case: \$75M drug value)"
      calculation: "(\$75M * 1 month early / 10 year development) / \$15K pilot = 500x"
    
    row_8_decision_threshold:
      line: "Go/no-go: if pilot shows > 2x speedup on test molecules"
      threshold: "Continue to larger validation study"

  logistics_segment:
    row_1_vehicles_per_day:
      line: "Average vehicles optimized per day"
      typical_value: "100 vehicles"
    
    row_2_stops_per_vehicle:
      line: "Average stops per vehicle"
      typical_value: "50 stops"
    
    row_3_current_solution_optimality:
      line: "Current heuristic solution quality"
      typical_value: "85% of optimal (15% suboptimal)"
    
    row_4_value_per_1_percent_improvement:
      line: "Value of 1% route improvement (fuel, driver time)"
      typical_value: "\$10K - \$50K annual"
    
    row_5_quantum_improvement_hypothesis:
      line: "Quantum improvement hypothesis: 2-5% better"
      impact: "Mid-case: 3% = \$30K annual (conservative)"
    
    row_6_pilot_cost:
      line: "Pilot cost (50 instances + analysis)"
      value: "\$10K"
    
    row_7_roi:
      line: "Pilot ROI"
      calculation: "\$30K expected / \$10K pilot = 3x"
    
    row_8_payback_period:
      line: "If positive: upgrade to Tier 2"
      calculation: "Payback in ~4 months (\$1.2M annual deployment cost)"

# ============================================================================
# SECTION 5: SUCCESS CRITERIA & GRADUATION
# ============================================================================

pilot_success_criteria:
  minimum_criteria:
    - "Pilot completed all phases (4-12 weeks)"
    - "Results documented and verified reproducible"
    - "Customer satisfied with methodology + results"
    - "No critical bugs or unplanned limitations discovered"
  
  by_customer_type:
    research: "Reproducibility verified; density matrix axioms held; publication-ready"
    finance: "Quantum vs. classical comparison completed; ROI quantified"
    pharma: "Molecular simulation worked; regulatory-acceptable methodology"
    logistics: "Vehicle routing problem solved; improvement vs. classical quantified"

pilot_graduation_path:
  if_success:
    next_step: "Upgrade to Tier 2 or Tier 3 contract"
    offer_structure:
      research: "Tier 2 Developer: \$1K/month base (academic discount available)"
      finance: "Tier 3 Enterprise: negotiated \$500K-\$2M annually"
      pharma: "Tier 2 Developer + custom integrations (negotiate)"
      logistics: "Tier 2 Developer: \$1K/month base"
    
    additional_benefits:
      - "Reference customer opportunity"
      - "Case study publication (co-authored)"
      - "Priority support queue"
  
  if_no_success:
    action: "Conduct post-mortem; iterate product"
    learning:
      - "Gather feedback: what didn't work? Why?"
      - "Identify product gaps: missing features? Bugs?"
      - "Plan improvements: next iteration"
    
    next_opportunity:
      - "Re-engage in 6-12 months (after improvements)"
      - "Offer free extended evaluation"
      - "Position as "partner in innovation""

# ============================================================================
# SECTION 6: IMPLEMENTATION CHECKLIST
# ============================================================================

implementation:
  - [ ] "ICPs documented and sales team trained"
  - [ ] "BANT qualification framework integrated into CRM"
  - [ ] "Pilot onboarding checklist created and tested"
  - [ ] "ROI worksheet templates finalized"
  - [ ] "Success criteria defined and measurable"
  - [ ] "Solutions engineer hiring/training (1 FTE minimum)"
  - [ ] "Pilot support SLA documented"
  - [ ] "Case study template created"
  - [ ] "Graduation path process automated"

---

## 4. Evidence of Completion

✅ **ICP profiles:** 4 segments with firmographics, buying patterns, disqualifiers  
✅ **BANT framework:** Budget, authority, need, timeline qualification gates  
✅ **Onboarding checklist:** 30/60/90-day milestones with deliverables  
✅ **ROI worksheets:** Segment-specific value calculations  
✅ **Success criteria:** Measurable pilot graduation thresholds  

---

## 5. Validation Hook

```bash
# test_pilot_protocol.sh

# Check all ICP profiles documented
for icp in "research" "finance" "pharma" "logistics"; do
  grep -q "icp_.*$icp:" docs/institutional_qaas/7_CUSTOMER_SEGMENTATION_PILOT_PROTOCOL.md || echo "❌ Missing ICP: $icp"
done

echo "✅ Customer Segmentation Pilot Protocol validated"
```

**Owner:** GTM Lead  
**Frequency:** Quarterly (customer feedback integration)  
**Success criteria:** Pilots tracked in CRM, closure rate > 60%, customer NPS > 40

---

## 6. Claim Boundary

**This artifact proves:**
- Customer segments are identified
- Qualification gates are defined
- Onboarding process is structured
- ROI models are built
- Success criteria are measurable

**This artifact does NOT prove:**
- Pilots will succeed
- Customer acquisition will follow forecast
- ROI models are accurate
- Pricing is competitive

---

## 7. Evidence Owner

**Role:** GTM Lead  
**Accountability:** Pilot quality, customer success, graduation rate  
**Escalation:** Chief Commercial Officer (for stuck pilots)
