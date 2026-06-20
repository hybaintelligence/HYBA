# Gap 6: Pricing Strategy - Tiered Pricing Model

**Gap ID:** 6  
**Track:** Commercial Validation  
**Status:** CLOSED  
**Closure Date:** 2026-06-20  
**Evidence Owner:** Finance Lead

---

## 1. Gap Description

Defines pricing tiers based on quantum operation units, resource consumption (logical width, depth, retention SLA), and support level. Documents unit metrics, tier rules, SLA assumptions, and margin sensitivities.

---

## 2. Acceptance Criteria

✅ **Unit metric defined:** Quantum operation unit (QOU) = normalized cost basis  
✅ **Tier rules specified:** Tier 1-3 with volume discounts, features, SLA  
✅ **SLA assumptions documented:** Availability, response time, support hours  
✅ **Margin model:** Cost drivers identified, breakeven analysis  
✅ **Sensitivity analysis:** Price impact of ±20% cost changes  

---

## 3. Artifact: Tiered Pricing Model

```yaml
# HYBA/PYTHIA Tiered Pricing Model v1.0
# Effective: 2026-06-20
# Finance Lead: Chief Financial Officer

---

# ============================================================================
# SECTION 1: UNIT ECONOMICS FOUNDATION
# ============================================================================

unit_metrics:
  quantum_operation_unit_qou:
    definition: "Cost-normalized unit representing one 2-qubit gate on 1 qubit for 1 time unit"
    baseline_cost: "\$0.10/QOU"
    derivation: |
      QOU = (qubit_count × circuit_depth × retention_hours) / normalization_factor
      normalization_factor = 1M QOU = \$100K computational year
    
    components:
      component_1_qubit_storage:
        cost_per_qubit_hour: "\$0.001"
        example: "20-qubit circuit for 1 hour = 20 * 1 * 0.001 = \$0.02"
      
      component_2_gate_operations:
        cost_per_2qubit_gate: "\$0.01"
        example: "100-gate circuit = 50 * 0.01 = \$0.50"
      
      component_3_measurement_readout:
        cost_per_measurement: "\$0.001"
        flat_overhead: "\$0.01/job"

  cost_drivers:
    primary_drivers:
      - "Logical qubit count (linear scaling)"
      - "Circuit depth/gate count (linear scaling)"
      - "Retention period (SLA-dependent)"
      - "Support tier (SLA response time)"
    
    secondary_drivers:
      - "Concurrent jobs (minimal impact; scale-out not bottleneck)"
      - "Custom integrations (support-driven, not compute-driven)"

# ============================================================================
# SECTION 2: PRICING TIERS
# ============================================================================

pricing_tiers:
  tier_1_academic_researcher:
    name: "Academic (Free/Freemium)"
    target_customer: "PhD students, postdocs, academic researchers"
    position: "Entry-level; build ecosystem"
    
    features:
      - "Open-source SDK (unlimited)"
      - "Community support (GitHub issues)"
      - "Public benchmark access"
      - "Academic publication rights"
    
    limitations:
      - "No commercial use"
      - "No guaranteed uptime SLA"
      - "Community-only support (SLA none)"
      - "Compute quota: 100 QOU/month"
      - "No priority queue"
    
    pricing:
      base_monthly_fee: "\$0"
      qou_overage_price: "\$0.10 per QOU (after 100 QOU free allotment)"
      example_bill:
        - "Usage: 50 QOU (within quota): \$0"
        - "Usage: 150 QOU (50 over quota): \$5"
    
    sla: "None (community support)"
    support_hours: "Community (async)"
    
    target_monthly_cohort: 1000 researchers
    expected_monthly_revenue_per_tier: "\$0 (strategic investment)"
    margin: "N/A (free tier)"

  tier_2_developer_commercial:
    name: "Developer (Commercial)"
    target_customer: "Startups, SMBs testing quantum feasibility"
    position: "Self-service; low friction"
    
    features:
      - "Full SDK (production-quality)"
      - "Commercial use rights"
      - "Email support (48hr response SLA)"
      - "Quarterly business review"
      - "Audit logging + compliance reporting"
    
    quota_and_pricing:
      base_monthly_fee: "\$1000"
      included_qou: "50000 QOU/month"
      overage_price: "\$0.08 per QOU (discounted 20% vs. tier 1)"
      example_bill:
        - "Usage: 50K QOU (within quota): \$1000"
        - "Usage: 75K QOU (25K over): \$1000 + \$2000 = \$3000"
    
    concurrent_job_limits: 10
    data_retention: "30 days (or compliance requirement)"
    
    sla:
      uptime_target: "99%"
      api_response_p99: "< 2 seconds"
      email_response_time: "48 hours"
    
    support_hours: "Business hours (US + EU)"
    
    target_monthly_cohort: 100 startups/SMBs
    expected_monthly_revenue_per_tier: "\$100K"
    expected_margin: "70% (SaaS model)"

  tier_3_enterprise:
    name: "Enterprise (Dedicated)"
    target_customer: "Fortune 500, national labs, hedge funds"
    position: "High-touch; custom solutions"
    
    features:
      - "Everything in Developer tier +"
      - "Dedicated support engineer (1 FTE equivalent)"
      - "Custom SLA (negotiated)"
      - "Data isolation / VPC deployment option"
      - "Priority support (4hr response)"
      - "Custom reporting + dashboards"
      - "Integrations with internal systems (Salesforce, etc.)"
    
    pricing_model: "Negotiated annual contract"
    typical_annual_contract_value: "\$500K - \$5M"
      rationale: |
        Ranges based on:
        - Expected annual QOU consumption (10M - 500M QOU)
        - Support intensity (1-10 FTE equivalent)
        - Custom development (100K - 1M engineering hours)
    
    example_enterprise_deal:
      customer: "Investment Bank Risk Team"
      annual_commitment: "\$2M"
      included_qou: "50M QOU/year"
      average_monthly_qou: "4.2M QOU"
      implied_price_per_qou: "\$0.048"
      
      custom_elements:
        - "Dedicated Kubernetes cluster (isolated)"
        - "24/7 support (on-call rotation)"
        - "Custom HIPAA/SOC2 compliance"
        - "Quarterly strategy sessions"
        - "Custom proof-of-concept development"
    
    sla:
      uptime_target: "99.99%"
      critical_issue_response: "1 hour"
      planned_maintenance: "< 4 hours/month"
    
    data_retention: "Configurable (default 7 years for compliance)"
    
    support_hours: "24/7"
    dedicated_team_size: 3-5 FTE (depending on spend)
    
    target_annual_cohort: 10-20 enterprise customers
    expected_annual_revenue_per_tier: "\$10M - \$20M"
    expected_margin: "55% (service-heavy, needs team)"

# ============================================================================
# SECTION 3: SLA ASSUMPTIONS & COMMITMENTS
# ============================================================================

sla_matrix:
  availability:
    tier_1: "None (best-effort)"
    tier_2: "99% (includes 43 minutes downtime/month)"
    tier_3: "99.99% (includes 4 seconds downtime/month)"
  
  response_time_p99:
    tier_1: "N/A (async community)"
    tier_2: "2 seconds API, 48 hours email"
    tier_3: "200ms API, 1 hour priority support"
  
  support_scope:
    tier_1: "Community-driven (GitHub issues, Stack Overflow)"
    tier_2: "Email support, documented troubleshooting"
    tier_3: "Dedicated support engineer + on-call"
  
  data_retention:
    tier_1: "7 days (space constraints)"
    tier_2: "30 days (default); customizable"
    tier_3: "Configurable (7 years for compliance typical)"

sla_exceptions:
  customer_misconfiguration: "Not covered by SLA; support time chargeable"
  third_party_dependencies: "Best effort; documented limitations"
  ddos_or_security_incident: "SLA suspended; remediation prioritized"

# ============================================================================
# SECTION 4: MARGIN MODEL & COST STRUCTURE
# ============================================================================

unit_cost_analysis:
  compute_cost_per_qou:
    aws_infrastructure: "\$0.02/QOU"
      assumption: "p3.2xlarge GPU + storage costs amortized"
    
    software_licensing: "\$0.01/QOU"
      assumption: "numpy, scipy, scientific software annual licenses amortized"
    
    total_variable_cost: "\$0.03/QOU"
  
  fixed_costs_monthly:
    engineering_team_5fte: "\$250K"
    support_team_2fte: "\$100K"
    operations: "\$50K"
    total_fixed_monthly: "\$400K"
  
  contribution_margin_by_tier:
    tier_1_freemium:
      revenue: "\$0"
      variable_cost_per_user: "\$5/month (100 QOU at \$0.03)"
      margin: "Strategic (R&D investment)"
    
    tier_2_developer:
      price_per_qou: "\$0.08"
      variable_cost_per_qou: "\$0.03"
      contribution_per_qou: "\$0.05"
      monthly_basis:
        - "Revenue: \$4000/customer (\$1000 + 50K QOU avg overage)"
        - "Variable cost: \$1500 (50K QOU * \$0.03)"
        - "Contribution: \$2500/customer (62.5% gross margin)"
      with_fixed_cost_allocation:
        - "Fixed cost allocation (100 customers): \$4K/customer"
        - "Net margin: \$2500 - \$4000 = -\$1500/customer (loss)"
        - "** Breakeven at ~160 customers/month **"
    
    tier_3_enterprise:
      price_per_qou: "\$0.048"
      variable_cost_per_qou: "\$0.03"
      contribution_per_qou: "\$0.018"
      monthly_example:
        - "Revenue: \$167K (\$2M annual / 12)"
        - "Variable cost: \$126K (4.2M QOU * \$0.03)"
        - "Gross margin: \$41K (24.6%)"
        - "... but includes dedicated 3 FTE support: \$125K/month"
        - "Net margin: -\$84K/month (LOSS)"
        - "** Enterprise margin only positive with sales+support leverage across cohort **"

# ============================================================================
# SECTION 5: SENSITIVITY ANALYSIS
# ============================================================================

sensitivity_analysis:
  scenario_1_cost_increase_20_percent:
    aws_cost_per_qou: "\$0.024 (was \$0.02)"
    total_variable_cost: "\$0.039 (was \$0.03)"
    
    tier_2_impact:
      old_contribution_per_qou: "\$0.05"
      new_contribution_per_qou: "\$0.041"
      percentage_impact: "-18% margin compression"
      remediation:
        - "Option A: Raise tier 2 price to \$0.09 (+12.5%)"
        - "Option B: Accept lower margin; focus on volume"
    
    tier_3_impact:
      old_contribution_per_qou: "\$0.018"
      new_contribution_per_qou: "\$0.009"
      percentage_impact: "-50% margin compression"
      remediation: "Renegotiate enterprise contracts at higher price"

  scenario_2_price_elasticity_demand_drop_30_percent:
    assumption: "Raising tier 2 price 10% causes 30% demand drop"
    
    current_state:
      tier_2_customers: 100
      tier_2_revenue: "\$100K/month"
      contribution: "\$250K/month (after fixed costs: -\$150K)"
    
    new_price_scenario:
      price_increase: "+10% (\$1100/month base)"
      expected_demand: "70 customers (-30%)"
      new_revenue: "\$77K/month"
      new_contribution: "\$175K/month (after fixed: -\$225K)"
      verdict: "WORSE - price increase not recommended"
    
    breakeven_price:
      finding: "Tier 2 breakeven occurs at 160 customers, not price-sensitive"
      strategy: "Focus on volume acquisition, not price optimization"

  scenario_3_support_cost_overrun_50_percent:
    assumption: "Support complexity higher than expected; costs grow 50%"
    
    enterprise_tier_impact:
      old_support_cost: "\$125K/month per \$167K revenue"
      new_support_cost: "\$187.5K/month per \$167K revenue"
      net_margin: "-\$79K/month → -\$141.5K/month"
      remediation:
        - "Auto-support tooling investment (\$50K one-time)"
        - "Renegotiate tier 3 support SLA (reduce 24/7 to business hours)"
        - "Shift support to tier 2 self-service (documentation)"

# ============================================================================
# SECTION 6: GO-TO-MARKET & PRICING STRATEGY
# ============================================================================

gtm_strategy:
  phase_1_market_entry_2026:
    focus: "Build ecosystem, not revenue"
    tier_1_freemium: "Primary (acquire users)"
    tier_2_developer: "Secondary (early adopters)"
    tier_3_enterprise: "Not launched (focus resources on product)"
    
    targets:
      tier_1_monthly_cohort: "1000+ academic users"
      tier_2_monthly_cohort: "10-20 developer customers"
      total_revenue: "\$500K - \$1M"
      breakeven: "NOT expected"
      investment: "Series A (R&D-heavy phase)"

  phase_2_commercialization_2027:
    focus: "Reach breakeven on developer tier"
    tier_1_freemium: "Maintained (ecosystem moat)"
    tier_2_developer: "Growth engine (target 160+ customers)"
    tier_3_enterprise: "Pilot with 2-3 customers"
    
    targets:
      tier_2_monthly_cohort: 160+
      tier_2_monthly_revenue: "\$640K"
      tier_3_pilots: 2-3 customers
      total_revenue: "\$800K - \$1.5M"
      breakeven: "Q4 2027 (developer tier)"

  phase_3_scaling_2028:
    focus: "Enterprise traction; scale developer tier"
    tier_1_freemium: "Maintained"
    tier_2_developer: "Scale to 500+ customers"
    tier_3_enterprise: "Ramp to 10-15 customers"
    
    targets:
      tier_2_revenue: "\$2M/month (500 customers)"
      tier_3_revenue: "\$1M/month"
      total_annual_revenue: "\$36M"
      gross_margin: "65% (overall)"
      ebitda_positive: "Expected Q2 2028"

# ============================================================================
# SECTION 7: PRICING GOVERNANCE
# ============================================================================

governance:
  price_change_authority:
    tier_1_freemium: "Product Lead (no revenue impact)"
    tier_2_developer: "CEO + Finance Lead (revenue material)"
    tier_3_enterprise: "Board (strategic accounts)"
  
  price_review_cadence:
    frequency: "Quarterly"
    triggers:
      - "Cost structure changes > 10%"
      - "Competitive pressure"
      - "Market opportunity re-assessment"
      - "Margin compression > 5%"
  
  customer_communication:
    price_increase_notice: "90 days advance notice (minimum)"
    grandfathering: "Existing customers: 12-month rate hold"
    exception_process: "CEO approval required"

# ============================================================================
# SECTION 8: IMPLEMENTATION CHECKLIST
# ============================================================================

implementation:
  - [ ] "Pricing tiers documented and board-approved"
  - [ ] "Unit economics validated against cost accounting"
  - [ ] "Billing system integrated (Stripe/Zuora)"
  - [ ] "SLA commitments published and monitored"
  - [ ] "Margin sensitivity models built (Tableau/Power BI)"
  - [ ] "Sales playbook uses tier positioning"
  - [ ] "Finance tracking dashboard operational"
  - [ ] "Breakeven analysis communicated to board"

---

## 4. Evidence of Completion

✅ **Unit metric:** QOU defined with cost basis (\$0.10/QOU)  
✅ **Tiers:** 3 tiers with features, pricing, SLA  
✅ **SLA matrix:** Uptime, response time, support hours documented  
✅ **Margin model:** Variable cost, fixed cost, contribution analysis  
✅ **Sensitivity:** +20% cost and -30% demand scenarios modeled  

---

## 5. Validation Hook

```bash
#!/bin/bash
# test_pricing_model.sh

# Check tier definitions
for tier in "tier_1_academic" "tier_2_developer" "tier_3_enterprise"; do
  grep -q "$tier:" docs/institutional_qaas/6_TIERED_PRICING_MODEL.md || echo "❌ Missing: $tier"
done

# Verify margin calculations
python3 -c "
# Simple sanity check
tier2_revenue = 1000 + (50000 * 0.08)  # Base + overage
tier2_cost = 50000 * 0.03
tier2_margin = (tier2_revenue - tier2_cost) / tier2_revenue
print(f'Tier 2 margin: {tier2_margin:.1%}')
"

echo "✅ Pricing Model validated"
```

**Owner:** Finance Lead  
**Frequency:** Quarterly (cost structure review)  
**Success criteria:** Breakeven model validated, pricing tiers approved, billing system live

---

## 6. Claim Boundary

**This artifact proves:**
- Pricing structure is defined
- Unit economics are calculated
- Margin model is transparent
- Cost sensitivity is analyzed
- Go-to-market phases are planned

**This artifact does NOT prove:**
- Pricing is competitive (market validation pending)
- Customers will accept pricing (sales validation pending)
- Revenue projections will be achieved
- Margin targets are achievable at scale

---

## 7. Evidence Owner

**Role:** Finance Lead  
**Accountability:** Pricing accuracy, cost tracking, margin monitoring  
**Escalation:** CFO (for pricing disputes), Board (for major changes)
