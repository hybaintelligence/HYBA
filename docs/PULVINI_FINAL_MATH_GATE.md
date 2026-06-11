# PULVINI Final Mathematical Gate

## BLUF

This gate closes the final mathematical review points without changing the pool-facing contract.

Implemented layers:

1. `pulvini_variational.py` — first-variation certificate for the threshold functional.
2. `pulvini_gamma.py` — empirical beta-binomial gamma estimates for NACK-driven jump strength.
3. `pulvini_choi.py` — Kraus/Choi certificate for complete-positivity checks.
4. `tests/test_pulvini_final_math_gate.py` — final property/integration gate.

## Variational threshold certificate

The control functional is:

```text
C(rho) = |dS/dt| * ||OffDiag(rho)||_F
```

The first variation is:

```text
deltaC = |dS/dt| * OffDiag(rho) / ||OffDiag(rho)||_F
```

The test asserts the stationary condition:

```text
stationary iff |dS/dt| = 0 or OffDiag(rho) = 0
```

## Empirical gamma

The NACK channel strength is now derived from observations:

```text
gamma_k = (nack_count_k + alpha_prior) /
          (observation_count_k + alpha_prior + beta_prior)
```

This removes uniform hardcoded jump strength from the final mathematical gate.

## Choi complete-positivity gate

The test builds a small-step Kraus channel from the Hamiltonian and gamma-derived jump operators, then checks:

```text
Choi PSD minimum eigenvalue >= -1e-9
trace preservation error < 1e-8
```

## Actual topology certificate

The final gate recomputes automorphisms from the runtime `ADJACENCY_MAP` constant and asserts:

```text
|Aut(G)| = 120
node orbits = [20, 12]
degree histogram = {6: 20, 10: 12}
adjacency is preserved for every computed automorphism
```

## Validation command

```bash
python -m unittest tests.test_pulvini_final_math_gate
python -m unittest discover -s tests -p "test_*.py"
```
