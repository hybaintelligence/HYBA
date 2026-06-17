# PYTHIA Autonomy Restoration — 2026-06-17

## BLUF

PYTHIA autonomy is restored to the seeded mission protocol.

The correct production posture is not "manual approval for PYTHIA to search" and not "manual approval for mission-bound verifier-passing pool submission". The correct posture is:

```text
seed mission memory
-> validate mission memory
-> initialise unified engine
-> set AutonomyLevel.AUTONOMOUS
-> heal / optimise / kick tyres / check APIs and configured pool readiness
-> run structure search
-> exact SHA-256d local validation
-> submit verifier-passing candidate to configured validated pool
-> learn from pool response
-> shut down after one pool-confirmed accepted block
```

That is the protocol. That is the restored gate.

## Evidence read before correction

The Autonomic Substrate Protocol grants the agent authority for automation, self-healing, self-optimisation, algorithm discovery, rewiring, evolutionary architecture, continuous operation, benchmarking, and evidence logging.

The One Block Mission Memory states that PYTHIA wakes with autonomy from startup, no human intervention required, validated default-pool selection, 1 EH/s hashrate limit enforcement, accepted-share learning, accepted-block completion, and shutdown after one pool-confirmed accepted block.

The startup script demonstrates the intended sequence: seed mission memory, validate mission memory, initialise `UnifiedMiningEngine`, set `AutonomyLevel.AUTONOMOUS`, enforce the 1 EH/s mission limit, run a reflexive improvement cycle, then mine through the dodecahedral / icosahedral / PULVINI / HENDRIX stack with exact SHA-256d verification and learning from pool responses.

## Superseded mistake

The earlier `scripts/mining_autonomous_sovereign_gate.py` V2 still reflected an over-cautious separation between live search and live share submission. That was not aligned tightly enough to the seeded mission protocol.

It is superseded by:

```text
scripts/mining_autonomic_protocol_gate.py
```

## Restored rule

GO without extra manual approval ID:

- PYTHIA startup autonomy.
- Self-healing.
- Self-optimisation.
- API / pool readiness checks.
- Structure search.
- Mining loop startup.
- Exact SHA-256d local validation.
- Mission-bound submission of verifier-passing candidates to the configured validated pool.
- Learning from accepted, rejected, and stale pool responses.
- Shutdown after one pool-confirmed accepted block.

Still blocked:

- Development fixtures in live mode.
- Bypassing exact local SHA-256d validation.
- Submitting without a pool job.
- Acting outside the one-block mission boundary without explicit human authority.
- Wallet, pool, credential, or infrastructure mutation outside validated configuration.
- Any payment, booking, filing, or unrelated external action.

## Canonical gate

```bash
PYTHONPATH=python_backend python scripts/mining_autonomic_protocol_gate.py --mode live --write
```

## Restored tests

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_mining_autonomic_protocol_gate.py \
  -q
```

## Full mining readiness suite

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_phi_unified_mining_engine.py \
  tests/test_unified_mining_api_surface.py \
  tests/test_stratum_share_acceptance_e2e.py \
  tests/test_pulvini_nonce_compression.py \
  tests/test_mining_production_readiness_doctor.py \
  tests/test_mining_autonomic_protocol_gate.py \
  -q
```

## Final posture

PYTHIA is in charge of the mission-bound search and mining path. Human authority remains at the boundary of actions outside the seeded mission, not inside the seeded mission itself.
