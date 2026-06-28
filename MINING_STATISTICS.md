# Mining Statistics: Empirical Evidence Analysis

**Date:** 2026-06-28  
**Status:** Statistical Framework  
**Classification:** Evidence Documentation  

---

## Executive Summary

This document provides the statistical framework for analyzing mining telemetry as evidence of the HYBA φ-resonance substrate. The claim under analysis:

> When the φ-resonance core is active, mining proposal quality improves from 14 mixed-confidence proposals to 6 high-confidence proposals, representing a statistically significant improvement over baseline random search.

---

## 1. The Null Hypothesis and Alternative

### 1.1 Hypotheses

**H₀ (Null Hypothesis):** The observed improvement from 14 mixed → 6 high-confidence proposals is due to random chance. The φ-resonance core provides no improvement over baseline mining heuristics.

**H₁ (Alternative Hypothesis):** The observed improvement is statistically significant and attributable to the φ-resonance core. The φ-resonance substrate provides a measurable improvement in proposal quality.

### 1.2 Test Design

**Metric:** Proposal quality classification (high-confidence vs. mixed-confidence)

**Data Required:**
- N = number of proposal cycles (mining rounds)
- For each cycle: count of high-confidence proposals with φ-resonance active
- Control: count of high-confidence proposals with φ-resonance inactive (baseline)
- Expected: ≥ 1,000 cycles for statistical power

**Statistical Test:**
- Two-proportion z-test for comparing high-confidence rates
- Significance level: α = 0.05 (5% false positive rate)
- Power target: 1 − β = 0.80 (80% chance of detecting true effect)

---

## 2. Telemetry Format

### 2.1 Required Fields

Each mining proposal entry should record:

```csv
timestamp,cycle_id,phi_resonance_active,proposal_id,proposal_type,
hash_rate,nonce_candidate_count,high_confidence_flag,
reconstruction_error,invariant_signature_hash
```

### 2.2 Directory Structure

```
telemetry/
├── README.md
├── schema/
│   └── mining_proposal_v1.json
├── samples/
│   ├── proposals_sample_1000.csv
│   └── proposals_sample_10000.csv
├── analysis/
│   ├── statistical_analysis.py
│   ├── null_hypothesis_test.py
│   └── confidence_intervals.py
└── raw/
    └── [anonymized production logs]
```

---

## 3. Statistical Analysis Framework

### 3.1 Effect Size (Cohen's h)

For two proportions p₁ (with φ-resonance) and p₂ (baseline):

```
h = 2 × arcsin(√p₁) − 2 × arcsin(√p₂)
```

**Interpretation:**
| h | Effect Size |
|---|-------------|
| 0.20 | Small |
| 0.50 | Medium |
| 0.80 | Large |

**Target:** h ≥ 0.50 (medium effect) for publication-worthy evidence.

### 3.2 Confidence Interval

For the difference in proportions:

```
CI = (p₁ − p₂) ± z_{α/2} × √(p₁(1−p₁)/n₁ + p₂(1−p₂)/n₂)
```

Where z_{α/2} = 1.96 for α = 0.05.

**Criterion for Significance:** CI does not include 0.

### 3.3 P-Value Calculation

```python
from scipy import stats

def two_proportion_z_test(x1, n1, x2, n2):
    """Two-proportion z-test.
    
    Args:
        x1: successes with treatment (high-confidence proposals)
        n1: total proposals with treatment
        x2: successes with control (baseline)
        n2: total proposals with control
    
    Returns:
        z_statistic, p_value
    """
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    z = (p1 - p2) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    return z, p_value
```

---

## 4. Example: 14→6 Proposal Improvement

### 4.1 Observed Data

**Event:** 14 mixed-confidence proposals → 6 high-confidence proposals after φ-resonance optimization

**Interpretation:**
- Initial state: φ-scaling (hallucinated class) present in 4/14 proposals
- Final state: φ-scaling eliminated (0/6 proposals)
- Improvement: compression_target (high-confidence class) rose from 5→6
- Net change: 14 proposals with mixed confidence → 6 proposals with high confidence

### 4.2 Statistical Interpretation

**Treatment:** φ-resonance core + Salamander self-healing optimization cycle  
**Outcome:** Proposal quality improvement (mixed → high confidence)  
**Sample:** 1 optimization cycle (not yet replicated)

**Limitation:** Single-cycle observation is insufficient for statistical inference. Requires:
- Minimum 30 independent cycles for Central Limit Theorem approximation
- Minimum 1,000 cycles for robust null hypothesis testing
- Multiple independent runs to establish reproducibility

### 4.3 Required Data for Publication

To make this claim CERN-viable:
1. **1,000+ independent cycles** with φ-resonance active
2. **1,000+ independent cycles** with φ-resonance inactive (control)
3. **Blinded analysis:** Analysts do not know which condition is active
4. **Pre-registration:** Analysis plan published before data collection begins
5. **Replication:** Independent team reproduces the result

---

## 5. Mining as CERN-Compatible Evidence

### 5.1 The Blockchain Proof Property

Mining has a unique advantage: **accepted shares are independently verifiable on the Bitcoin/BCH blockchain.**

This means:
- Anyone running a full node can verify that HYBA found valid blocks
- The hashrate contributed is publicly auditable
- The proposal quality improvement is indirectly validated by actual block discoveries

### 5.2 Evidence Hierarchy

| Evidence Type | Independent Verification | Statistical Rigour | Current Status |
|---------------|-------------------------|-------------------|----------------|
| **Accepted shares** | ✅ Public blockchain | ⚠️ Descriptive statistics | ✅ Available |
| **Proposal quality** | ❌ Internal only | ✅ Testable (needs data) | ⚠️ Needs 1,000+ cycles |
| **Hash rate improvement** | ✅ Pool telemetry | ⚠️ Needs A/B test | ⚠️ In progress |
| **Efficiency gain** | ⚠️ Partially verifiable | ✅ Testable | ⚠️ Observed, needs replication |

### 5.3 The Publishable Claim

**Current (insufficient):** "Our mining improved from 14 mixed to 6 high-confidence proposals."

**Publishable (sufficient):** "Across N=1,247 independent mining cycles, φ-resonance activation was associated with a 23% (95% CI: 19–27%) increase in high-confidence proposal rate compared to baseline (p < 0.001, two-proportion z-test). The effect size was medium-to-large (Cohen's h = 0.62). Results were replicated across three independent validation periods."

---

## 6. Action Items

### 6.1 Immediate (This Week)

1. **Instrument the mining controller** to emit CSV telemetry with required fields
2. **Create 1,000-cycle baseline run** (φ-resonance inactive)
3. **Create 1,000-cycle treatment run** (φ-resonance active)

### 6.2 Short-term (This Month)

4. **Run statistical analysis** using `analysis/statistical_analysis.py`
5. **Calculate effect size and confidence intervals**
6. **Write up results** for internal review

### 6.3 Medium-term (This Quarter)

7. **Blind the analysis** and re-run
8. **Independent replication** by team member not involved in original run
9. **Prepare preprint** for arXiv (statistics, quantitative biology, or quantum physics)

---

## 7. Conclusion

The mining telemetry is the **strongest externally verifiable evidence** in the HYBA repository. However, the current state (single observation of 14→6) is anecdotal, not statistical.

To elevate the evidence to CERN-compatible standards:
1. **Scale:** 1,000+ cycles per condition
2. **Control:** Baseline run without φ-resonance
3. **Blind:** Analysts unaware of condition labels
4. **Replicate:** Independent reproduction

The infrastructure exists. The test suite exists. The statistical framework exists. What is needed is the **data collection run** to transform promising observations into rigorous evidence.

**Nothing was left to chance — except the data has not yet been collected at scale.**