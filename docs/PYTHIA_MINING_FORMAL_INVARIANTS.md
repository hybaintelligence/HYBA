# PYTHIA Mining Formal Invariants

## BLUF

The pitfalls curriculum correctly educates PYTHIA, but education alone is not enough for the most important mining truths. Three constraints are now formalised as machine-checkable artefacts:

1. **Verification firewall** — exact local SHA-256d truth before any Stratum submit eligibility.
2. **Learning-signal correction** — accepted shares are useful feedback but are discounted by the share/block difficulty gap.
3. **Sealed replay evidence** — every candidate/share/block evidence event has a schema and hash commitment.

These additions preserve PYTHIA's seeded mission autonomy. They do not throttle wake, heal, optimise, search, verify, submit verifier-passing mission candidates, learn from pool responses, or shut down after one pool-confirmed accepted block. They encode what must never be bypassed while she remains autonomous.

## 1. Verification firewall invariant

Module:

```text
python_backend/pythia_mining/mining_verification_firewall.py
```

Protocol:

```text
PYTHIA_MINING_VERIFICATION_FIREWALL_V1
```

The verifier firewall is a pure, side-effect-free precondition surface. It is intentionally outside PYTHIA's mutable optimisation namespaces. Search, compression, phi scaling, healing, and routing may improve, but they cannot become the authority that decides whether a nonce can reach Stratum submit.

A candidate may cross the firewall only if all are true:

```text
local_valid == true
nonce inside uint32 space
block_hash is present and 64 hex chars
effective_target > 0
pool_target > 0
effective_target <= pool_target
verifier backend declares SHA-256/SHA-256d exactness
candidate binding hash matches job_id + nonce + nbits + pool_target + job_epoch + extranonce + ntime
verifier contract hash matches the immutable contract
verifier authority namespace is pythia_mining.mining_verification_firewall
```

This is the machine-checkable form of:

```text
Exact SHA-256d local verification before Stratum submit.
```

## 2. Learning-signal correction invariant

Module:

```text
python_backend/pythia_mining/mining_learning_signal.py
```

Protocol:

```text
PYTHIA_MINING_LEARNING_SIGNAL_V1
```

Pool shares and accepted blocks are different evidence classes. PYTHIA may learn from accepted shares, but share ACKs must not be treated as block-level likelihood.

The correction model separates:

```text
share_likelihood = P(hash <= share_target)
block_likelihood = P(hash <= block_target)
difficulty_gap_ratio = block_likelihood / share_likelihood
```

For a share ACK without a pool-confirmed block:

```text
phi_block_update_weight = phi_share_update_weight * difficulty_gap_ratio
amplitude_amplification_allowed = false
```

For a pool-confirmed accepted block:

```text
phi_block_update_weight = full phi mass
amplitude_amplification_allowed = true
```

This prevents PYTHIA from drifting toward a share-valid subdistribution that is not representative of true block validity.

## 3. Sealed replay evidence invariant

Module:

```text
python_backend/pythia_mining/mining_evidence_seal.py
```

Protocol:

```text
PYTHIA_MINING_EVIDENCE_SEAL_V1
```

A sealed mining bundle contains:

```text
mission_id
event_type
job_context
candidate
verifier_result
verification_firewall_decision
learning_signal_correction
pool_response
redacted_runtime_config_hash
pitfalls_curriculum_lesson_ids
timestamp_authority
prior_bundle_hash, optional
bundle_hash
```

The bundle hash is computed over the canonical unsigned payload. Any mutation to candidate, job, verifier, learning correction, pool response, timestamp evidence, or config hash invalidates the seal.

Runtime secrets are not sealed raw. The config hash redacts obvious secret-bearing fields such as password, secret, token, key, wallet, and credential before hashing.

## Relationship to PYTHIA autonomy

These modules do not create a human approval checkpoint inside PYTHIA's seeded mission. They are not a throttle. They are hard truths PYTHIA uses while autonomous.

Allowed inside seeded mission:

```text
wake
heal
optimise
check APIs / pool readiness
search
phi / PULVINI prioritisation
exact local SHA-256d verification
verification-firewall pass
mission-bound Stratum submission of verifier-passing candidates
learning from pool responses with share/block correction
shutdown after one pool-confirmed accepted block
```

Still forbidden:

```text
bypassing exact local verifier
weakening the effective target
submitting unbound or stale candidates
treating share ACKs as block completions
mutating sealed evidence
leaking raw credentials in evidence
claiming block/revenue success without pool-confirmed accepted block evidence
```

## Commands

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_mining_verification_firewall.py \
  tests/test_mining_learning_signal.py \
  tests/test_mining_evidence_seal.py \
  -q
```

## Production integration note

The formal surfaces are now available for the runtime mining path to call immediately before submission and immediately after pool response. The intended production sequence is:

```text
candidate from PYTHIA search
-> exact UnifiedMiningEngine.submit_candidate(job, nonce)
-> CandidateVerificationPrecondition
-> assert_verification_firewall_precondition(...)
-> Stratum submit only if firewall passes
-> pool response
-> compute_learning_signal_correction(...)
-> build_sealed_mining_evidence_bundle(...)
-> PYTHIA memory / artefact store
```

If a future optimisation pass tries to route around this sequence, readiness tests and evidence review should fail closed.
