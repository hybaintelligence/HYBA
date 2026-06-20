# Quantum Fault-Tolerance Claim Boundary

## Purpose

This document separates what the current HYBA fault-tolerant quantum core tests
actually verify from what remains a projection or product-facing claim boundary.
It must be read before using QaaS billing, public API, or sales language that
mentions `logical_error_rate`, `fault_tolerant`, surface-code distance, or
fault-tolerant virtual computers.

## What is currently verified by tests

The local tests verify implementation-level behavior of the mathematical model:

- `FaultTolerantQuantumCore` rejects even code distances and initializes odd
  distance logical-qubit arrays.
- Syndrome measurement returns arrays with the expected stabilizer dimensions.
- Decoder/correction, logical gates, measurement, controller, and mining-cycle
  integration return well-formed control-plane results.
- The modeled logical-error-rate formula follows the repository's explicit
  suppression equation:

  ```text
  p_L = 0.03 * (p_phys / 0.0109) ** ((distance + 1) / 2), for p_phys < 0.0109
  p_L = 1.0, for p_phys >= 0.0109
  ```

- For a fixed physical error rate below the `0.0109` model threshold, the modeled logical error
  rate is expected to decrease monotonically as odd code distance increases.
- For a fixed odd code distance, the modeled logical error rate is expected to
  increase monotonically as physical error rate increases below the `0.0109`
  model threshold. The separate `(3-φ) * 0.01` value is retained only as a
  φ-reference scalar and is not used to classify `fault_tolerant`.

These are deterministic checks of the implemented model and API envelope. They
are not empirical proof that a deployed substrate has measured physical
fault-tolerance behavior.

## What is not yet verified

The current suite does not prove any of the following:

- measured hardware quantum fault tolerance;
- experimentally observed threshold-theorem behavior on a physical device;
- production SLOs for real customer quantum workloads;
- economic value of a billed `logical_error_rate` unit;
- mining advantage, accepted shares, revenue, or physical quantum speedup.

## Product language allowed now

Allowed language:

- "modeled logical error rate";
- "virtual fault-tolerant quantum-core model";
- "surface-code-inspired mathematical control plane";
- "substrate-agnostic mathematical runtime";
- "API-level metering for virtual QaaS/CIaaS workloads."

Disallowed unless independently validated and approved:

- "measured physical logical error rate";
- "hardware-proven fault-tolerant quantum computer";
- "guaranteed threshold-theorem performance in production";
- "mining revenue or accepted-share advantage";
- "physical quantum speedup."

## Commercial sequencing gate

Before charging customers for "fault-tolerant quantum compute cycles," one of
these decisions must be recorded:

1. **Modeled-math product:** billing units are sold as virtual mathematical
   workload units, and API responses continue to label logical-error-rate values
   as modeled/projection values.
2. **Measured fault-tolerance product:** independent evidence is added showing
   measured threshold behavior for the substrate being sold, including test
   fixtures, calibration artifacts, and acceptance criteria.

Until option 2 exists, QaaS/CIaaS public APIs must avoid implying measured
hardware fault tolerance.
