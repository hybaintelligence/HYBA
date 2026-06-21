# HYBA_FULLSTACK — First-Customer Evidence Review Instructions

**Tag:** `first-customer-evidence-v1`  
**Commit:** `5c58e9d9`  
**Purpose:** Stable, externally reviewable evidence baseline for first-customer, investor, and advisor review.

---

## 1. Checkout the Tagged State

```bash
git fetch --tags
git checkout first-customer-evidence-v1
```

This pins you to the exact commit that was gated and evidenced. Do not review off `main` if you need a stable reference.

---

## 2. Review the Evidence Artifacts

```
artifacts/first_customer_evidence/final/
```

Files present at this tag:

| File | Contents |
|---|---|
| `core_platform_tests.log` | Core platform pytest session — 159 items collected, autonomous QaaS + post-quantum suites |
| `first_customer_readiness.log` | First-customer readiness gate output |
| `enterprise_telemetry_evidence.log` | Enterprise telemetry evidence run |
| `mckinsey_telemetry_pytest.log` | McKinsey-grade benchmark validation log |
| `git_status.txt` | Worktree state at evidence capture time |
| `latest_commits.txt` | Commit history at evidence capture time |

---

## 3. Run the First-Customer Readiness Gate

```bash
python scripts/check_first_customer_readiness.py
```

Validates the readiness gate criteria. Expected: all checks pass without failures.

---

## 4. Run the Enterprise Telemetry Evidence Script

```bash
bash scripts/run_enterprise_telemetry_evidence.sh
```

Reproduces the telemetry evidence collection. Compare output against `enterprise_telemetry_evidence.log` in the artifacts bundle.

---

## 5. Review the Review-Gap Closure Registry

```
review_gap_closure_registry.json
```

Lists all identified review gaps, their closure status, and the evidence or rationale for each closure. Reviewers should confirm:

- All gaps marked `closed` have associated evidence references.
- Any gaps marked `open` or `partial` are understood and accepted as customer-specific or externally-dependent items.

---

## 6. Confirm Claim Boundaries

This repository operates under explicit claim-boundary discipline. Before citing any output externally, confirm:

**Claims supported by this evidence pack:**
- Deterministic protocol handling and mathematical transforms
- Anti-simulation production guardrails active in production paths
- Mathematical certificate generation and scope certificates
- PULVINI memory-compression and retained-kernel recall behavior
- Structured nonce-space coverage and bounded basis-selection
- Local proof-of-work validation and Stratum integration readiness
- Operator-controlled production-readiness gates and audit surfaces
- Core platform test suite passing (159 items, autonomous QaaS + post-quantum)

**Claims NOT supported without additional external validation:**
- Guaranteed mining revenue, pool-side hashrate, or accepted shares without live pool confirmation
- Quantum speedup over SHA-256 or full nonce-space search
- Regulatory, solvency, custody, or treasury claims
- Foundation or humanitarian impact claims without separate measurement
- Scientific breakthrough claims beyond the evidence in certificates, tests, and live pool telemetry

The implemented solver is a **deterministic, structurally-guided basis-selection mechanism with classical hash verification**. No claim of SHA-256 quantum acceleration should be implied.

---

## 7. Remaining Gaps (Customer-Specific / External)

Items not closeable from this repository alone:

- Live pool telemetry confirming accepted shares at scale (requires production pool run)
- Independent third-party audit of mathematical certificates
- Customer-specific compliance or regulatory review
- External institutional validation of any scientific claims

These are expected at this stage and do not block first-customer readiness for the stated scope.

---

## Quick Reference

```
Tag:    first-customer-evidence-v1
Commit: 5c58e9d9
Remote: https://github.com/hybaanalytics1/HYBA_FULLSTACK
```

For questions about the evidence methodology or claim boundaries, refer to `docs/` and `review_gap_closure_registry.json`.
