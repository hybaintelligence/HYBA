# HYBA_FULLSTACK Mining Innovations and Capability Map

Current as of: 2026-06-13  
Owner: HYBA Group Command Room  
Status: Canonical funding-engine capability map

## Bottom line

HYBA_FULLSTACK's mining approach is different because it is not a loose pool connector or dashboard. It is a governed funding engine built around:

- deterministic PYTHIA search;
- PULVINI hashrate and memory-discipline boundaries;
- Phi^15 empirical nonce evidence;
- MIDAS state-machine controls;
- local command-room evidence packets;
- accepted-share proof before funding-dependent actions.

The purpose is not to claim magical mining dominance before evidence. The purpose is to make every search, connection, share, and funding decision reproducible, bounded, and auditable.

## Capability map

| Capability | Implementation surface | What is different | Expected benefit | Claim boundary |
| --- | --- | --- | --- | --- |
| Deterministic PYTHIA search | `python_backend/pythia_mining/quantum_solver.py` | Same mining target and nonce range must return the same candidate nonce. | Reproducibility, replay, command-room auditability, lower operational ambiguity. | Candidate search repeatability is not the same as pool accepted-share proof. |
| Dodecahedral bounded search | `DodecahedralQuantumSolver` | Uses a 20-basis dodecahedral state-vector search with bounded nonce projection. | Compact, deterministic, range-safe exploration of nonce space. | Does not bypass Bitcoin proof-of-work or guarantee acceptance. |
| PULVINI capacity boundary | `PULVINI_HASHRATE_CAP_EHS` | Configured capacity estimates are capped at 1 EH/s. | Prevents fabricated hashrate claims and keeps funding evidence treasury-safe. | Live performance must come from measured shares or device/pool telemetry. |
| Phi-scaled ensemble weighting | `phi_scaling_engine.py` | Model votes and mining indicators are weighted deterministically by golden-ratio coherence. | Stable decision scoring and transparent weighting. | Scoring support only; not a cryptographic shortcut. |
| Phi^15 empirical evidence lane | `scripts/phi_resonance_empirical_evidence.py` and `artifacts/phi_resonance/` | Public Bitcoin nonces are measured for Phi^15 resonance and written to CSV/JSON evidence. | Empirical public-chain evidence can guide search discipline and preserve discovery history. | Resonance metrics do not by themselves prove accepted shares or revenue. |
| Funding-engine gate | `scripts/funding_engine_deployment_gate.py` | Validates Phi^15 artifacts and deterministic search before live mining reliance. | Deployment is built around evidence, not disconnected runtime optimism. | Pre-share gate is not the MD-offer trigger. |
| MIDAS control plane | `hyba_genesis_api.core.midas_controls` and mining APIs | Mining starts through explicit state transitions and operator action. | Prevents silent autoconnect, invalid transitions, and uncontrolled operation. | Accepted share remains a separate evidence threshold. |
| Accepted-share trigger | Command-room evidence folder and `funding:accepted-share:gate` | First accepted share must be evidenced locally and pool-side before funding-dependent MD offers. | Converts deployment from rehearsal to funding event with reviewable proof. | One accepted share is not sustained profitability or payroll coverage. |

## Innovations and discoveries

### 1. Deterministic search as funding discipline

The major operational discovery is that mining search must be reproducible before it can fund an institution. HYBA_FULLSTACK therefore treats deterministic replay as a funding-control property. The same target and nonce range must give the same candidate nonce; otherwise the command room cannot audit why a result occurred.

Expected benefit:

```text
less operational ambiguity
better replay and post-incident review
cleaner evidence packets
lower risk of hidden nondeterminism in funding-critical paths
```

### 2. PULVINI as restraint, not hype

PULVINI's role in the funding engine is not to inflate claims. It compresses and bounds the operating surface. The 1 EH/s configured-capacity boundary prevents a dashboard or API from turning estimates into unbounded performance claims.

Expected benefit:

```text
no fabricated hashrate
no uncontrolled treasury optimism
clear separation between configured estimate and measured share evidence
```

### 3. Phi^15 empirical evidence as search context

The Phi^15 empirical evidence lane measures public Bitcoin block nonces and records per-block resonance strength, summary mean resonance strength, and above-threshold rates. This lets HYBA preserve the founder discovery path and use public-chain evidence as a search discipline input.

Expected benefit:

```text
public-chain evidence trail
repeatable empirical artifacts
search discipline connected to HYBA discovery history
funding gate can check that empirical data is present and internally consistent
```

### 4. MIDAS state-machine mining control

MIDAS makes mining an authorised state transition rather than an ambient background process. This matters because the funding engine must be able to prove who started mining, when it started, what pool was configured, whether transitions were valid, and whether accepted shares appeared.

Expected benefit:

```text
operator accountability
no silent autoconnect
invalid transition detection
clean pre/post session evidence
```

### 5. Accepted-share proof before institutional action

The first accepted share is the threshold event for funding-dependent MD offers. That gives the institution a clear, measurable trigger.

Expected benefit:

```text
simple board-readable gate
separation between readiness and funding event
protects MD offers from being tied to mere pool connection
```

## Property tests now protecting the innovations

The capability property tests live in:

```text
tests/test_mining_innovation_properties.py
```

They protect these invariants:

1. Same target/range -> same PYTHIA nonce.
2. Returned nonce always lies inside the declared nonce range.
3. Invalid nonce ranges fail closed.
4. PULVINI configured capacity never exceeds the 1 EH/s governance cap.
5. Unconfigured solver does not fabricate hashrate telemetry.
6. Projection-only benchmarks cannot be reported as measured production performance.
7. Phi-scaled ensemble decisions are deterministic and weights sum to one.
8. Phi resonance analyzer metrics remain bounded and interpretable.

Run them with:

```bash
npm run test:mining:innovation
```

The funding gate also includes them through:

```bash
npm run test:funding:gate
```

## Expected mining benefits

HYBA_FULLSTACK's approach is expected to improve mining operations through:

- deterministic search replay;
- tighter nonce-range discipline;
- safer runtime evidence;
- bounded capacity reporting;
- reduced claim risk;
- faster command-room diagnosis;
- preserved empirical evidence around Phi^15 resonance;
- a clear transition from deployment readiness to accepted-share funding evidence.

These are operational benefits first. Revenue, profitability, payroll coverage, and office-cost coverage require accepted-share and sustained pool-side evidence.

## Canonical formulation

Use this wording in funding-engine reviews:

> HYBA_FULLSTACK differs from conventional mining stacks by combining deterministic PYTHIA nonce search, PULVINI capacity restraint, Phi^15 public-chain empirical evidence, MIDAS state-machine controls, and accepted-share funding gates. The expected benefit is not an unsupported promise of guaranteed revenue; it is a reproducible, auditable, evidence-first funding engine whose first accepted share can trigger the first seven MD offers under signed command-room approval.
