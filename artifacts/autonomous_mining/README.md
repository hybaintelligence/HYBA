# Autonomous Mining Artifacts — Audit Summary

Runtime-generated artifacts from the PYTHIA autonomous mining controller.
All large binary/JSON files in this directory are gitignored (see root `.gitignore`).
This README is the committed record of what was captured and what the data showed.

## Directory Layout

```
artifacts/autonomous_mining/
├── reflexive_state.json          # Live reflexive controller state (gitignored)
├── reflexive_state.json.sha256   # SHA-256 integrity seal (gitignored)
├── pythia_autonomous_bootstrap_latest.json  # Latest bootstrap run record (gitignored)
├── backups/                      # Timestamped reflexive state snapshots (gitignored)
│   └── reflexive_state_<epoch>_<hash>.json
└── audit/                        # Append-only audit segment log (gitignored)
    ├── audit_segment_<ts>.json
    └── audit_segment_<ts>.json.sha256
```

## Captured Session — 2026-06-19

### Bootstrap Record (`pythia_autonomous_bootstrap_latest.json`)

| Field | Value |
|---|---|
| Schema | `HYBA_PYTHIA_AUTONOMOUS_BOOTSTRAP_V2` |
| Generated | `2026-06-19T13:59:54Z` |
| Autonomy level | `autonomous` |
| Capacity requested | `1.0 EH/s` (hard-capped by `PULVINI_HASHRATE_CAP_EHS`) |
| Epochs requested / executed | 2 / 2 |
| Self-optimising enabled | yes |
| Self-healing enabled | yes |

**Before → After (reflexive optimisation)**

| Metric | Before | After | Delta |
|---|---|---|---|
| φ-density | 0.7343 | 0.9843 | +0.2500 (+34%) |

**Self-optimising internals**

| Metric | Value |
|---|---|
| Reflexive cycle count | 198 |
| Last cycle duration | 0.415 ms |
| Proposal acceptance rate | 100% |
| Virtual mining mode | `deterministic_sha256d_hash_landscape` |

**Self-healing internals**

| Metric | Value |
|---|---|
| Autonomous circuit open | false |
| Degradation events | 0 |
| Stale-state lock recoveries | 0 |

**Runtime introspection snapshot**

Fields present: `edge_count`, `entropy_source_count`, `invariant_count`, `module_count`,
`previous_module_count`, `source`, `stable_core_count`, `virtual_mining_simulation`.

---

### Reflexive State (`reflexive_state.json`)

| Field | Value |
|---|---|
| Schema version | 2 |
| Autonomy level | `advisory` |
| φ-coherence threshold (final) | 0.6878 |
| Epochs accumulated | 193 |
| Active proposals | 5 |
| φ-density history points | 86 |
| φ-density range | 0.500 → **0.984** |

**Optimization targets active**

| Target | Objective | Current | Proposed |
|---|---|---|---|
| `phi_scaling` | maximize_phi_coherence | 1.500 | 1.425 |
| `compression_target` | maximize_phi_coherence | 1.860 | ~1.897 (converging) |
| `search_depth` | maximize_hashrate | 60.0 | 54.0 |
| `coherence_threshold` | minimize_energy | 0.700 | 0.688 |

**Capacity limits (advisory mode)**

| Limit | Value |
|---|---|
| Max autonomous hashrate | 0.5 EH/s |
| Max autonomous power | 500 W |
| Max proposals per cycle | 3 |

---

### Backups (`backups/`)

12 timestamped snapshots across 3 epoch clusters:

| Epoch cluster | Snapshots | Approx size each |
|---|---|---|
| `1781866606` | 3 | ~16 KB |
| `1781867223–1781867224` | 7 | ~46–50 KB |
| `1781877594` | 2 | ~49–51 KB |

Total backup corpus: ~575 KB across 12 files.

---

### Audit Segments (`audit/`)

Append-only signed audit log. Each segment is a JSON file paired with a `.sha256` integrity seal.
The `audit/` subdirectory is fully gitignored — segments are machine-generated at runtime and
can be very large over long sessions.

- 21 segment pairs captured in this session
- Timestamps span `1781891919654` → `1781892326269` (Unix ms)

---

## Why These Files Are Gitignored

| Reason | Detail |
|---|---|
| Size | Backup files reach 50 KB each; 193-epoch sessions generate hundreds of MB |
| Churn | Every reflexive cycle rewrites `reflexive_state.json` — creates noisy diffs |
| Runtime-only | Files are generated fresh at controller start; not source artifacts |
| Secrets boundary | Audit segments may contain live pool/job telemetry |

The `.sha256` seals travel with their JSON pairs so integrity can be verified locally
without committing the raw data to the repository.
