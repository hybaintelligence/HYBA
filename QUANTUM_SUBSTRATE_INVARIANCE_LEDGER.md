# Quantum Substrate Invariance Ledger

## Purpose

This ledger tests the HYBA thesis that quantum-formal behaviour comes from mathematics, not from an external quantum SDK or a particular hardware substrate.

The claim under test is deliberately narrow:

```text
same formal state + same formal operator -> same invariant
```

CPU, GPU, Metal, MLX, CUDA, and other execution surfaces may accelerate computation. They do not create the formal invariant. A hardware-specific path is valid only if it preserves the same invariant as the reference mathematical operator.

## Current implementation

The first hermetic harness is implemented in:

```text
python_backend/pythia_self_healing/quantum_substrate_invariance.py
```

It runs the same phi-weighted formal operator across deterministic execution surfaces:

```text
pure_python
cpu_surface
accelerator_shadow
```

The accelerator shadow is not a hardware claim. It is a CI-safe adapter boundary that proves the invariant is tied to the operator, not to a single implementation path. Real Metal/CUDA/MLX adapters can later be inserted behind the same invariant contract.

## Falsifier

The quantum-substrate claim weakens or fails if:

```text
- two execution surfaces produce different invariant signatures;
- the result depends on Qiskit, Cirq, Braket, or another external quantum SDK;
- a hardware label is treated as proof of quantumness;
- a hardware adapter changes the mathematical invariant beyond tolerance;
- the invariant cannot be replayed without special state hidden outside the packet.
```

## Replay

```bash
pytest tests/test_quantum_substrate_invariance.py -q
```

## Boundary

This ledger does not claim quantum supremacy, quantum hardware execution, or new physics. It tests a first-principles mathematical substrate invariant and prepares the contract real hardware adapters must satisfy.
