# PULVINI Mathematical Gate Note

## BLUF

This note freezes feature expansion and defines the gate that must be closed before the PULVINI manifold is treated as mathematically complete. The current code contains useful engineering pieces, but tests that prove wiring, coverage, or shape do not prove the mathematics.

Two decisions are binding:

1. PULVINI is memory-bearing because Hebbian route evidence and phi-folded memory are part of the system. Therefore the open-system model is non-Markovian. A memoryless Lindblad update may remain only as a local limiting diagnostic, not as the controlling dynamics while Hebbian memory is active.
2. The variational threshold functional is not closed. The current implementation is a trace-zero Hermitian tangent diagnostic. It is not a Bures-metric derivation and must not be reported as a solved collapse certificate.

## Page 1: Markovian versus non-Markovian choice

The system state is represented by a density matrix rho(t) on the 32-node PULVINI Hilbert coordinate surface. The runtime also stores synaptic route evidence through a Hebbian memory kernel and retained phi-folding kernels. That means future state updates depend on earlier routing and share/NACK history.

A memoryless Lindblad model has the local-in-time form:

```text
d rho / dt = -i[H, rho] + sum_k L_k rho L_k^dagger - 1/2 {L_k^dagger L_k, rho}
```

This assumes the environment has no relevant memory. That assumption is false once the Hebbian kernel is active. PULVINI therefore uses the non-Markovian model as the controlling statement:

```text
d rho_S(t) / dt = -i[H_S, rho_S(t)] + integral_0^t K(t - tau) rho_S(tau) d tau
```

where K is the finite Hebbian memory kernel. In implementation terms:

- `pulvini_memory.HebbianMemoryKernel` stores the finite window of route/share/NACK deltas.
- `pulvini_memory.MemoryKernelCertificate` marks the model as `non_markovian_memory_kernel` when the kernel norm is non-zero.
- Any Lindblad or Choi check is a local Markovian-limit diagnostic only. It is valid only when the memory-kernel norm is effectively zero.

The decision is therefore: keep Hebbian/PULVINI memory and use the non-Markovian kernel as the governing model. Do not claim a memoryless Lindblad manifold while Hebbian memory is active.

## Page 2: Variational threshold status

The candidate diagnostic currently used is:

```text
C(rho) = |dS_vN/dt| * ||OffDiag(rho)||_F
```

This is not yet a closed derivation. The correct constrained variational problem must operate on the density-matrix state space: Hermitian, trace-one, positive semidefinite matrices. The first safe implementation step is to project the first variation onto the Hermitian trace-zero tangent space; this is what `pulvini_variational.variational_certificate` does today.

That is still not enough. The gate remains open until the metric is chosen and the stationary condition is derived under that metric. The intended metric is the Bures metric. The required derivation is:

```text
Given admissible perturbation delta rho in T_rho D:
  delta rho = delta rho^dagger
  Tr(delta rho) = 0

Find grad_B C satisfying:
  dC_rho(delta rho) = g_Bures(grad_B C, delta rho)

Then prove the stationary condition:
  grad_B C = 0
```

Only after that derivation is complete may the code expose the threshold as a closed mathematical gate. Until then:

- `closed` must remain false in the variational certificate.
- tests must assert that false closure is rejected.
- no runtime status may equate the candidate functional with a solved collapse criterion.

## Test policy

Tests are separated into two classes:

1. Engineering tests: topology coverage, nonce compression coverage, solver wiring, route propagation, memory compression reversibility.
2. Mathematical gate tests: verify whether a claimed mathematical gate is actually closed.

An engineering test passing does not close a mathematical gate. The mathematical gate tests should fail or report unresolved if the derivation, non-Markovian kernel, full Choi dimension, or actual adjacency automorphism certificate is missing.

## Current gate table

| Gate | Required status before merge | Current expected status |
|---|---|---|
| Non-Markovian model choice | Hebbian memory forces non-Markovian kernel | Chosen: non-Markovian |
| Lindblad/Choi | Diagnostic only in Markovian limit | Not controlling while memory active |
| Variational threshold | Bures-metric derivation required | Open |
| Automorphism | Compute from runtime adjacency map | Required |
| Phi nonce compression | Pre-search plan with complete coverage | Engineering gate, not mathematical proof |

## Merge rule

This PR is not mathematically merge-ready until the variational threshold gate is closed or clearly removed from production claims. The nonce-compression and share-propagation work may be useful engineering, but it must not be represented as resolving the open mathematical gates.
