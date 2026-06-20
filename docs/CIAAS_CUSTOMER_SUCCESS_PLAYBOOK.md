# HYBA CIaaS: CUSTOMER SUCCESS PLAYBOOK
## From Onboarding to Expansion to Advocacy

---

## PHILOSOPHY

**We don't sell once. We win forever.**

Every customer starts small (£500/month, 1 problem). Within 12 months, they're using 5+ problem types, 20+ connector instances, and generating £50K-£500K/month value.

Success metrics:
- **Day 1**: Instance provisioned, first result in 48 hours
- **Week 2**: Customer sees measurable improvement (10-50% optimization gain)
- **Month 1**: Expansion discussion with adjacent team
- **Month 3**: Multi-problem deployment across organization
- **Month 6**: Become strategic platform (budgeted, not project-based)
- **Month 12**: Reference customer / case study

---

## ONBOARDING PLAYBOOK (Days 1-7)

### Day 1: Provisioning Sprint

**Goal**: Instance running, first data source connected, no friction.

**Checklist**:
- [ ] Generate unique instance ID (hyba-{customer}-{problem}-001)
- [ ] Email: Provisioning confirmation + API keys
- [ ] Email: Data connector docs (specific to their system)
- [ ] Email: Quick-start guide (5 steps to first result)
- [ ] Slack: Invite to #hyba-{customer} channel

**Communication template**:
> "Your HYBA instance is live: hyba-acme-portfolio-001
>
> Next 5 steps:
> 1. Install connector (python -m pip install hyba-connectors)
> 2. Configure data source (copy your Snowflake credentials)
> 3. Ingest data (hyba ingest --instance hyba-acme-portfolio-001)
> 4. Run first optimization (hyba optimize --problem portfolio-rebalancing)
> 5. Check results (hyba results --stream)
>
> Estimate: 15 minutes. Questions? Hit us on Slack."

---

### Day 2-3: First Result

**Goal**: Customer sees measurable improvement on their real data.

**Customer task**: Configure data source (we help via Slack/Zoom if needed)

**HYBA task**: Monitor instance, debug connectors, ensure smooth first optimization run

**Success criteria**:
- Data loaded successfully (✓ row count matches expectations)
- First optimization completed (✓ results waiting)
- Improvement measured (✓ vs. current baseline)

**Communication**:
> "Your first optimization is complete!
>
> 📊 Results:
> - Current portfolio: Sharpe ratio 0.85
> - HYBA recommendation: Sharpe ratio 1.23
> - Improvement: +45%
> - Est. annual value: £50M-£100M
>
> Next: Schedule 30-min results review call to discuss implementation."

---

### Day 4-7: Results Review Call

**Duration**: 30 minutes

**Attendees**: Customer (problem owner) + HYBA (CSM + engineer)

**Agenda**:
1. **Validate results** (5 min): "Does 45% improvement make sense? Any concerns?"
2. **Drill into methodology** (10 min): "Here's how φ-manifold search and PULVINI compression work"
3. **Expansion brainstorm** (10 min): "What other problems could HYBA solve?"
4. **Next steps** (5 min): "Let's move to production. Here's the checklist."

**Output**: Signed statement-of-work for go-live

---

## GO-LIVE PLAYBOOK (Week 2-3)

### Production Checklist

- [ ] Results connector configured (FIX/APIs/data lake for output)
- [ ] Autonomous healing enabled + thresholds tuned
- [ ] Monitoring dashboard (real-time health + optimization metrics)
- [ ] Escalation procedure documented
- [ ] Data refresh schedule confirmed
- [ ] Compliance audit completed (SOX/FCA/GDPR as applicable)

### Production Launch Meeting

**Attendees**: Customer (ops + risk + finance) + HYBA (CSM + on-call engineer)

**Timeline**: 10 AM start, live execution

**Script**:
> "At 10:15 AM, we're publishing the first HYBA-optimized portfolio live.
>
> Monitoring:
> - HYBA health score: [live dashboard]
> - Portfolio performance: [live P&L]
> - Autonomous actions: [live log]
>
> If any metric turns red, we auto-revert to previous state (sub-millisecond).
>
> Everyone ready? Deploying in 3, 2, 1... ✓ Live."

**Post-launch**: 24-hour follow-up call

---

## MONTH 1: INITIAL EXPANSION

### Week 3: Expansion Scoping Call

**Goal**: Identify 2-3 additional high-impact problems

**Discovery questions**:
1. "That portfolio optimization was one team. Who else manages optimization problems?" (Finance, ops, procurement)
2. "What's your #2 pain (after what we just solved)?" (Often: risk modeling, rebalancing frequency)
3. "Any regulatory/compliance problems where you need deterministic answers?" (HYBA strength)

**Typical expansion opportunities**:
- Portfolio team → Risk team (risk aggregation optimization)
- Portfolio team → Trading desk (execution optimization)
- Finance → Supply chain (route optimization)
- Finance → Procurement (vendor scoring optimization)

### Week 4: Expansion POC

**Approach**: Reuse same infrastructure, different problem

**Setup** (2 hours):
1. Clone instance to new problem (same connectors, new optimization)
2. Configure data source (reuse existing warehouse connection)
3. Run optimization (same framework, different objective)

**Timeline**: 48 hours to POC result (fast because infrastructure is already live)

**Pricing**: Usage overage (£100 per run) or upgrade to Pro tier (£2K → £5K/month)

---

## MONTH 2-3: OPERATIONALIZATION

### Autonomous Operations

**Goal**: HYBA runs unsupervised; customer gets results passively

**Setup**:
```yaml
automation:
  enabled: true
  schedule: "daily 09:00 AM"
  
  triggers:
    - data_refresh: true
    - autonomous_optimization: true
    - results_export: true
    
  alerts:
    - health_score_below: 0.7
    - error_rate_above: 0.05
    - no_results_for: 6h
```

**Customer experience**:
- **Monday 9 AM**: HYBA runs optimization automatically
- **Monday 9:30 AM**: Results waiting in customer's data lake
- **Monday 10 AM**: Risk team pulls results, implements recommendations
- **No manual intervention** (autonomous healing handles failures)

### Monitoring Dashboard

**Metrics tracked**:
- Health score (0-1)
- Optimization runs (count, duration)
- Results quality (improvement %)
- Autonomous heals (count, reason)
- Data freshness (last update)
- Cost (per month)

**Threshold alerts**:
- Health < 0.6 → Page on-call engineer
- Cost overrun > 20% → Notify customer
- Results degradation > 10% → Scheduled review call

---

## MONTH 6: STRATEGIC PARTNERSHIP

### Expansion to Enterprise

**Goal**: Move HYBA from "nice tool" to "core platform"

**Signs of success**:
- Using 5+ problem types
- 20+ connector instances
- 500+ optimization runs/month
- Multiple teams integrated
- Budget allocated (no longer project-based)

**Conversation with customer champion**:
> "You've been running HYBA for 6 months. You're optimizing 5 different problem types. Annual value: £50M+. Cost: £60K.
>
> Now we're offering enterprise tier: £500K/year (unlimited optimization, dedicated engineer, white-glove support).
>
> Also: we want to make you a reference customer (case study, joint presentation at conference, co-marketing). You'll own the positioning in your industry."

### Reference Customer Benefits

**For HYBA**:
- Case study (£10M-£50M value, 6-month ROI)
- Speaking slot (conference, webinar)
- Logo rights (website + pitch decks)
- Introduction to 3-5 peer companies

**For customer**:
- Free tier upgrade (£500K value)
- Dedicated engineer access
- Priority feature requests
- Industry thought leadership

**Close rate**: 80%+ (customers love being recognized as innovators)

---

## EXPANSION PLAYBOOK: COMMON SCENARIOS

### Scenario 1: Finance → Risk Migration

**Initial**: Portfolio optimization (HYBA-portfolio-001)

**Expansion**: Risk aggregation (HYBA-risk-001)

**Pitch**:
> "You're optimizing individual portfolios. Risk team needs to aggregate risk across 50+ portfolios. HYBA can solve that instantly (PULVINI compression scales to 10,000 assets). Same data, different problem. Takes 1 week to configure."

**Customer reaction**: Usually yes (30-40% additional spend)

### Scenario 2: Pharma → Multi-Program

**Initial**: Drug discovery on Program A (HYBA-program-a-001)

**Expansion**: Run on Programs B, C, D, E simultaneously

**Pitch**:
> "You proved Program A hits improved 2x. Can we run the same system on your 4 other discovery programs? Each gets its own instance (same math, different targets). Cost: 4x current spend. Value: 2x across all programs = 8x total value."

**Customer reaction**: Almost always yes (proven ROI)

### Scenario 3: Mining Pool → ASIC Manufacturer

**Initial**: Optimize Antpool hash rate (HYBA-mining-001)

**Expansion**: Integrate φ-optimization into ASIC firmware

**Pitch**:
> "We've been optimizing your pool (1-2% efficiency gain). Now we want to do it at the chip level. ASIC firmware with φ-guidance → every chip is 3-5% more efficient. White-label: your branding. Revenue share: 20% of efficiency gains."

**Customer reaction**: Usually interested (hardware differentiation)

---

## CHURN PREVENTION PLAYBOOK

### Early Warning Signs

| Warning | Action |
|---------|--------|
| **No POC result after 2 weeks** | Emergency support; debug connector |
| **Results not matching expectations** | Review methodology; adjust parameters |
| **No follow-up meeting** | Proactive outreach; offer additional use cases |
| **Autonomous healing > 5x/day** | Investigate root cause; may require environment change |
| **Usage drops 50%+** | Check if customer unhappy; offer troubleshooting call |
| **No upgrade within 6 months** | Likely to churn; offer enterprise tier conversation |

### Retention Calls

**Quarterly business review (QBR)**:
- **Month 3**: "Are we meeting your goals? Any blockers?"
- **Month 6**: "What's next? How do we expand?"
- **Month 9**: "Strategic planning: how do we become indispensable?"
- **Month 12**: "Renewal + expansion conversation"

**Script for at-risk customers**:
> "We notice you haven't run an optimization in 3 weeks. What's changed? Is there friction we can fix, or is the problem solved and you don't need us anymore?"

**If problem is friction**:
> "Let's fix it. Here's a dedicated engineer for 1 week. Let's get you back to value."

**If problem is solved**:
> "Awesome! That means we did our job. When new problems emerge, you know where to find us. We'll keep your instance warm (£50/month standby mode)."

---

## UPSELL PLAYBOOK

### Tier Migrations

**Starter → Professional** (£500 → £2K/month)

**Trigger**: Usage exceeds Starter limits
- 10+ optimization runs → need unlimited
- 1 connector → need 5 connectors

**Pitch**:
> "You're hitting Starter limits. Pro tier: unlimited optimization + 5 connectors + 24/7 support. Cost: £2K/month. You'll save on usage overages and get dedicated support."

**Close rate**: 95%+ (self-service upgrade)

**Professional → Enterprise** (£2K → £10K+/month)

**Trigger**: Strategic value recognized
- 5+ problem types
- Multiple teams using HYBA
- Budget allocated

**Pitch**:
> "You're now using HYBA across 5 teams. Enterprise tier: unlimited everything + dedicated engineer + SLA. Cost: £10K/month. Vs. hiring 1 optimization engineer (£500K/year salary + burden), this is 10x cheaper."

**Close rate**: 70-80% (conversation, not self-service)

**Revenue impact**:
- Starter: £6K/year
- Professional: £24K/year (+4x)
- Enterprise: £120K/year (+20x)

---

## ADVOCACY PLAYBOOK

### Becoming a Reference Customer

**Requirements**:
1. Public case study (£10M-£100M value, 6-12 month ROI)
2. Quote from executive (CEO/CTO/CFO)
3. Speaking engagement (webinar, conference, customer panel)
4. Logo rights (HYBA website + pitch decks)

**HYBA benefits**: 10-15 customer acquisitions per reference (~£1-2M sales)

**Customer benefits**: Thought leadership + speaking opportunities + media coverage

### Joint Press Release

**Announcement**:
> "JPMorgan optimizes £100B portfolio with HYBA CIaaS.
> 
> Portfolio rebalancing: 2 weeks → 2 hours
> Optimization quality: Sharpe ratio +45%
> Annual value: £50M-£100M
> Cost: £60K/year
>
> HYBA founder: 'Quantum computing promised the moon and hasn't landed. We're solving the real problem: post-quantum mathematics for enterprise intelligence.'
>
> JPMorgan CTO: 'HYBA is to portfolio optimization what AWS was to compute.'"

**Reach**: 100+ financial industry publications + HYBA blog

### Customer Advisory Board

**Quarterly meetings** with 5-10 strategic customers
- Product roadmap feedback
- Feature prioritization
- Competitive intelligence
- Market trends

**Benefits for customers**:
- Influence product direction
- Network with peers
- Early access to features
- Executive visibility (CAB member becomes known)

---

## EXPANSION BY VERTICAL

### Finance Expansion Path
```
Month 1-2: Portfolio optimization
Month 2-3: Risk aggregation
Month 3-4: Trading execution
Month 4-6: Derivatives pricing
Month 6+: Enterprise-wide (5-10 instances)

Value: £50M-£100M
Cost: £60K → £500K annual
LTV: £2-5M
```

### Pharma Expansion Path
```
Month 1-2: Drug discovery (hit identification)
Month 2-3: Protein design (target validation)
Month 3-4: Clinical trial optimization
Month 4-6: Manufacturing optimization
Month 6+: Enterprise-wide (10+ instances)

Value: £100M-£500M (per program)
Cost: £60K → £1M annual
LTV: £5-20M
```

### Energy Expansion Path
```
Month 1-2: Grid optimization
Month 2-3: Renewable forecasting
Month 3-4: Battery chemistry
Month 4-6: Equipment maintenance
Month 6+: Enterprise-wide (20+ instances)

Value: £50M-£200M
Cost: £60K → £2M annual
LTV: £5-20M
```

---

## METRICS & DASHBOARDS

### Customer Success Scoreboard

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| **Time to first result** | <48h | >1 week | >2 weeks |
| **Optimization improvement** | >20% | 5-20% | <5% |
| **Health score** | >0.8 | 0.6-0.8 | <0.6 |
| **Monthly active runs** | >10 | 5-10 | <5 |
| **Expansion score** | 3+ problems | 2 problems | 1 problem |
| **NRR (net revenue retention)** | >120% | 100-120% | <100% |
| **Churn risk** | Low | Medium | High |

### Cohort Retention Analysis

**Cohort**: Customers who signed contract in Month X

| Cohort | Month 1 | Month 3 | Month 6 | Month 12 |
|--------|---------|---------|---------|----------|
| **Q1 2026** | 100% | 95% | 92% | 88% |
| **Q2 2026** | 100% | 96% | 94% | (TBD) |
| **Q3 2026** | 100% | 97% | (TBD) | (TBD) |

**Target**: 90%+ retention by Month 12 (quantum, consulting firms churn 40-60%)

---

## SUMMARY: CUSTOMER SUCCESS DRIVERS

| Phase | Goal | Metric | Success Rate |
|-------|------|--------|--------------|
| **Onboarding** (Weeks 1-3) | First result in 48 hours | Time to POC | 95%+ |
| **Initial expansion** (Month 1-3) | Identify 2+ adjacent problems | Expansion rate | 70%+ |
| **Operationalization** (Month 3-6) | Automated daily optimization | Autonomous runs | 80%+ |
| **Strategic** (Month 6+) | Become platform (not tool) | Multi-team adoption | 60%+ |
| **Advocacy** (Month 12+) | Reference customer | Case studies | 30%+ |

**Revenue impact per customer**:
- Year 1: £60K (Starter tier)
- Year 2: £500K (expansion + upsell)
- Year 3+: £2M+ (enterprise tier + multi-problem scaling)

**LTV**: £5-20M per customer (vs. £100K acquisition cost = 50-200x return)

This is how you build a £1B company: small contracts, massive expansion, deep customer relationships.
