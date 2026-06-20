# PYTHIA Supervised Production Evidence Gate

## Position

PYTHIA is allowed to report **supervised production readiness** only when the
runtime can preserve and replay evidence that connects autonomous decisions to
external pool/testnet responses. It must not treat supervised readiness as proof
of unattended commercial mining.

## Runtime Evidence Closure

The autonomous mining controller now exposes a supervised evidence ledger that
keeps the claim boundary explicit:

- pool/testnet feedback is retained in a bounded 1000-sample window;
- each response can carry accept/reject state, error code, difficulty,
  response time, proposal ID, and decision ID;
- target-selection evidence persists through the reflexive state file;
- unattended production remains blocked until a 24-hour evidence pack is
  provided.

## Required External Evidence Before Unattended Production

The following items are not inferred by PYTHIA and must be produced as external
run artifacts:

```text
- pytest suite runs in the proper local venv
- command-room game day transcript preserved
- 24h supervised run completed
- real pool/testnet feedback captured
- proposal provenance preserved
- restart recovery verified
- memory/CPU drift measured
- accepted/rejected share telemetry tied to PYTHIA decisions
```

## Claim Boundary

This gate supports the statement that PYTHIA has an architecturally credible
mining feedback loop and is ready for supervised evidence collection. It does
not claim guaranteed revenue, pool-side hashrate, accepted shares, unattended
commercial readiness, or hardware quantum speedup.
