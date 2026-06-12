# HYBA Command Center Operational Manifesto

This runbook defines how a human operator observes the PULVINI manifold without
interfering with its autonomous objective reductions. Operators observe,
correlate, and authorize deployment boundaries; the manifold performs its own
thermal fade, sacrifice, Bures re-routing, and lattice re-pointing.

## Prime Directive

The external pool must continue to see one stable Stratum identity while the
internal 32-node D/I compound self-organizes. Operators must not manually move
nonce ranges during an autonomic event unless the autonomic ledger reports loss
of trace, overlapping healing ranges, or backend health degradation.

## Observability Surfaces

1. `GET /api/mining/ops/autonomics`
   - Read the latest autonomics snapshot exported by PYTHIA.
   - Confirm `pulvini_autonomics.status == "ok"`.
   - Confirm `pulvini_autonomics.rho.trace == 1.0` within operational tolerance.
   - Confirm `pulvini_autonomics.sacrificed_nodes` only contains nodes with a
     corresponding thermal event and lattice re-point in `rebalances`.

2. `GET /api/mining/ops/metrics`
   - Confirm pool acceptance rate and latency remain stable during healing.
   - Treat repeated pool connection failures as external-session decoherence.

3. `pulvini_overlay.healing_routes`
   - Confirm every sacrificed node has partitioned, non-overlapping healing
     ranges assigned to recipients.
   - Confirm `healing_ranges_overlap_free == true` before continuing a live cut.

4. `pulvini_overlay.lifecycle`
   - Expected event order during thermal sacrifice:
     `autonomic_distribution_applied` -> `lattice_repointed` -> continued
     `candidate_evaluated` / `share_submitted` / `share_outcome_recorded`.

## Live Cut Protocol: Three-Node Wipeout

Use this only after staging has passed autonomics unit, property, integration,
and end-to-end share-flow tests in the Phase Transition container.

Before touching hardware, run the invariant gate against the latest exported
state:

```bash
npm run pulvini:live-cut:check -- --state python_backend/pythia_state.json --mode preflight --min-purity 0.9
```

For a dry-run before touching hardware, execute the deterministic live-cut drill;
it writes a PYTHIA-compatible state export and reports post-cut purity:

```bash
npm run pulvini:live-cut:simulate -- --nodes 0,1,2 --state python_backend/pythia_state.live_cut.json --min-purity 0.9
```

After the physical disconnect or thermal-sacrifice event, run the post-cut gate:

```bash
npm run pulvini:live-cut:check -- --state python_backend/pythia_state.json --mode postcut --expected-severed-nodes 0,1,2 --min-purity 0.9
```

1. Establish a live Stratum session and capture the active job id.
2. Record the pre-cut values:
   - pool-visible worker identity
   - active pool name
   - active job id
   - `rho.trace`
   - `rho.purity`
   - `healing_ranges_overlap_free`
3. Disconnect or thermally sacrifice three non-adjacent nodes.
4. Observe, but do not manually interfere, while PULVINI emits:
   - thermal governance event
   - sacrifice list
   - lattice re-point commands
   - healing routes
5. Pass criteria:
   - live-cut gate reports `manifold_purity >= 0.9`
   - pool-visible worker count remains `1`
   - active job id remains unchanged
   - `rho.trace` remains `1.0`
   - `healing_ranges_overlap_free == true`
   - failed nonce ranges resolve to live recipient assignments
   - share submission continues without a Stratum session reset

## Escalation Rules

Escalate to human intervention only if one of these hard faults occurs:

- `rho.trace` deviates from `1.0` beyond tolerance.
- `healing_ranges_overlap_free` is false.
- The same sacrificed node repeatedly emits fresh lattice re-point commands
  without a new thermal event.
- The bridge health endpoint reports backend degradation and mining ops cannot
  serve autonomics state.
- The external pool disconnects or rejects all shares after a healing event.

## Phase Transition Container

Production and staging deployments must use the root Dockerfile. The runtime
image installs `python_backend/requirements.phase-transition.txt`, which bundles
FastAPI/Uvicorn, NumPy/SciPy, Stratum clients, telemetry, auth, and the test
runner needed to validate PULVINI autonomics inside the same dependency envelope
used for live mining. The frontend/server build stage uses `npm ci` and the
repository lockfile so Vite and esbuild are present when `dist/server.mjs` is
built.

## Operator Posture

The operator is an observer of the manifold, not a scheduler of node work. The
operator's job is to verify that the mathematical invariants remain closed:

- Trace conservation: `Tr(rho) = 1`
- No duplicate nonce ownership: `healing_ranges_overlap_free == true`
- Pool identity continuity: one visible worker
- Thermal sacrifice continuity: every sacrificed node has a healing route
- Bures exclusion: sacrificed nodes do not regain amplitude until telemetry
  returns below the sacrifice threshold and governance policy permits recovery
