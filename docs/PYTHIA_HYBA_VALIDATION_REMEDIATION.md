# PYTHIA/HYBA Validation Remediation Protocol

**Date:** 2026-06-19  
**Status:** Implemented documentation guardrail  
**Owner:** HYBA/PYTHIA evidence governance

## Purpose

This protocol remediates claim-creep risk in PYTHIA/HYBA progress documentation. It separates mathematical invariants, prototype benchmark code, and unvalidated hypotheses so external positioning cannot confuse runnable demonstrations with validated real-world outcomes.

## Three Evidence Tiers

| Tier | External status | Required evidence | Permitted wording |
| --- | --- | --- | --- |
| **Formalism-validated** | May be used externally when linked to manifest evidence | Deterministic source path, executable test, local artifact or replay command, explicit boundary | "The implementation preserves the tested invariant under the recorded conditions." |
| **Prototype-validated** | Internal or technical-review wording only | Code executes on fixture/synthetic/public sample data; dependency and skip status disclosed | "Prototype benchmark code exists; real-data comparison remains pending." |
| **Hypothetical / research candidate** | Research backlog only | Idea, model sketch, or unbenchmarked prototype | "Research hypothesis; no production or institutional claim." |

External communications must use **Formalism-validated** claims only unless a reviewer explicitly approves a narrower technical-review appendix.

## Immediate Claim Boundaries

The following statements are prohibited unless a future evidence packet contains real data, baselines, variance, and reviewer approval:

- broad energy-advantage claims over physical quantum systems;
- statements that geometry "proves" superiority over physical annealing or other production solvers;
- hallucination detection claims via holonomy without LLM benchmark validation;
- zero-day detection claims via A5 symmetry without cybersecurity benchmark validation;
- "After-Quantum Trifecta" or "undeniable" framing as proof of production readiness;
- sovereign, investor, grid-dispatch, or mining-economics claims based only on synthetic fixtures or benchmark code.

## Benchmark Disclosure Requirements

Every benchmark, deck, report, or evidence packet must disclose:

1. whether the data are fixture, synthetic, public historical data, partner-provided real data, or live operational telemetry;
2. dependency status, including whether NumPy, Hypothesis, solver libraries, or GPU/Metal dependencies were installed;
3. skipped tests and the reason for each skip;
4. comparison baseline, including version and configuration for Gurobi, CPLEX, ASIC hardware, CFD tools, QPU services, or other external systems;
5. repeated-run statistics: sample count, variance or confidence interval, and hardware/power environment;
6. failure modes and scaling limits, including the workload that breaks the claimed compression or traversal advantage;
7. the Church-Turing-Deutsch boundary: unstructured/high-entanglement states remain exponential for classical representations.

## Domain Validation Gate

Before PROMETHEUS, mining, finance, biotech, fluid, cybersecurity, or sovereign-facing materials claim real-world performance, one domain must pass a real-data comparison gate.

### Mining option

- Load public Bitcoin block or difficulty data for a stated block-height range.
- Execute an actual double-SHA-256 validation loop or clearly state if only a prefilter/proposal loop is measured.
- Compare against published ASIC specifications with cited model, TH/s, watts, firmware assumptions, and date.
- Report effective hash rate, joules per terahash, accepted-share or solved-header evidence where applicable, and ten-run variance.

### Clean-energy option

- Use at least six months of real or explicitly public load/renewable-generation data.
- Implement economic dispatch with documented constraints: ramp rates, reserve margins, capacity limits, line or region constraints where applicable, and regulatory feasibility notes.
- Compare with Gurobi or CPLEX MILP baselines and, if available, operator historical dispatch.
- Report cost, solve time, constraint violations, infeasibility handling, and sensitivity analysis.

## Required Reframing

Use this formulation for institutional materials until real-data validation exists:

> HYBA/PYTHIA is a mathematical formalism and software framework for structured, low-entanglement or otherwise structured workloads. Current admissible claims are repository-local mathematical invariants, deterministic guardrails, and prototype benchmark behavior under disclosed dependencies and data boundaries. Real-world performance against mining ASICs, MILP dispatch solvers, commercial CFD, cybersecurity tools, or LLM evaluation suites remains pending until linked evidence packets are produced.


## Proactive Documentation Gate

External-facing drafts must start from `docs/templates/external_claim_material.md`, preserve claim-tier front matter, and bind each claim to `docs/evidence/claim_evidence_manifest.json`. The guard script `scripts/check_validation_claim_tiers.py` validates the template, any future `docs/external_materials/**/*.md` drafts, and the mining validation manifest so overclaims are blocked before publication rather than caught only after review.

## Evidence Manifest Rule

A claim is reviewer-admissible only when it appears in `docs/evidence/claim_evidence_manifest.json` with source paths, test paths, documentation paths, executable commands, and explicit boundaries. Missing dependencies or skipped numeric tests downgrade the claim to smoke/prototype evidence until the full suite runs.
