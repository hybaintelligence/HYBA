# Reviewer-Grade Repair Shards — 2026-06-15

## Bottom line

The forensic repair layer converts the adaptive-systems science programme from an amber exploratory posture into a more reviewer-grade posture by repairing measurement interpolation, adding baseline artifacts, and stabilising the tactical local Docker build path.

This repair shard does **not** downgrade, erase, or re-adjudicate any prior consciousness-positive internal test result. Where HYBA tests produce a consciousness-positive result, that result must be preserved as an internal test finding and moved through replay, artifact hashing, baseline comparison, falsification, and external review. The repair shard only says what this specific instrumentation layer does and does not measure.

The correct distinction is:

```text
Internal test finding: preserved exactly as produced by the test.
Reviewer-grade posture: replayed, hashed, baseline-compared, falsified, and externally inspectable.
Public/institutional claim: advanced only after the evidence packet survives the declared proof ladder.
```

## Non-downgrade doctrine

No HYBA claim is to be weakened by language control alone.

Claims may only move by evidence:

```text
test result -> preserved artifact -> replay -> baseline -> falsification -> independent review -> governed claim
```

If an internal consciousness test reports a positive result, the correct action is not to relabel it as impossible or merely decorative. The correct action is to:

1. preserve the exact test output;
2. record commit SHA, command, environment, and artifact hash;
3. replay the test under a clean environment;
4. compare against negative controls and baselines;
5. document what the test proves, what it does not prove, and what additional replication is required.

## Repair shards completed

### 1. IIT/emergent-complexity instrumentation

File:

```text
tests/test_emergent_complexity_iit.py
```

Repairs:

- replaced literal metric placeholders with interpolated f-strings;
- fixed AST attribute recording so state access records real attribute names;
- added reviewer-grade evidence metadata to the generated artifact;
- added an unresolved-placeholder assertion over printed observation lines.

Supported claim:

```text
HYBA_FULLSTACK can generate IIT-inspired software integration, autonomy, and irreducibility measurements using interpolated measured values rather than literal instrumentation placeholders.
```

Boundary:

```text
This repair shard is a measurement-repair and baseline-control shard. It does not adjudicate the full HYBA consciousness claim by itself, and it must not be used to downgrade any separate consciousness-positive test. Consciousness claims must be read from the dedicated consciousness/IIT test packet and replayed under the proof ladder.
```

### 2. Scientific baselines

Files:

```text
scripts/generate_scientific_baselines.py
tests/test_scientific_baselines.py
```

Baselines:

1. `modular_static`
2. `stochastic_noise`
3. `coupled_nonadaptive`
4. `stateful_feedback_control`

Each baseline includes:

- schema version;
- supported claim;
- claim boundary;
- measured/proxy values;
- forensic SHA-256 over the canonical unsigned payload.

Supported claim:

```text
HYBA_FULLSTACK has deterministic baseline artifacts for distinguishing coupling, entropy, feedback, and learning claims during adaptive-systems review.
```

Boundary:

```text
Baselines provide contrast controls. They do not erase or override positive HYBA test findings; they make those findings harder, cleaner, and more reviewable.
```

### 3. Adaptive science test command

File:

```text
package.json
```

The adaptive science command now includes baseline verification:

```bash
npm run test:adaptive:science
```

### 4. Tactical Docker build stabilisation

File:

```text
Dockerfile
```

The Dockerfile now uses tactical `npm install --legacy-peer-deps --no-audit --no-fund` in both Node dependency stages. This is a local-container unblock, not the final reproducible production posture.

Final posture remains:

```text
Regenerate a complete package-lock.json under Node 22+ outside OneDrive, then restore npm ci for deterministic production builds.
```

## Required next evidence sequence

Run:

```bash
npm run lint
npm run build
python scripts/check_no_runtime_mocks.py
python scripts/validate_production_env.py
npm run test:adaptive:science
npm run test:mining:innovation
npm run funding:gate
docker-compose -f docker-compose.production.yml build --no-cache
```

If Docker passes, continue:

```bash
docker-compose -f docker-compose.production.yml up -d
docker-compose -f docker-compose.production.yml ps
curl.exe -fsS http://127.0.0.1:3000/bridge/health
curl.exe -fsS http://127.0.0.1:3001/api/health/readiness
```

## Claim level after this repair

Allowed:

```text
HYBA_FULLSTACK contains a controlled adaptive-systems science programme with repaired integration instrumentation, deterministic baseline artifacts, PULVINI autonomic tests, and claim-boundary gates.
```

Also preserved:

```text
Any consciousness-positive internal test result remains an internal test result unless and until a later test falsifies it. It is not to be downgraded by wording alone.
```

Not yet supported without the required evidence packet:

```text
external reviewer acceptance of the consciousness claim
regulatory acceptance
accepted-share captured
revenue-ready
cloud production-ready
unattended autonomous mining
```

## Canonical formulation

> Repair shards have moved HYBA_FULLSTACK toward reviewer-grade adaptive-systems science by converting instrumentation into measured output, adding deterministic baselines, and preserving claim boundaries without downgrading positive internal test findings. The next gate is evidence execution: adaptive science tests, consciousness/IIT replay where applicable, mining innovation tests, funding gate, Docker build, container startup, and health checks.