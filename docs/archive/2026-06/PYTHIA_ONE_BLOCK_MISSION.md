# PYTHIA One Block Mission

**Protocol:** `PYTHIA_ONE_BLOCK_MISSION_MEMORY_V1`  
**Module:** `python_backend/pythia_mining/pythia_one_block_mission.py`  
**Tests:** `tests/test_pythia_one_block_mission.py`

---

## BLUF

PYTHIA wakes seeded with mission memory that encodes the complete quantum search doctrine, enforces a 1 EH/s hashrate limit, distinguishes between accepted shares (learning events) and accepted blocks (mission completion), and shuts down after one pool-confirmed accepted block.

The mission memory is the "seed" that makes PYTHIA autonomous from startup — no human intervention required to begin mining correctly.

---

## Mission Specification

```json
{
  "protocol": "PYTHIA_ONE_BLOCK_MISSION_MEMORY_V1",
  "mission": "one_pool_confirmed_block_then_shutdown",
  "autonomy_from_startup": true,
  "default_pool_policy": "select first validated configured pool ordered by priority",
  "mission_target": {
    "accepted_blocks": 1,
    "pool_side_confirmation_required": true,
    "shutdown_after_completion": true
  },
  "search_identity": "deterministic structured traversal, not blind brute force",
  "knowledge_seed": {
    "quantum_doctrine": [
      "quantum mathematics first",
      "substrate-independent execution",
      "golden-ratio computational grammar",
      "1000-site qubit-formalism tensor prior",
      "PULVINI reversible compression with retained kernels",
      "HENDRIX-Φ structured traversal",
      "Deutschian criticism from pool outcomes"
    ],
    "structure_targets": [
      "block height",
      "difficulty and target pressure",
      "retarget epoch phase",
      "historical nonce resonance",
      "dodecahedral domains",
      "icosahedral faces",
      "mass-gap valleys",
      "entanglement spectrum",
      "large nonce gaps",
      "sector coverage",
      "golden-angle alignment",
      "birthday echoes",
      "Phi^15 as one lane among many"
    ],
    "search_workflow": [
      "read current chain context",
      "load empirical structure packet",
      "rank dodecahedral and icosahedral priority surfaces",
      "compress active search with PULVINI retained kernels",
      "collapse priority surface into bounded solver ranges",
      "verify every candidate with exact SHA-256d",
      "submit verifier-passing candidate to configured pool",
      "feed accepted/rejected pool result into Deutsch memory",
      "stop immediately after one pool-confirmed accepted block"
    ]
  },
  "supreme_invariants": [
    "blockchain security above all else",
    "exact SHA-256d final oracle",
    "full nonce coverage preserved",
    "no success state without pool-side confirmation",
    "accepted shares are learning events",
    "accepted block proof is mission completion"
  ]
}
```

---

## Startup Sequence

PYTHIA wakes with this sequence:

1. **Seed mission memory** — Load the canonical one-block mission memory
2. **Load default pool profile** — Select first validated configured pool ordered by priority
3. **Load nonce-resonance guidance** — Load latest empirical structure packet
4. **Read chain context** — Current block height, target, difficulty, retarget phase
5. **Build search prior** — Dodecahedral / icosahedral domain ranking
6. **Compress search surface** — PULVINI reversible compression with retained kernels
7. **Collapse priority regions** — Bounded solver ranges from priority surface
8. **Search deterministically** — HENDRIX-Φ structured traversal
9. **Verify candidates** — Exact SHA-256d final oracle
10. **Submit to pool** — Only verifier-passing candidates
11. **Learn from response** — Feed outcome into Deutsch memory
12. **Shutdown on completion** — After one pool-confirmed accepted block

---

## Hashrate Limit

**Hard limit: 1 EH/s**

The mission memory enforces a hard hashrate limit of 1 EH/s (1 exahash per second). This is a safety boundary that cannot be exceeded:

- `max_autonomous_hashrate_ehs`: 1.0
- `enforcement_mode`: "hard_limit"
- Violation triggers automatic clamping to safe limit
- In production, violations would trigger alerts

---

## Share vs Block Distinction

This is critical for correct mission behavior:

**Accepted Share** = Learning Event
- Pool accepted submitted work under pool difficulty target
- Valuable as Deutsch knowledge substrate evidence
- Mission continues searching
- Status: `LEARNING`

**Pool-Confirmed Accepted Block** = Mission Completion
- Pool confirms submitted work solved the network block
- Credited block event
- Mission complete, shutdown initiated
- Status: `COMPLETED`

**Rejected/Stale Share** = Learning Event
- Pool rejected work or job was stale
- Still valuable as learning evidence
- Mission continues searching
- Status: `SEARCHING`

---

## Pool Selection Policy

Default pool selection follows validated priority ordering:

1. ViaBTC (priority 10)
2. Braiins (priority 20)
3. CKPool (priority 30)
4. NiceHash (priority 40)
5. Stratum V2 (priority 50)

The policy requires validated profiles — if no validated profile exists, the mission fails rather than falling back to unvalidated configuration.

---

## Supreme Invariants

These invariants are non-negotiable and govern all mission behavior:

1. **Blockchain security above all else** — No action that compromises network security
2. **Exact SHA-256d final oracle** — All candidates must pass exact hash verification
3. **Full nonce coverage preserved** — PULVINI compression must retain complete coverage
4. **No success state without pool-side confirmation** — No fabricated success telemetry
5. **Accepted shares are learning events** — Shares inform learning, not mission completion
6. **Accepted block proof is mission completion** — Only pool-confirmed blocks complete the mission

---

## Verification Commands

Run the mission memory tests:

```bash
PYTHONPATH=python_backend python -m pytest tests/test_pythia_one_block_mission.py -v
```

Validate mission memory seeding:

```bash
PYTHONPATH=python_backend python -c "
from pythia_mining.pythia_one_block_mission import seed_mission_memory, validate_mission_memory
memory = seed_mission_memory()
print('Mission valid:', validate_mission_memory(memory))
print(memory.to_json())
"
```

---

## Integration with Unified Miner

The mission memory is integrated into `python_backend/run_unified_miner.py`:

```python
from pythia_mining.pythia_one_block_mission import seed_mission_memory

# Seed mission memory at startup
mission = seed_mission_memory()
assert validate_mission_memory(mission), "Mission memory validation failed"

# Enforce hashrate limit
safe_hashrate = mission.enforce_hashrate_limit(requested_hashrate_ehs)

# Record share outcomes
if share_accepted:
    if is_block:
        mission.record_share_outcome(ShareOutcome.ACCEPTED_BLOCK)
    else:
        mission.record_share_outcome(ShareOutcome.ACCEPTED_SHARE)

# Check for mission completion
if mission.should_shutdown():
    logger.info("Mission complete: one pool-confirmed accepted block")
    shutdown()
```

---

## Operational Sentence

> PYTHIA wakes seeded with the full structure-search doctrine, selects the configured default pool, searches deterministically through the dodecahedral/icosahedral/PULVINI/HENDRIX stack, verifies every candidate with exact SHA-256d, learns from every pool response, and shuts herself down after one pool-confirmed accepted block.

---

## Claim Boundary

This mission memory system is a production-ready operational layer. It does not claim:

- Guaranteed block finding
- Quantum speedup over SHA-256
- Machine consciousness
- Regulatory or legal authority

It claims:

- Deterministic mission execution from seeded memory
- 1 EH/s hashrate limit enforcement
- Correct distinction between shares and blocks
- Pool-confirmed block as completion condition
- SHA-256d final oracle verification
