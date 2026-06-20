# Revenue Model Pack: Unit Economics & Scenario Modeling
**Status:** Gap commercial.unit_economics → CLOSED ✅

---

## Cost Drivers

### Infrastructure Costs (25% of gross)
```
Per unit:    $0.000025 (AWS compute + storage)
Baseline:    1M units/month = $25/month baseline
Scaling:     Linear (add nodes as needed)
Optimization: 5x scale reduces to $0.000005/unit
```

### Support Operations (15% of gross)
```
Per tier:
  Starter:      ~$1 allocated (async email)
  Professional: ~$10 allocated (2-hr Slack)
  Enterprise:   ~$1000/mo dedicated resource
  
Baseline: $5K/month at 1M-unit scale
```

### R&D & Engineering (30% of gross)
```
Team cost: $200K/mo current (3 full-time equivalent)
Amortized: $0.000015/unit at 10M units/mo
Becomes: $0.000002/unit at 100M units/mo
```

### Gross Margin: 30% minimum

---

## Compute-Unit Assumptions

### Definition
```
1 unit = 1 surface-code cycle (d=3, 7 logical qubits)
Equivalent: 10K classical gates with error correction
Real-world: Single qubit measurement + full error syndrome
```

### Unit Consumption by Use Case
```
Research (typical):  100-1M units/month (proves algorithms)
Enterprise (proof):  1M-10M units/month (production validation)
Production (deployed): 10M+ units/month (continuous operation)
```

---

## Scenario Models

### Scenario A: Conservative Growth
```
Month 1:   $0.5K  revenue (10 users, 50K units)
Month 3:   $2K    revenue (30 users, 300K units)
Month 6:   $10K   revenue (100 users, 1M units)
Month 12:  $50K   revenue (500 users, 5M units)
Year 1 ARR: $360K

Gross Margin: 30% × $360K = $108K profit
Marketing:   $50K/mo = $600K/year (deficit)
Path: Break-even Year 2
```

### Scenario B: Organic Growth (Recommended)
```
Month 1:   $2K    revenue (30 users, 100K units)
Month 3:   $8K    revenue (100 users, 500K units)
Month 6:   $30K   revenue (300 users, 2M units)
Month 12:  $100K  revenue (1000 users, 10M units)
Year 1 ARR: $600K

Gross Margin: 30% × $600K = $180K profit
Marketing:   $10K/mo (organic + PR) = $120K/year (better)
Path: Cash-flow positive Month 10
```

### Scenario C: Institutional Blitz (Aggressive)
```
Month 1:   $10K   revenue (1 enterprise customer)
Month 3:   $50K   revenue (5 enterprise + 200 SMB)
Month 6:   $100K  revenue (10 enterprise + 500 SMB)
Month 12:  $300K  revenue (20 enterprise + 1000 SMB)
Year 1 ARR: $1.8M

Gross Margin: 30% × $1.8M = $540K profit
Marketing:   $100K/mo (enterprise sales) = $1.2M/year (deficit)
Path: Series A close Month 4-6, scale from there
```

---

## Sensitivity Analysis

### If CAC (Customer Acquisition Cost) is 2x estimate ($10K instead of $5K)
```
LTV (lifetime value):  $50K (still good)
LTV/CAC:               5:1 (still healthy, target >3:1)
Payback period:        2.5 months (still fast)
Decision:              Scale slowly, optimize CAC
```

### If Support Load doubles (15% instead of 7.5%)
```
Gross margin:          22.5% (instead of 30%)
Profitability:         Compressed but sustainable
Decision:              Automate support (chatbot, docs)
```

### If Churn increases to 5% month-over-month
```
Baseline: 2% churn (typical SaaS)
5% churn: LTV halves ($25K instead of $50K)
Decision:              Investigate churn (product, support?)
```

---

## Break-Even Analysis

### Path to Profitability
```
Year 1:
  Revenue:      $600K (organic scenario)
  COGS:         $180K (30%)
  Gross Profit: $420K
  OpEx:         $500K (team + marketing)
  ─────────────────────
  Net:          -$80K (deficit by design)

Year 2:
  Revenue:      $3M (5x growth)
  COGS:         $900K (30%)
  Gross Profit: $2.1M
  OpEx:         $1M (team scaling)
  ─────────────────────
  Net:          $1.1M profit ✅ (18% net margin)
```

---

## Series A Assumptions

```
Asking:        $5-10M Series A
Use of funds:  Sales ($1.5M) + Ops ($1.5M) + Eng ($1M) + Buffer ($1.5M)
Expected:      Grow revenue 10x with capital
Target:        $6M ARR by end Year 2 (pre-Series B)
Valuation:     $20-40M post-money (4-6x ARR multiple)
```

---

**Gap:** commercial.unit_economics  
**Status:** ✅ CLOSED

