# 📊 HYBA Key Metrics Dashboard
**Real-Time Tracking for Investors, Board & Leadership**  
**Date:** June 20, 2026  
**Purpose:** Track progress to $10M ARR

---

## 🎯 Executive Dashboard (Update Weekly)

### **ARR & Revenue** 📈

```
WEEKLY UPDATES (Every Monday):

ARR (Annual Recurring Revenue):
└─ Week 0:    $0/mo × 12 = $0 ARR
└─ Week 2:    $5-10K/mo × 12 = $60-120K ARR
└─ Week 4:    $20-30K/mo × 12 = $240-360K ARR
└─ Month 2:   $50-150K/mo × 12 = $600K-1.8M ARR
└─ Month 3:   $100K+ /mo × 12 = $1.2M+ ARR
└─ Target (Year 1): $7.2M-24M ARR

MRR (Monthly Recurring Revenue):
└─ Week 0:    $0
└─ Week 2:    $5-10K ← First customers
└─ Week 4:    $20-30K ← Enterprise deal
└─ Month 2:   $50-150K ← Expansion
└─ Month 3:   $100-500K ← Scaling
└─ Target (Year 1): $600K-2M/mo

YTD Revenue (Track Cumulative):
└─ Month 1:   $20-50K
└─ Month 2:   $70-200K
└─ Month 3:   $150-700K
└─ Quarter 2: $400K-2M
└─ By EOY:    $7.2M-24M

Note: Update from analytics dashboard at:
      dashboards/revenue-analytics.json (local Grafana)
```

### **Customer Metrics** 👥

```
WEEKLY UPDATES (Every Monday):

Total Customers:
└─ Week 0:    0
└─ Week 2:    3-5 (paying)
└─ Week 4:    8-12 (paying) + 1 enterprise
└─ Month 2:   20-40 (paying)
└─ Month 3:   50-100 (paying)
└─ Target (Year 1): 200-500

Enterprise Customers (>$10K/mo):
└─ Week 0:    0
└─ Week 2:    0
└─ Week 4:    1 (first deal)
└─ Month 2:   2-3
└─ Month 3:   3-5
└─ Target (Year 1): 10-20

New Customers This Week:
└─ Track week-over-week churn/addition
└─ Target: Positive growth every week

Churn Rate (Monthly):
└─ Healthy: <2% month-over-month
└─ Track: Customers lost vs. added

NRR (Net Revenue Retention):
└─ Target: >100% (expansion revenue)
└─ Track: Revenue from existing customers growing
```

### **Unit Economics** 💰

```
MONTHLY UPDATES (End of Month):

CAC (Customer Acquisition Cost):
└─ Startup phase: $2-5K per customer (from beta outreach)
└─ Self-serve: $0-2K (organic)
└─ Enterprise: $5-10K (direct sales)
└─ Track: Total marketing spend / new customers

LTV (Lifetime Value):
└─ Calculation: Average annual value × 3-year retention
└─ Week 2: $5-10K (early data point)
└─ Month 2: $15-30K (more data)
└─ Month 3: $20-50K (stable estimate)
└─ Target: >$50K per customer

LTV/CAC Ratio:
└─ Healthy SaaS: >3:1
└─ Excellent SaaS: >5:1
└─ HYBA target: >5:1 (we should hit 5-10:1)
└─ Formula: LTV ÷ CAC

Gross Margin:
└─ Hosting cost: ~25% of revenue
└─ Operations: ~5% of revenue
└─ Gross margin: ~70% (after hosting + ops)
└─ Track: Revenue - Direct COGS

Payback Period:
└─ Formula: CAC ÷ (Monthly Revenue per Customer - COGS)
└─ Healthy: <12 months
└─ Excellent: <6 months
└─ HYBA target: 2-3 months
```

### **Operational Metrics** 🔧

```
DAILY UPDATES (Or continuous from Prometheus):

System Uptime:
└─ Target: 99.9% (4.4 hours downtime/month)
└─ Track: Prometheus alert + manual daily check
└─ Endpoint: curl http://[backend_url]/api/health

API Response Time (p99):
└─ Target: <100ms
└─ Track: Prometheus histogram
└─ Alert if: >500ms for >5 minutes

Deployment Frequency:
└─ Target: Daily or multiple times per week
└─ Track: GitHub Actions workflow runs
└─ Measure: Speed to fix bugs

Incident Response Time:
└─ Target: <30 minutes to detect, <1 hour to fix
└─ Track: Prometheus alerts → response
└─ Document: All incidents in runbook

Error Rate:
└─ Target: <0.1% (1 error per 1,000 requests)
└─ Track: Prometheus error counter
└─ Alert if: >1% error rate for >5 min

Database Health:
└─ Connection pool: Target 80% utilization max
└─ Query time (p95): <50ms
└─ Disk usage: <70% of allocated
└─ Backup status: Daily incremental
```

---

## 📋 Weekly Tracking Template

**Use this every Monday morning:**

```
WEEK [#] METRICS UPDATE (Date: _______)

ARR:
├─ Previous: $___K/mo × 12 = $___K ARR
├─ Current:  $___K/mo × 12 = $___K ARR
├─ Change:   +$___K/mo (+___%)
└─ Status:   ✅ On track / ⚠️ Behind / 🚀 Ahead

MRR:
├─ Previous: $___K
├─ Current:  $___K
├─ Change:   +$___K (+___%)
└─ Status:   ✅ On track / ⚠️ Behind / 🚀 Ahead

Customers:
├─ Previous: ___ customers
├─ Current:  ___ customers
├─ New this week: ___ (+___)
├─ Churned: ___ (-___)
└─ Net change: +___ customers

LTV/CAC:
├─ LTV: $___K
├─ CAC: $___K
├─ Ratio: ___:1
└─ Status: ✅ Healthy (>3:1) / ⚠️ Below target

Uptime:
├─ This week: ___%
├─ Rolling 30-day: ___%
├─ Incidents: ___ (all resolved)
└─ Status: ✅ Excellent / ⚠️ Check required

Notable Events:
├─ New enterprise customer: [Name]
├─ Bugs fixed: [Count]
├─ Features deployed: [List]
├─ Support tickets: [Count]
└─ Comments: [Any issues/wins]

Decision / Action Items:
├─ [ ] Need to hire [role]
├─ [ ] Need to fix [bug]
├─ [ ] Need to upsell [customer]
├─ [ ] Need to reach out [prospect]
└─ [ ] Next milestone: [Target]
```

---

## 🎯 Monthly Tracking Template

**Use this on the last Friday of each month:**

```
MONTH [Month Name] RESULTS

Revenue:
├─ MRR Start of Month: $___K
├─ MRR End of Month: $___K
├─ Growth: +___% ($___K)
├─ ARR Annualized: $___K
└─ YTD Revenue: $___K

Customers:
├─ Start of Month: ___ customers
├─ End of Month: ___ customers
├─ New: ___ customers
├─ Churned: ___ customers
├─ Net Growth: +___ customers (+__%)
├─ Enterprise: ___ customers
└─ Enterprise %: __% of revenue

Unit Economics:
├─ CAC (monthly): $___K
├─ LTV (estimated): $___K
├─ LTV/CAC: ___:1
├─ Gross Margin: ___%
├─ Payback: ___ months
└─ Status: ✅ Healthy / ⚠️ Needs work

Operations:
├─ Uptime: ___%
├─ Mean Response Time: ___ms
├─ Error Rate: ___%
├─ Incidents: ___ (severity: ___)
├─ Deployments: ___ (automated: __%)
└─ Status: ✅ Stable / ⚠️ Degraded

Team:
├─ Headcount: ___ people
├─ New hires: ___ this month
├─ Open roles: ___ (priority: ___)
└─ Status: ✅ On plan / ⚠️ Behind

Cash Runway:
├─ Monthly burn: $___K (ops + salaries)
├─ Monthly revenue: $___K
├─ Net burn: $___K (after revenue)
├─ Runway remaining: ___ months
└─ Status: ✅ Healthy / ⚠️ Tight / 🚀 Profitable

Highlights:
├─ Win: [Major customer or milestone]
├─ Challenge: [Main blocker]
├─ Next: [Priority for next month]
└─ Comments: [General thoughts]
```

---

## 📊 Quarterly Tracking Template

**Use this end of each quarter:**

```
Q[Quarter] RESULTS & PLAN

Financial Summary:
├─ Q-Start ARR: $___K
├─ Q-End ARR: $___K
├─ Q Growth: +___% ($___K)
├─ YTD ARR: $___K
├─ YoY Growth: +__% (if applicable)
└─ Projected Full Year ARR: $___K

Customer Summary:
├─ Q-Start Customers: ___
├─ Q-End Customers: ___
├─ Q Growth: +___ customers (+__%)
├─ Enterprise Customers: ___
├─ Churn Rate: __% avg
└─ NRR: __% (if >100%, excellent!)

Product Metrics:
├─ Features shipped: ___
├─ Bugs fixed: ___
├─ Performance improvement: ___% (p99 latency)
└─ Uptime: __% (4-hour downtime budget used)

Financial Health:
├─ Gross Margin: __% (target: >70%)
├─ Operating Expenses: $___K/month
├─ Path to Profitability: ___ months
└─ Runway: ___ months at current burn

Team:
├─ Headcount Growth: ___ people added
├─ Role: __ engineers, __ sales, __ ops, __ other
├─ Planned Q+1 Hires: ___ people
└─ Priority Gaps: [List]

Series A Readiness (Track Progress):
├─ ARR Milestone: $___K (target: $100K+ for strong raise)
├─ Enterprise Customers: ___ (target: 2-3)
├─ Patent Status: [Filed / Pending / Approved]
├─ SOC 2 Status: [Not started / In progress / Completed]
├─ Case Studies: ___ customers (target: 3+)
├─ Investor Meetings: ___ (intro + full meetings)
└─ Series A Timeline: [Expected closing month]

Key Risks & Mitigations:
├─ Risk 1: [Description]
│  └─ Mitigation: [Action]
├─ Risk 2: [Description]
│  └─ Mitigation: [Action]
└─ Risk 3: [Description]
   └─ Mitigation: [Action]

Next Quarter Priorities:
├─ [ ] Hit ARR target: $___K
├─ [ ] Reach ___ customers
├─ [ ] Close ___ enterprise deals
├─ [ ] Ship features: [List]
├─ [ ] Hire roles: [List]
└─ [ ] Milestone: [Series A / Expansion]
```

---

## 🎯 Targets by Milestone

### **Week 2: First Revenue**
```
✅ MRR: $5-10K
✅ Customers: 3-5 paying
✅ ARR (annualized): $60-120K
✅ First invoice generated
✅ Portal proven working
└─ Key metric: Revenue proves PMF
```

### **Week 4: Enterprise Proof**
```
✅ MRR: $20-30K
✅ Customers: 8-12 paying + 1 enterprise
✅ Enterprise ARR: $50-500K annualized from 1 deal
✅ First case study started
✅ LTV/CAC calculated: >3:1
└─ Key metric: Enterprise deal proves scalability
```

### **Month 2: Expansion**
```
✅ MRR: $50-150K
✅ Customers: 20-40 paying
✅ Enterprise: 2-3 customers
✅ ARR: $600K-1.8M annualized
✅ 3+ case studies completed
✅ LTV/CAC: 5-10:1 confirmed
└─ Key metric: Scaling proof
```

### **Month 3: Series A Ready**
```
✅ MRR: $100K-500K
✅ Customers: 50-100 paying
✅ Enterprise: 3-5 customers (20%+ of revenue)
✅ ARR: $1.2M-6M annualized
✅ 5+ case studies with ROI
✅ SOC 2 in progress
✅ Gross margin: 70% proven
✅ Unit economics: LTV/CAC 5-10:1
└─ Key metric: Series A metrics demonstrated
```

### **Year 1: Target ARR**
```
✅ MRR: $600K-2M
✅ Customers: 200-500 paying
✅ Enterprise: 10-20 customers (30%+ of revenue)
✅ ARR: $7.2M-24M
✅ Gross margin: 70%+ maintained
✅ Payback: 2-3 months proven
✅ NRR: >100% (expansion revenue)
✅ Series A: Closed ($5-10M)
└─ Key metric: Clear path to $10M+ ARR
```

---

## 💻 How to Track These Metrics

### **Option 1: Manual Tracking (Weekly)**
Use the templates above. Fill in every Monday morning. Share with leadership/board.

### **Option 2: Grafana Dashboard (Real-Time)**
All metrics automatically update in Grafana from Prometheus:
- Location: `http://localhost:3000` (or production endpoint)
- Dashboard: `revenue-analytics.json`
- Metrics: ARR, MRR, LTV/CAC, uptime, error rate

### **Option 3: Database Query (Advanced)**
```sql
-- Query current month revenue
SELECT SUM(actual_cost) as current_month_revenue
FROM workload_executions
WHERE EXTRACT(MONTH FROM executed_at) = EXTRACT(MONTH FROM NOW())
  AND EXTRACT(YEAR FROM executed_at) = EXTRACT(YEAR FROM NOW());

-- Query customer count
SELECT COUNT(DISTINCT tenant_id) as total_customers
FROM workload_executions
WHERE executed_at > NOW() - INTERVAL '30 days';

-- Query churn
SELECT 
  (customers_last_month - customers_this_month) / customers_last_month as churn_rate
FROM (
  SELECT COUNT(DISTINCT tenant_id) as customers_last_month FROM workload_executions
  WHERE executed_at > NOW() - INTERVAL '60 days' AND executed_at < NOW() - INTERVAL '30 days'
) last_month,
(
  SELECT COUNT(DISTINCT tenant_id) as customers_this_month FROM workload_executions
  WHERE executed_at > NOW() - INTERVAL '30 days'
) this_month;
```

---

## 🎯 Alert Thresholds

**Set up alerts if:**

```
REVENUE ALERT:
└─ If MRR drops >10% week-over-week → Investigate churn

CUSTOMER ALERT:
└─ If churn >3% in a week → Reach out to lost customers

QUALITY ALERT:
└─ If uptime <99.5% → Page on-call engineer
└─ If error rate >1% for 5 min → Page on-call engineer
└─ If response time p99 >500ms → Investigate performance

UNIT ECONOMICS ALERT:
└─ If LTV/CAC drops <3:1 → Review pricing/CAC strategy
└─ If Gross margin <60% → Investigate costs

OPERATIONAL ALERT:
└─ If deployment fails → Review CI/CD pipeline
└─ If database CPU >80% → Plan upgrade
└─ If disk usage >70% → Plan expansion
```

---

## 📞 Weekly Dashboard Review

**Every Monday 10am (30 min meeting):**

```
ATTENDEES: Founder, VP Ops, VP Sales (if relevant)

AGENDA (30 min):
├─ [5 min] Review metrics from last week
├─ [5 min] Discuss variances from plan
├─ [10 min] Identify blockers
├─ [5 min] Decide actions for this week
├─ [5 min] Update forecast for month
└─ [Async] Update board/investors if needed

OUTCOMES:
├─ [ ] Weekly metrics logged
├─ [ ] Blockers escalated
├─ [ ] Actions assigned (with owners)
└─ [ ] Next review scheduled
```

---

## 📈 What Success Looks Like

```
Week 2:  First revenue 💰 → "We're in business"
Week 4:  Enterprise deal 🎯 → "We can scale"
Month 2: Expansion 📈 → "Market wants this"
Month 3: Series A ready 🚀 → "Time to grow"
Year 1:  $7.2M-24M ARR 🏆 → "We won"
```

---

**Status:** Ready to track 📊  
**Next Step:** Fill in Week 0 metrics from June 20, 2026, then update weekly  
**Let's go to market.** 🚀

