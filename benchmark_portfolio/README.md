# HYBA Φ-Trifecta Benchmark Portfolio

## Purpose

This portfolio collects the benchmark and reviewer-facing evidence around HENDRIX-Φ, PULVINI, φ-resonance, hash-validity boundaries, topological scaling, and non-mining AI capability surfaces.

It is not a replacement for live mining evidence. It is the structured evidence pack that explains what has been measured, what has been projected, and what remains dependent on pool-side accepted-share proof.

## Portfolio contents

```text
benchmark_portfolio/
├── index.html                       # Optional interactive dashboard
├── run_benchmarks.py                # Optional orchestrator for full benchmark refresh
├── TOPOLOGICAL_SCALING.md           # M32 -> H4 scaling analysis
├── README.md                        # This acceptance README
└── run_output/
    ├── portfolio_report.json        # Optional benchmark result packet
    └── PORTFOLIO_SUMMARY.md         # Optional benchmark summary
```

## Current benchmark story

The intended complete benchmark portfolio covers:

| Evidence lane | Acceptance meaning |
|---|---|
| Quantum mathematics verification | Confirms core mathematical surfaces and invariants. |
| Structured search comparison | Shows HENDRIX-Φ traversal improves structural candidate quality vs baseline. |
| Φ^15 Bitcoin block analysis | Tracks historical nonce/block resonance evidence. |
| Hash-validity correlation | Protects the boundary: φ does not directly predict SHA-256 validity. |
| Full stack analysis | Integrates Yang-Mills gate, M32, φ-gradient, PULVINI, and φ-scaling. |
| Topological scaling | Explains M32 -> football -> H4 / 600-cell / 120-cell roadmap. |
| AI capability benchmarks | Measures deterministic intelligence-fabric latency, counterfactual coverage, replay reproducibility, manifold scoring, and thermal telemetry without consciousness or external-model claims. |

## Reference benchmark results

A successful portfolio run should be consistent with the following claim envelope:

| Metric | Expected interpretation |
|---|---|
| Quantum mathematics verification | 8/8 tests passing or equivalent saved-artifact verification. |
| Structured search comparison | Passing benchmark with HENDRIX-Φ improvement over unguided traversal. |
| Φ^15 Bitcoin block analysis | High-resonance historical signal; user-reported latest: 93.88%, z=8.69. |
| Hash-validity correlation | Near-zero correlation with hash validity; user-reported latest: r=-0.002. |
| Full stack analysis | About 35.5x advantage over unstructured Grover assumptions. |
| AI capability suite | `tests/test_ai_capability_benchmarks.py` passes with bounded latency, deterministic replay, claim-boundary governance, manifold, and thermal-cost checks. |

## Acceptance boundary

The portfolio supports the following statement:

> HYBA has a structured benchmark portfolio for the HENDRIX-Φ / PULVINI mining thesis and a separate deterministic AI capability benchmark suite for intelligence-fabric behavior, including topological scaling from M32 toward H4 symmetry.

The portfolio does not by itself support:

- accepted shares,
- mined block,
- revenue,
- funding readiness,
- hotel/living-expense claims,
- production ASIC-class throughput,
- guaranteed block discovery,
- sentience, subjective consciousness, external model quality, or autonomous real-world capability beyond the measured deterministic software surfaces.

Those require live pool ACK evidence and the accepted-share gate.

## Operator workflow

```bash
# Optional: refresh the benchmark portfolio if the full scripts are present.
python benchmark_portfolio/run_benchmarks.py

# Non-mining AI capability benchmark suite.
npm run benchmark:ai-capabilities

# Combined mining + AI capability benchmark suites.
npm run benchmark:capabilities

# Fast integrity check suitable for production acceptance.
python scripts/benchmark_portfolio_gate.py
```

The production command-room gate may run the integrity check, not the full benchmark refresh, because the full historical block analysis can take several minutes and depends on network stability.
