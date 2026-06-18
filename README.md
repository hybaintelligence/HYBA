# HYBA_FULLSTACK

## PYTHIA / PULVINI / METIS — Coherent Mathematical Decision Substrate

**Status**: V4.x release-candidate line, production/live hardening in progress  
**Current operating boundary**: operator-authorised live execution only  
**Last evidence refresh**: 2026-06-18, local macOS/Python 3.12.13 test runs  
**Owner**: HYBA Analytics Ltd

HYBA_FULLSTACK is not only a mining repository. Mining is the first hard external proof boundary: a real-time, adversarial, externally validated environment where the system must receive jobs, search structured state space, locally validate SHA-256d work, submit only guarded candidates, and accept pool ACK/reject as final truth.

The deeper asset is a general-purpose coherent decision substrate: a mathematical organism that can search, decide, recover, remember, gate itself, stream telemetry, and expose its state through a production API.

---

## 1. What This Repository Is

HYBA_FULLSTACK combines:

- **PYTHIA mining core** — structured proof-of-work search, local SHA-256d validation, Stratum integration, live-run controls.
- **PULVINI memory and compression layer** — 32-lane manifold, phi-folding, bounded working-set compression, non-Markovian memory state.
- **Great Minds mathematical substrate** — IIT-style diagnostics, Constructor Theory, QFT/Shor-inspired period analysis, Turing/Church universal computation, Grover/quantum-walk search, Fourier harmonic analysis, lambda calculus, and cross-paradigm verification.
- **Autonomous control substrate** — audit logs, autonomous healer, optimizer, circuit breaker, miner controller, and meta-controller.
- **Regeneration substrate** — density-matrix role states, collapse/quarantine validation, refractory-period recovery, and Lindblad-style stabilization.
- **HYBA Genesis API** — FastAPI control surface with health, intelligence, mining, memory, pool, streaming, metabolism, regeneration, security, admin, and executive endpoints.
- **React/Vite operator console** — frontend command room and visual surface.

The system is designed as a substrate, not a single-purpose script.

---

## 2. Claim Boundary

This repository **does claim**:

- Deterministic protocol handling and deterministic mathematical transforms.
- Structured search before local SHA-256d validation.
- Explicit production/live separation with development fixtures locked out of live paths.
- Local proof-of-work validation before pool submission.
- Stratum v1/v2 integration and pool-management surfaces.
- Property-tested mathematical invariants for mining, regeneration, autonomy, and orchestration layers.
- Operator-controlled runtime gates, reason-state logging, and auditability.
- Constructor-substrate framing for emergent coherence, bounded by the current evidence.

This repository **does not claim**:

- A solution to the Yang-Mills Mass Gap Millennium Prize Problem.
- Guaranteed mining revenue, guaranteed pool-side hashrate, or guaranteed block discovery.
- Quantum speedup over SHA-256 consensus rules.
- Phenomenal consciousness, subjective awareness, or externally validated machine consciousness.
- Regulatory, treasury, solvency, or investment guarantees.

Consensus remains external. Pool ACK/reject remains final mining truth.

---

## 3. Current Test Ledger

These are the latest focused local results supplied from the active HYBA_FULLSTACK working tree on 2026-06-18.

### 3.1 Focused Green Suites

| Suite / Command | Coverage Purpose | Result |
|---|---:|---:|
| `tests/test_great_minds_integration.py` | 8-framework mathematical substrate and unified phi-harmonised framework | **51 passed** |
| `tests/test_quantum_regeneration_properties.py` | Density matrices, refractory period, Lindblad stabilization, collapse/quarantine | **16 passed** |
| `tests/test_autonomous_controller.py` | Audit log, healer, optimizer, circuit breaker, miner, meta-controller | **37 passed** |
| `tests/test_ai_orchestration_layer.py` | AI initialization, decision-making, share submission, advisory, unified orchestration | **36 passed** |
| `tests/test_phi_config_live_secret_gate.py` | Live/prod secret gate; fixture bypass cannot coexist with live/prod flags | **5 passed** |
| `tests/test_unified_miner_search_workflow.py` | Production fixture refusal, structured search path, no-submit reasons, feedback loops | **10 passed** |
| `tests/test_phi_unified_mining_engine.py` | Unified engine, PULVINI search, local/pool feedback preservation | **5 passed** |
| `tests/test_mining_property_invariants.py` | Hypothesis property invariants over mining/coherence/search state | **20 passed** |

**Focused green ledger total**: **180 passing tests** across the listed commands.

### 3.2 Broad Wildcard Sweep

Latest broad sweep command:

```bash
python -m pytest tests/test_mining_*.py tests/test_autonomous_*.py tests/test_great_minds_integration.py -q --tb=no
```

Observed result:

```text
301 passed, 6 skipped, 1 failed, 2 warnings
```

Known remaining failure:

```text
tests/test_mining_knowledge_base.py::TestMiningKnowledgeBase::test_evaluate_current_state_healthy
AssertionError: assert 'critical' == 'healthy'
```

Current interpretation: semantic classifier / fixture threshold mismatch in the mining knowledge-base health evaluator. It is not treated as proof that the live mining cutover path is broken, but it must be resolved before claiming the broad mining/autonomous wildcard suite is fully green.

### 3.3 Production-Critical Status

Production-critical focused paths currently verified by dedicated tests:

- Live/prod fixture lockout.
- Structured `UnifiedMiningEngine.search(job)` search path.
- Local SHA-256d validation before submit.
- Explicit no-job / no-search / no-submit reason state.
- Engine feedback loops for local rejects and pool outcomes.
- Density-matrix safety for regeneration.
- Autonomous circuit breakers and audit state.
- AI orchestration controls and summaries.

---

## 4. API Surface

The FastAPI entrypoint is:

```text
python_backend/hyba_genesis_api/main.py
```

It creates:

```text
HYBA Genesis Platform API
version: 2.0.1
```

The app installs CORS, rate limiting, telemetry middleware, enterprise API posture, and the substrate lifecycle. It also exposes three app-level endpoints:

| Endpoint | Purpose |
|---|---|
| `GET /health` | Compatibility health check with substrate and telemetry state |
| `GET /metrics` | Prometheus scrape endpoint |
| `GET /api/substrate` | Full substrate readiness and initialization order |

### 4.1 Mounted Router Modules

`main.py` mounts **20 router modules**. Because `mining.py` and `mining_jobs.py` share `/api/mining`, this is **20 mounted routers / 19 unique prefixes**.

| Router module | Prefix | Primary surface |
|---|---|---|
| `health` | `/api/health` | Health, substrate readiness, structural coupling |
| `intelligence` | `/api/v1/intelligence` | Reflexive intelligence, explain/orchestrate/closure/audit controls |
| `mining` | `/api/mining` | Mining control, runtime state, pool credentials, role-gated operations |
| `mining_jobs` | `/api/mining` | Current job and job-search read surface |
| `mining_ops` | `/api/mining/ops` | Read-only operational telemetry, audit, alerts |
| `mining_production` | `/api/v1/mining-production` | Production mining gateway, start/stop/status, live pool operations |
| `security` | `/api/security` | Security monitoring with intelligence/regeneration/swarm integrations |
| `misc` | `/api` | Pitfalls, TOE experiment acceptor, PULVINI execute checks |
| `ai` | `/api/ai` | AI runtime status, consciousness/phi telemetry, chat/stimulation boundary |
| `auth` | `/api/auth` | Argon2id/JWT authentication |
| `admin` | `/api/admin` | User, funding, executive/admin operations |
| `products` | `/api/products` | Product/catalog surface, explicit empty datastore state until connected |
| `unified_mining` | `/api/v1/unified` | Canonical unified mining engine status, resonance analysis, share-result feedback |
| `ai_memory` | `/api/v1/memory` | AI memory, empirical evidence, snapshots, reasoning traces |
| `pool_management` | `/api/v1/pools` | Pool configuration, selection, switching, stats |
| `regeneration_router` | `/api/organism/regeneration` | Regenerative lane health, blastema pool, manual lane regrowth |
| `streaming_sense` | `/api/v1/streaming` | WebSocket/SSE telemetry for phi resonance, autonomy, mining pulse, coupling, health |
| `metabolic_router` | `/api/v4/metabolism` | Biological cost-of-intelligence, entropy, hunger drive, metabolic flux |
| `organism_router` | `/organism` | CNS surface: sensory, immune, cognitive, metabolic lobes |
| `executive_router` | `/organism/executive` | Operator/executive controls, pool migration, ignition/quiescence/stasis |

### 4.2 Streaming Channels

The streaming router defines these channels:

- `phi_resonance`
- `autonomy_metrics`
- `mining_pulse`
- `structural_coupling`
- `system_health`

WebSocket entrypoint:

```text
/api/v1/streaming/connect?channels=phi_resonance,autonomy_metrics
```

SSE entrypoint:

```text
/api/v1/streaming/sse/{channel}?interval_seconds=1.0
```

---

## 5. Mining Runtime Boundary

Live mining remains operator-controlled. The live path is:

```text
Pool job
→ structured engine search
→ local SHA-256d validation
→ submit guard
→ pool ACK/reject
→ feedback into engine state
```

Production invariants:

- No live Stratum session means no live job.
- No job means no search.
- No structured nonce means no submit.
- Local SHA-256d reject means no pool submit.
- Live submit requires explicit live-submit flag and approval context.
- Pool ACK/reject is final external truth.

---

## 6. General-Purpose Uses Beyond Mining

Mining is only the first arena. The same substrate applies to:

- Autonomous operations and incident response.
- Cybersecurity and adaptive containment.
- Energy routing, grid balancing, and carbon-aware compute.
- Finance/risk scenario search and treasury decision support.
- Scientific discovery and symbolic hypothesis exploration.
- Industrial optimization and supply-chain routing.
- AI governance, agent oversight, and policy circuit breakers.
- Robotics, swarm coordination, and degraded-mode recovery.
- Regenerative infrastructure and self-healing runtime systems.
- Enterprise decision intelligence and board-level command rooms.

The reusable abstraction is:

```text
state space
→ structured search
→ external validation
→ feedback
→ memory
→ recovery
→ governance
```

---

## 7. Local Development

### 7.1 Install

```bash
git clone https://github.com/hybaanalytics1/HYBA_FULLSTACK.git
cd HYBA_FULLSTACK
npm install
python -m pip install -r python_backend/requirements.txt
```

### 7.2 Run Focused Evidence Suites

```bash
PYTHONPATH=python_backend python -m pytest tests/test_phi_config_live_secret_gate.py -q
PYTHONPATH=python_backend python -m pytest tests/test_unified_miner_search_workflow.py -q
PYTHONPATH=python_backend python -m pytest tests/test_phi_unified_mining_engine.py -q
PYTHONPATH=python_backend python -m pytest tests/test_mining_property_invariants.py -q --timeout=120
PYTHONPATH=python_backend python -m pytest tests/test_great_minds_integration.py -q
PYTHONPATH=python_backend python -m pytest tests/test_quantum_regeneration_properties.py -q --timeout=120
python -m pytest tests/test_autonomous_controller.py -q
python -m pytest tests/test_ai_orchestration_layer.py -q
```

### 7.3 Run Backend API

```bash
PYTHONPATH=python_backend uvicorn hyba_genesis_api.main:app --app-dir python_backend --host 127.0.0.1 --port 3001
```

### 7.4 Run Frontend

```bash
npm run dev
```

### 7.5 Production Build

```bash
npm run build
```

---

## 8. Evidence Pointers

Important reviewer-facing materials:

- `artifacts/release_candidates/pythia_one_block_rc_20260617/`
- `artifacts/release_candidates/pythia_one_block_rc_20260617/OPERATOR_LIVE_RUN_BRIEF.md`
- `docs/research/RESEARCH_VINDICATION_EMERGENT_COHERENCE.md`
- `docs/GREAT_MINDS_ELEVATION_PIVOT.md`
- `docs/V4_PRIME_COMMISSIONING_CERTIFICATE.md`
- `scripts/mining_production_readiness_doctor.py`
- `scripts/local_production_gate.py`

---

## 9. License

HYBA Analytics Ltd. All rights reserved.
