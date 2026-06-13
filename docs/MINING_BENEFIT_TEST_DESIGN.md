# HYBA_FULLSTACK Mining Benefit Test Design

Current as of: 2026-06-13  
Owner: HYBA Group Command Room  
Status: Benefit-assessment test doctrine

## Why these tests exist

HYBA_FULLSTACK already has tests showing that key pieces are deterministic, bounded, reversible, and evidence-gated.

The next question is different:

```text
Do the advances actually help us?
```

The answer cannot come from belief alone. It must come from benefit tests that compare HYBA's structured approach against explicit baselines.

The purpose of these tests is to measure expected operational benefit before relying on live mining outcomes.

## The actual hypothesis

HYBA's mining advantage is expected to come from the combination of:

1. memory compression reducing the active working space;
2. empirical Phi^15 structure giving a prior over nonce space;
3. deterministic search allowing replay and controlled ranking;
4. phi/exponential scaling improving decision discipline;
5. MIDAS and accepted-share gates preventing operational overclaim.

The tests therefore ask:

```text
Can we reduce the active space without losing information?
Can structure rank useful candidates earlier than a baseline order?
Can phi-scaled indicators improve harmony when real structure is present?
Can scaling be kept tied to measured inputs rather than fabricated performance?
```

## What is being tested

The benefit suite lives at:

```text
tests/test_mining_benefit_assessment.py
```

Run it with:

```bash
npm run test:mining:benefit
```

The funding gate includes it through:

```bash
npm run test:funding:gate
```

## Benefit tests

### 1. PULVINI reduces active working space without information loss

The test compresses deterministic vectors and requires:

- reversible reconstruction;
- complete coverage;
- deterministic output;
- folded active size smaller than original size;
- compression ratio greater than 1.0;
- reconstruction error within tolerance.

This answers:

```text
Does memory compression reduce the working space while preserving what matters?
```

### 2. The 32-lane surface aligns with the 20-state PYTHIA basis

The test proves the 32-lane nonce surface folds to the dodecahedral working scale used by PYTHIA.

This answers:

```text
Does PULVINI's compression fit the solver geometry rather than existing as a separate trick?
```

### 3. Structure-aware ordering finds an injected Phi^15 signal earlier than a linear baseline

The test creates a deterministic candidate set with a known high-resonance signal and compares:

- baseline linear order;
- structure-aware order.

The structure-aware order must find the target earlier.

This answers:

```text
If the structure exists, does our ordering exploit it?
```

### 4. Structure-aware ordering is deterministic and complete

The test verifies that ranking may reorder candidates but cannot drop candidates.

This answers:

```text
Do we keep full coverage while improving order?
```

### 5. Phi-scaled decision scoring improves when indicators are structured

The test compares structured Phi-ratio indicators against unstructured indicators.

This answers:

```text
Does phi scaling respond to structure rather than arbitrary noise?
```

### 6. Capacity scaling requires measured input before performance claims

The test verifies projection-only mode cannot masquerade as measured performance, while measured input creates a measured-input benchmark record.

This answers:

```text
Can scaling help us without letting us fabricate hashrate or revenue?
```

### 7. Candidate budget can be reduced when a structure prior exists

The test computes the rank improvement when the target set is defined by high Phi^15 resonance.

This answers:

```text
Does structure reduce how much of the candidate list must be examined in structured fixtures?
```

## What these tests prove

These tests can prove:

```text
PULVINI reduces active memory while preserving reconstruction.
Structured ranking can improve candidate ordering when signal exists.
Phi-scaled decision scoring responds to structured indicators.
Performance claims remain blocked without measured input.
```

## What these tests do not prove

These tests do not prove:

```text
Bitcoin proof-of-work is bypassed.
Accepted shares are guaranteed.
Sustained revenue is guaranteed.
Payroll or office costs are covered.
A structure prior exists in every future mining window.
```

Those require live accepted-share evidence and repeated pool-side validation.

## The practical conclusion

There is no conceptual problem with HYBA's approach.

The operational question is simply whether the benefit chain survives measurement:

```text
compression benefit
+ structure-ranking benefit
+ deterministic replay benefit
+ measured accepted-share evidence
= funding-engine confidence
```

The benefit tests are designed to measure the first three parts before live mining, while the command-room accepted-share gate measures the fourth.

## Canonical formulation

Use this wording in internal reviews:

> HYBA_FULLSTACK's mining advances should benefit the funding engine if PULVINI compression reduces active working space without information loss, Phi^15 empirical structure ranks useful candidate regions earlier, deterministic search preserves replay, and measured accepted-share evidence confirms live-pool usefulness. The benefit suite tests these claims against explicit baselines before any revenue, payroll, office-cost, or MD-offer reliance is made.
