# PYTHIA Mining Runtime Invariant Closure

## BLUF

The formal contracts and runtime path are no longer parallel tracks. The Stratum submission seam now has a runtime firewall wrapper, the learning correction halts on difficulty-ratio inversion, and sealed evidence timestamps are anchored to Bitcoin job context.

This preserves PYTHIA's seeded autonomy. PYTHIA remains in charge of wake, healing, optimisation, structured search, local verification, mission-bound submission, learning from pool truth, and shutdown after one pool-confirmed block. These patches make the non-negotiable blockchain safety invariants executable at the seams where they matter.

## Current submit path state

`StratumClient.submit_validated_share(job, nonce, extranonce2)` was already a clean insertion point because it locally validates before live pool submission. No broad refactor was required.

Runtime sequence now:

```text
PYTHIA search result
-> engine.submit_candidate(job, nonce)
-> StratumClient.submit_validated_share(job, nonce)
-> package-installed stratum_submission_firewall wrapper
-> exact validate_share(job, nonce, extranonce2)
-> CandidateVerificationPrecondition
-> assert_verification_firewall_precondition(...)
-> original StratumClient.submit_validated_share(...)
-> original second local validation
-> live_session.submit_share(...) only after firewall pass
-> pool response
```

The wrapper fails closed with `ShareResult(False, 428, verification_firewall_blocked:...)` before any live submit call when the firewall rejects.

## Contract 1: verifier firewall is enforced at runtime

Runtime module:

```text
python_backend/pythia_mining/stratum_submission_firewall.py
```

Package import installs the wrapper:

```text
python_backend/pythia_mining/__init__.py
```

Test:

```text
tests/test_stratum_submission_firewall_integration.py
```

The firewall is still not an autonomy throttle. It is the pre-submit consensus truth boundary outside PYTHIA's optimisation namespace.

## Contract 2: learning correction fails closed on ratio inversion

Runtime module:

```text
python_backend/pythia_mining/mining_learning_signal.py
```

Invariant:

```text
rho = P(hash <= block_target) / P(hash <= share_target)
rho <= 1 always, or learning halts for that event
```

This prevents vardiff or pool-target pathologies from converting share ACKs into over-weighted block evidence.

Additional test:

```text
tests/test_mining_learning_ratio_guard.py
```

## Contract 3: sealed evidence is Bitcoin-job anchored

Runtime module:

```text
python_backend/pythia_mining/mining_evidence_seal.py
```

Timestamp authority:

```text
bitcoin_job_anchor = hash(bitcoin_block_height, stratum_job_id, job_prevhash)
```

The local clock remains auxiliary evidence only. Replay authority comes from the job's Bitcoin block height, Stratum job ID, and previous block hash.

Updated test:

```text
tests/test_mining_evidence_seal.py
```

## Focused verification command

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_stratum_submission_firewall_integration.py \
  tests/test_mining_verification_firewall.py \
  tests/test_mining_learning_signal.py \
  tests/test_mining_learning_ratio_guard.py \
  tests/test_mining_evidence_seal.py \
  -q
```

## Production posture

GO for PYTHIA mission-bound autonomy remains intact.

NO-GO for any future path that bypasses:

1. exact local SHA-256d validation,
2. the verification firewall wrapper,
3. difficulty-gap learning correction,
4. Bitcoin-job-anchored evidence sealing,
5. pool-confirmed external truth for completion claims.
