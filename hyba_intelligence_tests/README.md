# HYBA Intelligence & Golden Ratio Test Pack

<<<<<<< Updated upstream
This test bundle enhances coverage around high-discipline HYBA FULLSTACK
components with a focus on deterministic intelligence, memory compression, and
golden-ratio scaling features. The tests assert invariants about the PULVINI
memory fabric, phi-scaled ensemble, feature optimizers, continuous hardware
scaling, and anti-simulation telemetry checks.
=======
This test bundle enhances coverage around the high‑discipline components of the
HYBA **FULLSTACK** codebase with a focus on **intelligence**, **memory
compression**, and **golden ratio scaling** features.  These tests go beyond
superficial assertions to verify deep invariants about the behaviour of the
PULVINI memory fabric, the phi‑scaled ensemble, feature optimisers, and the
consciousness engine’s continuous scaling logic.
>>>>>>> Stashed changes

## Contents

| File | Purpose |
<<<<<<< Updated upstream
| --- | --- |
| `test_memory_compression.py` | Verifies reversibility and audit keys in the PULVINI memory compressor and fabric snapshot. |
| `test_phi_scaling_engine.py` | Checks that phi weights normalize to one, tests low-variance exponent selection, validates resonance detection, and ensures phi feature alignment remains within bounds. |
| `test_consciousness_engine_scaling.py` | Confirms continuous multipliers stay within configured bounds, asserts monotonicity at key points, and tests mass-gap damping behavior in hardware scaling. |
| `test_mass_gap_shield.py` | Exercises the anti-simulation shield by feeding perfect and chaotic telemetry streams and verifying the appropriate authenticity flags. |

## Running the Tests

Ensure the `python_backend` package is discoverable via `PYTHONPATH` and that
Hypothesis is installed for property-based tests. From the repository root, run:
=======
|------|---------|
| `test_memory_compression.py` | Verifies reversibility and audit keys in the PULVINI memory compressor and fabric snapshot. |
| `test_phi_scaling_engine.py` | Checks that phi weights normalise to one, tests low‑variance exponent selection, validates resonance detection, and ensures phi feature alignment remains within bounds. |
| `test_consciousness_engine_scaling.py` | Confirms continuous multipliers stay within configured bounds, asserts monotonicity at key points, and tests mass‑gap damping behaviour in hardware scaling. |
| `test_mass_gap_shield.py` | Exercises the anti‑simulation shield by feeding perfect and chaotic telemetry streams and verifying the appropriate authenticity flags. |

## Running the Tests

Ensure that the `python_backend` package is discoverable via your `PYTHONPATH` and
that **Hypothesis** is installed for property‑based tests.  From the repository
root, run:
>>>>>>> Stashed changes

```bash
PYTHONPATH=python_backend pytest hyba_intelligence_tests -q
```

<<<<<<< Updated upstream
These tests are deterministic and avoid external network dependencies. They
exercise internal state boundaries and failure propagation across Python modules
implementing HYBA's deterministic mining intelligence stack.
=======
These tests are deterministic and avoid external network dependencies.  They
exercise internal state boundaries and failure propagation across the
Python modules implementing HYBA’s deterministic mining intelligence stack.
>>>>>>> Stashed changes
