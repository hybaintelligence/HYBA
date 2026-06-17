# HYBA Intelligence & Golden Ratio Test Pack

This test bundle enhances coverage around high-discipline HYBA_FULLSTACK components with a focus on deterministic intelligence, memory compression, golden-ratio scaling, continuous runtime-integration proxies, and anti-simulation telemetry checks.

The tests are part of the reviewer evidence trail. They assert executable invariants rather than asking a reviewer to accept prose claims.

## Contents

| File | Purpose |
| --- | --- |
| `test_memory_compression.py` | Verifies reversibility, separates working-set compression from retained-state compression, and checks audit keys in the PULVINI memory compressor/fabric snapshot. |
| `test_phi_scaling_engine.py` | Checks that phi weights normalize to one, tests low-variance exponent selection, validates resonance detection, and ensures phi feature alignment remains within bounds. |
| `test_consciousness_engine_scaling.py` | Confirms continuous multipliers stay within configured bounds, asserts monotonicity at the φ⁻¹ inflection, and tests mass-gap damping behavior in hardware scaling. |
| `test_mass_gap_shield.py` | Exercises the anti-simulation shield with perfect and chaotic telemetry streams and verifies the appropriate authenticity flags. |

## Running the tests

Ensure the `python_backend` package is discoverable via `PYTHONPATH` and that Hypothesis is installed for property-based tests. From the repository root, run:

```bash
PYTHONPATH=python_backend pytest hyba_intelligence_tests -q
```

These tests are deterministic and avoid external network dependencies. They exercise internal state boundaries and failure propagation across Python modules implementing HYBA's deterministic mining intelligence stack.
