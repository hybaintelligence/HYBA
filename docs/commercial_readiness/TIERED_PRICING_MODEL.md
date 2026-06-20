# Tiered Pricing Model
**Status:** Gap commercial.pricing → CLOSED ✅

---

## Unit Economics Foundation

### Compute Unit Definition
```
1 unit = 1 surface-code cycle on 1 logical qubit
Equivalent to: ~10K classical gates with error correction overhead
Real-world mapping: 
  - 1M units = Full quantum algorithm simulation (1000-qubit depth-100)
  - 1K units = Single error correction cycle verification
```

### Cost Structure
```
Infrastructure:      $0.000025/unit (AWS compute + storage)
Support operations:  $0.000010/unit (15% of gross)
R&D allocation:      $0.000015/unit (30% of gross)
────────────────────────────────────
Total cost:          $0.000050/unit
Gross margin:        60% (pricing at $0.0001/unit minimum)

Assumes: 1M units/month baseline, $50K/month ops
```

---

## Pricing Tiers

### Tier 1: Starter
```
Price:           $10/month
Monthly quota:   100K units
Per-unit cost:   $0.0001
SLA:             99% uptime (best effort)
Support:         Email (24hr response)
Use case:        Individual researchers, proof-of-concept
Minimum commit:  Month-to-month
```

### Tier 2: Professional
```
Price:           $80/month
Monthly quota:   1M units
Per-unit cost:   $0.00008
SLA:             99.5% uptime (guaranteed)
Support:         Email (2hr response)
Use case:        Small teams, production research
Minimum commit:  Annual preferred (month-to-month OK)
```

### Tier 3: Enterprise
```
Price:           Custom ($50K-$500K/month)
Monthly quota:   Unlimited
Per-unit cost:   $0.00005 (at 10M units)
SLA:             99.9% uptime (guaranteed)
Support:         Dedicated Slack + 1hr response
Features:        Audit logs, SOC 2, custom integrations
Use case:        Fortune 500, governments, unicorns
Minimum commit:  1-year contract
```

---

## SLA Assumptions

### Uptime Targets
```
Starter:      99%  = 7.2 hours downtime/month (acceptable)
Professional: 99.5% = 3.6 hours downtime/month (good)
Enterprise:   99.9% = 43 minutes downtime/month (excellent)
```

### Support Response Times
```
Starter:      24-hour email (async)
Professional: 2-hour email + Slack (sync)
Enterprise:   1-hour phone/Slack (dedicated)
```

---

## Revenue Projections (Year 1)

### Conservative Scenario
```
Month 1-2:  10 Starter @ $10 +  5 Professional @ $80   = $500/mo
Month 3-4:  20 Starter + 10 Professional + 1 Enterprise = $2K/mo
Month 5-6:  30 Starter + 25 Professional + 2 Enterprise = $5K/mo
Month 7-12: 50 Starter + 50 Professional + 5 Enterprise = $15K/mo average
────────────────────────────────────────────────────────
Year 1 total:     ~$80K (ramp from $500 to $15K/mo)
```

### Aggressive Scenario
```
Month 1-2:  50 Starter + 20 Professional + 1 Enterprise = $3K/mo
Month 3-4:  100 Starter + 50 Professional + 2 Enterprise = $8K/mo
Month 5-6:  150 Starter + 100 Professional + 5 Enterprise = $20K/mo
Month 7-12: 200 Starter + 150 Professional + 10 Enterprise = $50K/mo average
────────────────────────────────────────────────────────
Year 1 total:     ~$300K (ramp from $3K to $50K/mo)
```

---

## Margin Sensitivities

### If infrastructure costs 2x current estimate
```
Cost:           $0.0001/unit (not $0.00005)
Starter margin: 0% (break-even at $10/mo, 100K units)
Professional:   -20% (unsustainable)
Enterprise:     60% (still profitable)

Action: Raise Starter/Professional prices 50% OR optimize ops
```

### If support load is 2x estimate
```
Cost:           $0.00075/unit (not $0.0001)
Starter margin: -650% (impossible)
Professional:   -850% (impossible)
Enterprise:     -500% (unsustainable)

Action: Auto-support only for Starter tier; require professional support
```

### If we achieve 5x scale (5M units/mo baseline)
```
Cost:           $0.000025/unit (ops scale linearly)
Starter margin: 750% profit (price can drop)
Professional:   600% profit (or increase value)
Enterprise:     1000% profit (pricing negotiation needed)

Action: Drop Starter to $2/mo; raise Enterprise negotiation floor
```

---

## Tier Upgrade Path

```
Customer journey:
Day 1:     Sign up for Starter ($10/mo, 100K units)
Week 2:    Exhaust quota, upgrade to Professional ($80/mo, 1M units)
Month 2:   Growing team, need SLA guarantee + support
Month 4:   Production workload, move to Enterprise custom pricing
```

---

## Annual Discount Strategy

```
Starter:       -10% for annual commit ($9/mo equivalent)
Professional:  -15% for annual commit ($68/mo equivalent)
Enterprise:    -20% for multi-year commit ($40K/mo on $50K baseline)
```

---

**Gap:** commercial.pricing  
**Status:** ✅ CLOSED

