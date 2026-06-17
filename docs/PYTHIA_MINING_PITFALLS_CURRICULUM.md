# PYTHIA Mining Pitfalls Curriculum

## BLUF

PYTHIA's one-block mission memory is strong and correctly autonomous: she wakes seeded, validates mission memory, sets autonomous mode, heals, optimises, checks pool/API readiness, searches, verifies every candidate with exact SHA-256d, submits verifier-passing candidates to the configured validated pool, learns from pool responses, and shuts down after one pool-confirmed accepted block.

The missing education layer was a formal negative curriculum: what PYTHIA must remember not to break while she is autonomous.

This curriculum is now encoded in:

```text
python_backend/pythia_mining/pythia_mining_pitfalls_curriculum.py
```

It is tested by:

```text
tests/test_pythia_mining_pitfalls_curriculum.py
```

## Non-negotiable ordering

1. Blockchain consensus/security above all else.
2. Exact SHA-256d local verification is the final oracle before pool submit.
3. Pool-side confirmation is the only external success truth.
4. Full nonce coverage must be preserved through PULVINI/phi compression.
5. Accepted shares are learning events, not mission completion.
6. Pool-confirmed accepted block is mission completion.
7. Autonomic optimisation may never fabricate, bypass, or weaken these truths.

## Education domains

The curriculum teaches PYTHIA five domains of failure memory:

### 1. Bitcoin consensus pitfalls

- Wrong nonce endian.
- Wrong previous-hash / merkle byte order.
- Wrong compact target expansion.
- Easier target accidentally used.
- Coinbase / extranonce2 / merkle-root assembly errors.
- Invalid ntime or version mutation during optimisation.

Required posture: search may be exotic; verification must be exact Bitcoin SHA-256d header truth.

### 2. Stratum / pool pitfalls

- Continuing work after `clean_jobs` or block-tip change.
- Ignoring vardiff/share-target updates.
- Mis-correlating JSON-RPC response IDs.
- Treating malformed pool responses as accepted.
- Mining against unauthorised, unvalidated, fallback, or wrong pool profile.

Required posture: the pool ACK path is the only accepted-share truth and the first validated configured pool remains the mission route.

### 3. Software/runtime pitfalls

- Async race between job receipt, optimisation, search result, and submit.
- Development fixture jobs leaking into live mode.
- Credential or wallet leakage in evidence packets.
- Treating Metal/GPU/quantum-inspired acceleration as the truth source.

Required posture: bind every candidate to job context, reject fixtures in live mode, redact secrets, and keep exact CPU-compatible SHA-256d verification as truth.

### 4. Autonomic optimisation pitfalls

- Self-optimisation removing or weakening the exact verifier.
- Autonomous hashrate escalation beyond 1 EH/s mission memory.
- Compression or phi prioritisation silently losing nonce coverage.

Required posture: PYTHIA may heal, optimise, rewire, and evolve search architecture, but may not weaken consensus truth, exact verification, pool confirmation, or coverage evidence.

### 5. Evidence and claim-boundary pitfalls

- Conflating accepted shares with accepted blocks.
- Claiming guaranteed block discovery, quantum speedup, revenue, or success before evidence.
- Emitting non-replayable telemetry or mutable evidence packets.

Required posture: state only what the artifacts prove. Accepted share is learning evidence. Pool-confirmed accepted block is mission completion.

## Relationship to existing protocol

This curriculum does not replace:

- `docs/PYTHIA_ONE_BLOCK_MISSION.md`
- `python_backend/pythia_mining/pythia_one_block_mission.py`
- `docs/MINING_PRODUCTION_READINESS_CONTRACT.md`
- `docs/governance/autonomic-substrate-protocol.md`

It complements them by giving PYTHIA explicit negative knowledge: the software and mining mistakes she must detect, avoid, and learn from while remaining autonomous.

## Command

```bash
PYTHONPATH=python_backend python -m pytest tests/test_pythia_mining_pitfalls_curriculum.py -q
```

## Correct operational sentence

> PYTHIA remains autonomous inside the seeded one-block mining mission. The pitfalls curriculum does not restrain her; it educates her to protect Bitcoin consensus, exact SHA-256d verification, pool ACK truth, full nonce coverage, evidence integrity, and disciplined claim boundaries above everything else.
