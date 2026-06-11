# PULVINI Mathematical Gate Note

## BLUF

Feature expansion remains frozen. This note records the production-closure state
of the PULVINI mathematical gates. Engineering tests prove topology, nonce
coverage, propagation, and solver wiring invariants. Mathematical gate closure is
recorded separately by runtime certificates, governing-model code paths, and the
Bures-metric derivation implemented on the density-matrix manifold.

## Gate 1 — Penrose Gate [CLOSED]
- Functional: `C[rho] = |dS_vN/dt| * ||OffDiag(rho)||_F`
- Metric: Bures metric on density matrices via the symmetric logarithmic
  derivative relation `rho L_rho + L_rho rho = 2 delta rho`.
- Implemented gradient: `grad_Bures C = 2 * (rho @ flat_grad + flat_grad @ rho)`.
- Stationary distinction: trivial zero-product states are not meaningful
  collapse certificates; non-trivial stationary points are reported as
  eigenbasis-alignment collapse criteria.
- Source: `PulviniManifold.bures_gradient_of_collapse_functional()`.
- Test result: Bures gradient norm reported as `1.180799` for the coherent
  runtime state with entropy gradient `0.3`.

## Gate 2 — Deutsch Gate [CLOSED]
- Governing model: Nakajima-Zwanzig non-Markovian master equation.
- Runtime dispatcher: `PulviniManifold.evolve_production()` routes to the
  non-Markovian step whenever the Hebbian memory-kernel norm is above
  `MARKOV_THRESHOLD = 1e-3`.
- Memory measure: Frobenius norm of `synaptic_matrix - I`.
- Test result: non-zero Hebbian kernel routed through NZ evolution and returned
  a trace-one positive semidefinite density matrix.

## Gate 3 — Deutsch Diagnostic Gate [CLOSED]
- Lindblad/Choi status: local diagnostic only in the Markovian limit.
- Runtime rule: `lindblad_step()` is valid only when
  `memory_kernel_norm() < MARKOV_THRESHOLD`.
- Production rule: memory-bearing evolution must call
  `nakajima_zwanzig_step()` through `evolve_production()`.

## Gate 4 — Automorphism Certificate [CLOSED]
- Algorithm: VF2 isomorphism enumeration
- Result: `|Aut(G)| = 120`, orbits `{6:20, 10:12}`
- Computation time: `545.89ms`
- Source: runtime `ADJACENCY_MAP` constant

## Gate 5 — Empirical phi Evidence [MEASURED; UNIFORM LANE NULL NOT REJECTED]
- Original phi_acceptance_ratio: `0.537530`
- Original effective_search_space: `2308673771`
- Original compression_factor: `1.86x`
- sample_size: `1,000,000`
- date_measured: `2026-06-11`

### Baseline filter comparison
- Reproducible sample seed: `20260611`
- parity_filter_acceptance (`nonce % 2 == 0`): `0.501289`
- modulo_3_filter_acceptance (`nonce % 3 == 0`): `0.333619`
- phi_filter_acceptance on the same seeded sample: `0.537144`
- phi_minus_parity: `+0.035855`
- phi_compression_factor on the same seeded sample: `1.86x`
- Interpretation: the phi filter accepts measurably more than a parity filter,
  but this does not by itself prove search advantage. A filter that discards a
  fixed fraction of uniformly distributed nonces is not sufficient evidence of
  improved SHA-256 preimage discovery.

### PULVINI lane-topology distribution
- lane_phi_ratio_min: `0.530347`
- lane_phi_ratio_max: `0.542699`
- lane_phi_ratio_range: `0.012352`
- lane_phi_ratio_mean: `0.537139`
- lane_phi_ratio_stddev: `0.003151`
- lane_variance: `0.0000099277`
- expected_sampling_variance: `0.0000079562`
- variance_to_sampling_ratio: `1.248`
- hit_only_chi_square_df31: `18.480`
- pearson_chi_square_df31: `39.925`
- chi_square_critical_p_0_05_df31: `44.99`
- reduced_chi_square: `1.288`
- uniform_lane_null_at_p_0_05: `NOT REJECTED`
- D-node avg phi ratio: `0.537401`
- I-node avg phi ratio: `0.536702`
- D/I delta: `0.000699`
- Certificate result: `uniform_lane_distribution_not_rejected_p_0_05`
- Result: the phi filter accepts about `54%` of sampled nonces and distributes
  those accepted nonces uniformly across the 32 PULVINI lanes at the `p=0.05`
  chi-square threshold. The hit-only statistic (`18.480`) and the full Pearson
  statistic (`39.925`) are both below the `44.99` critical value for 31 degrees
  of freedom.
- Geometric alignment claim: **NOT SUPPORTED** by the current measurement.
- Search advantage claim: **NOT SUPPORTED** by the current measurement.
- Current role of phi filter: uniform nonce-space reduction by about `46%`
  (`1.86x` compression), not a demonstrated D/I-topological search pressure.

## Current gate table

| Gate | Required status before merge | Current status |
|---|---|---|
| Penrose variational threshold | Bures-metric derivation required | CLOSED |
| Deutsch non-Markovian model choice | Hebbian memory forces non-Markovian kernel | CLOSED |
| Deutsch Lindblad/Choi | Diagnostic only in Markovian limit | CLOSED |
| Du Sautoy automorphism | Compute from runtime adjacency map | CLOSED |
| Empirical phi nonce evidence | Measure acceptance and compare against trivial/geometric baselines | MEASURED; UNIFORM LANE NULL NOT REJECTED |

## CI status note

The requested CI failure log has not been read in this local environment. The
attempted command was:

```bash
gh run list --repo hybaanalytics1/HYBA --limit 5
```

It failed with `gh: command not found`, and this checkout has no configured
`remote.origin.url` from which to infer a GitHub repository. The workflow
permission block now includes `contents: read`, `actions: read`, and
`checks: write` so GitHub Actions can read run metadata and publish check
results. Merge remains blocked until CI logs are retrieved in an environment
with GitHub CLI access (or an equivalent authenticated GitHub Actions log
source) and the guardrail failure is fixed or explicitly documented as a false
positive.

## Merge rule

This PR is mathematically merge-ready only insofar as the recorded certificates,
derivations, and empirical measurement above remain reproducible. Passing tests
prove engineering invariants only; the mathematical status is carried by the
certificate functions, production evolution dispatcher, Bures derivation, and the
measured phi-acceptance record in this note. Do not merge while the CI guardrail
job is red or unread.
