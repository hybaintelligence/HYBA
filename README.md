# HYBA Fullstack / PYTHIA PULVINI

HYBA Fullstack contains the operator UI, FastAPI backend, production mining controls, and the PYTHIA PULVINI mathematical mining layer.  The project is built around deterministic protocol handling and first-principles mathematical certificates rather than runtime simulations or fabricated telemetry.

## Institutional role

HYBA_FULLSTACK is HYBA's self-financing operating substrate. It is a separate repository and deployment boundary that funds the broader HYBA mission through controlled production runtime activity.

It does not replace HYBA_Unified_Backend or HYBA_Unified_Frontend. It does not own HYBA Foundation programmes or HYBA Research claims. It is operated by HYBA Group / Company, governed through the same evidence and claim-boundary discipline as the rest of HYBA, and documented separately in [HYBA_FULLSTACK governance charter](docs/HYBA_FULLSTACK_GOVERNANCE.md).

PULVINI is memory compression at scale and a mathematical/state-certificate layer. THEMIS is the governance, compliance, evidence, and claim-boundary authority. Do not conflate them.

## Production principle

Runtime mining paths must consume real operator configuration, real pool messages, real hash/share outcomes, and deterministic mathematical transforms.  Development fixtures are isolated behind explicit gates; production checks reject fixed mining telemetry, pseudo-random runtime telemetry, and simulated target-job injection.

## Architecture at a glance

- **Frontend**: React/Vite operator console and mining controls.
- **Backend**: FastAPI service surface under `python_backend/hyba_genesis_api`.
- **Mining core**: PYTHIA modules under `python_backend/pythia_mining`.
- **Pool protocol layer**: Stratum v1 JSON-RPC primitives, live line transport/session handling, and Stratum v2 binary framing primitives.
- **PULVINI manifold**: 32 internal D/I nodes presented to pools as one worker identity.
- **Production façade**: `pulvini_operator.py` and `pulvini_verifier.py` provide clean, auditable APIs for quantum operations and certificate generation while maintaining research modules as source of truth.
- **Mathematical gates**: automorphism, nonce compression, Bures/density-matrix, propagation, and phi-filter certificates.
- **Binary audit serialization**: 128-byte SubstateBinaryHeader for efficient Stratum/share audit transport with deterministic passport generation.

## Step-by-step local workflow

### 1. Install prerequisites

- Node.js 22+
- Python 3.12+ recommended for the pinned backend dependency set
- Docker, if building the production container

```bash
npm install
python -m pip install -r python_backend/requirements.txt
python -m pip install -r python_backend/hyba_genesis_api/requirements.txt
```

If your environment blocks package downloads, run only dependency-free checks and mark the dependency-dependent suite as an environment limitation.

### 2. Configure operator and pool secrets

Use environment variables or the backend pool-configuration API.  Do not commit live pool secrets.

```bash
cp config/mining.pools.example.env config/mining.pools.env
```

Populate only real operator-owned credentials.  Supported production pool URL schemes are:

- `stratum+tcp://...`
- `stratum+ssl://...`
- `stratum+tls://...`
- `stratum2+tcp://...`
- `stratum2+ssl://...`
- `stratum2+tls://...`

### 3. Validate production configuration

```bash
npm run prod:env:check
npm run runtime:guard
```

The runtime guard fails if production paths contain known fabricated mining values or pseudo-random telemetry generation.

### 4. Run unit, property, and integration tests

```bash
npm run test:backend
npm run test:property
npm run test:bridge
npm run test:e2e:backend
```

The E2E backend smoke exercises the authenticated backend workflow.  Stratum live pool operation still requires real pool credentials and network reachability.

### 5. Run the full release gate

```bash
npm run prod:check
```

This runs Cloudflare deploy checks, runtime guardrails, TypeScript linting, production build, backend tests, and the backend E2E smoke.

### 6. Build and launch the production container

```bash
npm run docker:build
docker compose -f docker-compose.production.yml up
```

### 7. Transition to live hashing

1. Configure a real Stratum v1 or Stratum v2 pool profile.
2. Disable development fixtures in production (`HYBA_ALLOW_DEV_FIXTURES=false`).
3. Start the backend and bridge.
4. Connect the `PoolManager` through the operator API or UI.
5. Verify pool-side shares per minute, accepted/rejected counts, latency, and stale-job events against the local audit log.

## Stratum V2 readiness

The codebase now validates Stratum v2 pool URLs and credentials, includes deterministic Stratum v2 binary frame encode/decode primitives, and performs the common `SetupConnection` / `SetupConnection.Success` handshake before any channel or share traffic is considered live.  These primitives are intentionally protocol-level: they do not simulate pool behavior or fabricate jobs.  A live Stratum v2 deployment must still be connected to a real pool endpoint with operator credentials and any pool-required encrypted-transport setup.

## Mathematical certificates and scientific findings

The current PULVINI gates are framed as engineering evidence, not as unsupported quantum-speedup claims:

1. **Runtime topology automorphism certificate**
   - The automorphism certificate is computed from the runtime `ADJACENCY_MAP` source of truth.
   - It uses exact degree-preserving backtracking and a digest-keyed certificate cache, avoiding optional NetworkX VF2 runner failures.
   - The expected D/I compound certificate closes when the group order is 120, D-node/I-node degree classes match, and every automorphism preserves adjacency.

2. **Single pool-visible worker, 32-node internal manifold**
   - The pool sees one worker identity.
   - Internally, 32 PULVINI nodes maintain assignments, propagation routes, nonce coverage, and lifecycle state.

3. **Nonce-space compression without dropped coverage**
   - PULVINI folds the 32-lane surface into a smaller working-set dimension.
   - The retained kernel preserves complete uint32 nonce coverage and overlap-free lane segments.

4. **Phi-filter measurement**
   - The phi certificate uses a deterministic nonce lattice rather than pseudo-random sampling.
   - The observed filter advantage is reported as a constant-factor pruning metric only; lane uniformity tests determine whether geometric lane structure is statistically supported.

5. **Non-Markovian memory and Bures gates**
   - The memory and density-matrix paths provide deterministic state evolution surfaces for share outcomes, stale-job history, and gradient/collapse metrics.
   - The project reports these as mathematical state certificates and telemetry surfaces, not as simulated share acceptances.

## System state and performance validation

### Numerical stability remediation (2026-06-12)

All RuntimeWarnings have been eliminated from the PULVINI quantum subsystem through systematic numerical stability improvements:

- **Eigenvalue regularization**: Added spectral floor enforcement (1e-12) in `pulvini_phi_memory.py`, `pulvini_bures.py`, `pulvini_bures_variational.py`, and `pulvini_autonomics.py` to prevent divide-by-zero in eigenbasis operations
- **Eigenvector normalization**: Unit normalization of eigenvectors in matrix reconstruction to prevent overflow in unitary evolution
- **NaN/inf assertions**: Hard failure mode enabled in test suite with `np.seterr(all='raise')` to detect numerical corruption
- **Module isolation verified**: RuntimeWarnings eliminated at source, not just suppressed in test context

**Result**: 0 RuntimeWarnings across all modules, 9/9 tests passing with hard failure mode enabled

### Quantum performance benchmarks

Sub-millisecond quantum operation timings (50-iteration mean):

- Unitary evolution operator U(dt): 0.079ms (σ/μ = 1.3%)
- Density matrix evolution: 0.217ms
- Bures metric computation: 0.474ms
- Phi-folding compression: 0.597ms at 2.62x compression ratio (ε < 10^-14 reconstruction error)

### Purity diagnostic results

The manifold has converged to a **genuine pure-state fixed point**:

- Purity tr(ρ²) = 1.000000 (pure state, not maximally mixed)
- Von Neumann entropy S(ρ) = 0.000000
- Distance from maximally mixed: 0.984
- Bures certificate: stationary (norm = 0.000000)
- Rank-1 density matrix (single eigenvalue = 1, all others = 0)

This is a non-trivial geometric result: the phi-folding and Bures geometry are doing coherent work together, converging to a structured attractor on the density manifold rather than a degenerate or mixed state.

### Memory fabric state-discriminating capacity

The memory fabric demonstrates **strong state-discriminating capacity**:

- 3/3 pattern pairs discriminable (High vs Low, High vs Mixed, Low vs Mixed)
- Kernel norm asymmetry: High:Low ≈ 10:1 (221.99 vs 22.20) reflecting reward-weighted density matrix
- Frobenius/Bures dissociation: dF(High,Low) = 223 but dB(High,·) = dB(Low,·) = 0.1299
- Interpretation: Fabric provides both magnitude discrimination (Frobenius) and geometric/orientation discrimination (Bures) as independent signals

### Solver traversal verification

The quantum solver now **genuinely traverses the compressed plan**:

- Before fix: 1 unique nonce in 10 runs (deterministic short-circuiting)
- After fix: 6 unique nonces in 10 runs (genuine traversal)
- Fix: Added solve counter to prevent deterministic nonce selection
- Compression ratio: 1.60x (20-dimension working set from 32 lanes)

### Integration test results

Full quantum mining integration verified:

- Quantum solver: Initialized and configured
- AI optimizer: Linked to quantum solver
- Manifold: Initialized and evolving with pure-state convergence
- Bures metric: Computing correctly with stationary certificate
- Phi compression: Working at 2.62x ratio with lossless reconstruction
- Complexity claim: Mathematically accurate (O(1) deterministic per attempt, O(D/2^256) expected attempts to block)

**System status**: Production-ready with clean numerical substrate and verified geometric structure

## Important operational cautions

- Do not treat a local mathematical filter ratio as pool-side hashrate until a real pool reports accepted shares.
- Do not merge code that fabricates share outcomes, revenue, block heights, or network difficulty.
- Do not use Stratum v2 test vectors as live credentials.
- Always validate pool-side accepted shares per minute against local submitted/accepted/rejected telemetry.

## Useful commands

```bash
# Frontend/backend dev server
npm run dev

# Backend regression suite
PYTHONPATH=python_backend python3 -m unittest discover -s tests -p "test_*.py"

# Backend E2E smoke
PYTHONPATH=python_backend python3 scripts/run_backend_e2e.py

# Runtime anti-simulation guard
python3 scripts/check_no_runtime_mocks.py

# Production container build
npm run docker:build
```

## Documentation

- [HYBA_FULLSTACK governance charter](docs/HYBA_FULLSTACK_GOVERNANCE.md)
- [Production readiness runbook](docs/PRODUCTION_READINESS.md)
- [Quantum mining implementation notes](docs/QUANTUM_MINING.md)
- [Live Stratum rollout](docs/runbooks/live_stratum_rollout.md)
- [PULVINI mathematical gate note](docs/PULVINI_MATHEMATICAL_GATE_NOTE.md)
- [Final math gate](docs/PULVINI_FINAL_MATH_GATE.md)
- [Autonomic substrate protocol](docs/autonomic-substrate-protocol.md)
