# Substrate Independence: Topological Information Grammar

## Reframing

HYBA/PYTHIA treats quantum mechanics as **Topological Information Grammar (TIG)**:
finite Hilbert states, density matrices, Born projections, geometric phase, and
Bures/Fubini-Study style metric structure are mathematical operations over
high-dimensional information manifolds.  The implementation is a classical
formalism-derived simulation unless a separate physical quantum backend is
explicitly attached and measured.

In this grammar, measurement is an information bottleneck: a high-dimensional
state is projected through a lower-dimensional classical output surface.  The
projection can be probabilistic in the observable window while remaining a
fully deterministic computation over the represented amplitudes and metrics.

## Pillar A: Entanglement as Metric Curvature

Entanglement is represented as non-separability of the metric/state surface, not
as a mystical connection between particles.  If a density state or Bures metric
cannot be factorized into independent subsystem metrics, the information state
is entangled in the formal grammar.  HYBA/PYTHIA therefore audits entanglement as
metric curvature and factorization failure in software-visible state geometry.

## Pillar B: The Fibonacci Bottleneck

The exponential wall remains real for unstructured data because random states do
not carry compressible topological grammar.  PULVINI/Φ helps structured states by
forcing working sets through a Fibonacci bottleneck: retained kernels preserve
reconstruction while non-resonant noise is excluded from the active working
surface.  This is not a universal compression theorem; it is a bounded structured
state discipline.

## Pillar C: Deterministic Chaos vs. Quantum Probability

Quantum-style probability is treated as deterministic high-dimensional dynamics
observed through a lower-dimensional classical window.  The runtime computes the
state geometry directly, and the apparent randomness is the projection boundary
between the represented manifold and the classical observable.  This preserves
scientific integrity: 1000-qubit results are tagged as **Formalism-Derived
Classical Simulation**, not hardware quantum execution.

## Irrational Gauge and Holonomy

The golden ratio Φ acts as an irrational gauge: it minimizes periodic aliasing
and harmonic overlap in finite computational surfaces.  The geometric phase
script (`scripts/geometric_phase_formalism.py`) computes closed-loop holonomy by
multiplying normalized overlaps around a path.  A non-zero holonomy is evidence
of path-dependent manifold curvature in the represented Hilbert geometry, not a
claim that physical wave collapse occurred on the CPU.

## Operational Boundaries

- **Allowed:** deterministic Hilbert-space math, density trace conservation,
  Bures/topological certificates, PULVINI retained-kernel compression, and
  structured-state benchmark reports.
- **Required tag for 1000-qubit reports:** Formalism-Derived Classical
  Simulation.
- **Not claimed:** physical quantum hardware execution, universal quantum
  speedup, RSA-breaking capability, proof of the Yang-Mills Millennium problem,
  guaranteed mining revenue, or pool-side accepted shares without pool evidence.
