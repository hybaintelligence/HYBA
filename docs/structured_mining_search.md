# Structured Mining Search Boundary

HYBA mining search is framed as a structured, evidence-weighted candidate selection process, not as Grover amplitude amplification over the full nonce space.

## Evidence boundary

The blockchain evidence available to the runtime is structured:

- bounded nonce ranges supplied by pool/job configuration;
- block-header material used for SHA-256d validation;
- target difficulty and share acceptance thresholds;
- local coverage history and already-attempted nonce memory;
- dodecahedral/Φ basis sectors used only as deterministic candidate-ordering features.

The runtime may rank candidates using those features, but a candidate is only a live mining win when the concrete job header hashes below the configured target.

## Implementation boundary

`DodecahedralQuantumSolver.solve()` therefore uses deterministic structured ordering and classical SHA-256d verification. It does not run Grover iterations, does not claim hardware quantum execution, and does not claim a pool-side share unless a real job is supplied and validated.

No-job test paths may return the highest-ranked bounded candidate to exercise deterministic search behavior, but that result is explicitly candidate-only and must not be represented as accepted-share telemetry.

## Autonomous mining implementation

The concrete autonomous implementation is `PythiaAutonomousMiningAgent`. PYTHIA owns the lifecycle: it initializes a seed from repository/chain/evidence state, builds a structured Dodecahedron+Icosahedron candidate plan, modulates requested hashrate under the 1 EH/s governance cap, persists memory, records audit events, verifies hashes, and submits only verified shares through an injected submission adapter.
