# Benchmark Portfolio Acceptance Addendum

## BLUF

The HYBA Phi-Trifecta Benchmark Portfolio is the reviewer-facing evidence pack for the HENDRIX-Phi / PULVINI thesis.

It explains the measured benchmark story, preserves the hash-validity boundary, and records the topological scaling path from M32 toward H4 geometry.

## Portfolio surfaces

Required repo-controlled surfaces:

```text
benchmark_portfolio/README.md
benchmark_portfolio/TOPOLOGICAL_SCALING.md
scripts/benchmark_portfolio_gate.py
```

Optional generated surfaces:

```text
benchmark_portfolio/index.html
benchmark_portfolio/run_benchmarks.py
benchmark_portfolio/run_output/portfolio_report.json
benchmark_portfolio/run_output/PORTFOLIO_SUMMARY.md
```

The optional generated surfaces may be produced by a full benchmark refresh. The fast integrity gate validates documentation and saved report consistency without rerunning network-bound historical analysis.

## Latest benchmark envelope

The latest local portfolio run reported:

| Evidence lane | Result |
|---|---|
| Quantum mathematics verification | 8/8 tests passing from saved artifacts |
| Structured search comparison | Passed, about 0.05s |
| Phi15 Bitcoin block analysis | 93.88 percent resonance, z=8.69 |
| Hash-validity correlation | r=-0.002, near-zero direct SHA validity correlation |
| Full stack analysis | 35.5x over unstructured Grover assumptions |

Interpretation:

> HYBA has benchmark evidence for structured Phi-guided traversal and topological scaling. SHA-256 and external share acceptance remain the final proof oracle.

## Topological scaling result

```text
M32 baseline: H3, 32 domains, 120 transforms.
Football: 60 domains, same H3 class, incremental domain refinement.
600-cell: H4, 120 vertices, 14,400 transforms, real step-change.
120-cell: H4, 600 vertices, full 4D Phi-manifold scaling candidate.
```

The key result is not that more vertices automatically win. The key result is that the H4 jump changes the symmetry class and expands the Phi-preserving transform group.

## Fast validation command

```bash
python scripts/benchmark_portfolio_gate.py
```

Use `--strict-optional` only when the local HTML dashboard, orchestrator, and run-output files are expected to be present.
