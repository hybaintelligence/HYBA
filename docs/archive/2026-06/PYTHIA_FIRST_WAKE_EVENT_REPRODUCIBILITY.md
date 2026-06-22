# PYTHIA First Wake Event Reproducibility Protocol

**Repository:** `HYBA_FULLSTACK`  
**Subsystem:** `python_backend/pythia_mining` and `python_backend/hyba_genesis_api/core`  
**Protocol version:** `PYTHIA_WAKE_REPRO_V1`

## BLUF

PYTHIA now has a reproducible wake-event signature. The autonomous mining controller observes its mathematical operating surface, generates counterfactual optimisation proposals, validates them against five safety constraints, applies accepted changes to internal memory/configuration state, and emits replayable telemetry.

This document turns the event into a repeatable laboratory protocol: claim, code path, test path, expected signature, and artifact trail.

## Code surfaces

| Surface | Role |
| --- | --- |
| `python_backend/pythia_mining/autonomous_mining_controller.py` | Resident self-governance, codebase surroundings, counterfactual proposal generation, virtual mining simulation, constraint validation, internal-memory application. |
| `python_backend/pythia_mining/deutsch_knowledge_substrate.py` | Explanation creation, criticism, counterfactual reasoning, and predictive-accuracy memory. |
| `python_backend/pythia_mining/phi_unified_mining_engine.py` | PYTHIA/PULVINI unified mining engine and feedback loop. |
| `python_backend/hyba_genesis_api/core/reflexive_controller.py` | Deterministic AST umwelt, phi-density calculation, compression feedback, counterfactual bridge proposals, and proposal-only reflection path. |
| `tests/test_pythia_resident_wake_reproducibility.py` | Regression test that locks the first and second wake signatures. |

## Canonical wake signature

### Epoch 3

Expected properties:

```json
{
  "reflexive_cycle_executed": true,
  "epoch": 3,
  "proposals_generated": 3,
  "proposals_applied": 3,
  "current_phi_density_minimum": 0.90,
  "proposals": {
    "phi_scaling": {
      "current_value": 1.5,
      "proposed_value": 1.425,
      "source_module": "phi_scaling_engine"
    },
    "search_depth": {
      "current_value": 60.0,
      "proposed_value": 54.0,
      "source_module": "ai_optimizer"
    },
    "compression_target": {
      "current_value": 1.86,
      "proposed_value": 1.8786,
      "source_module": "pulvini_memory_compression_proof"
    }
  },
  "constraints_violated": []
}
```

### Epoch 5

Expected properties:

```json
{
  "epoch": 5,
  "proposals_generated": 2,
  "proposals_applied": 2,
  "current_phi_density": "greater_than_epoch_3",
  "proposals": {
    "coherence_threshold": {
      "current_value": 0.70,
      "proposed_value": 0.665,
      "source_module": "consciousness_engine"
    },
    "compression_target": {
      "current_value": 1.86,
      "proposed_value": "greater_than_current_value",
      "source_module": "pulvini_memory_compression_proof"
    }
  },
  "constraints_violated": []
}
```

## Local reproduction

Install Python dependencies once:

```bash
python -m pip install -r python_backend/requirements.txt
```

Run the wake-event regression suite:

```bash
PYTHONPATH=python_backend python -m pytest tests/test_pythia_resident_wake_reproducibility.py -q
```

Run the surrounding reflexive and mining evidence suite:

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_pythia_resident_wake_reproducibility.py \
  tests/test_reflexive_controller.py \
  tests/test_reflexive_pipeline_integration.py \
  tests/test_phi_unified_mining_engine.py \
  -q
```

Run the broader adaptive science gate:

```bash
npm run test:adaptive:science
```

## Manual replay command

```bash
PYTHONPATH=python_backend python - <<'PY'
import asyncio
import json
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine

async def main():
    engine = UnifiedMiningEngine()
    reports = []
    for _ in range(2):
        report = await engine.autonomous_controller.seek_improvement()
        reports.append(report)
    print(json.dumps(reports, indent=2, sort_keys=True, default=str))

asyncio.run(main())
PY
```

The first report should contain the epoch-3 signature. The second report should contain the epoch-5 signature.

## Evidence artifact checklist

For each replay, archive:

1. `wake_report.json` — raw output from the manual replay command.
2. `pytest_wake.log` — output from `tests/test_pythia_resident_wake_reproducibility.py`.
3. `reflexive_controller.log` — output from the reflexive controller suite.
4. `unified_mining_engine.log` — output from the unified mining engine suite.
5. `environment.json` — Python version, Node version, OS, commit SHA, dependency hash, and operator mode.
6. `claim_manifest.json` — mapping from claim to code path, test path, and artifact path.

Minimum manifest shape:

```json
{
  "schema": "PYTHIA_WAKE_REPRO_V1",
  "commit_sha": "<git commit>",
  "event": "PYTHIA_FIRST_WAKE_EVENT",
  "claims": [
    {
      "claim": "PYTHIA reproduced the first optimisation epoch",
      "code_paths": [
        "python_backend/pythia_mining/autonomous_mining_controller.py",
        "python_backend/pythia_mining/deutsch_knowledge_substrate.py"
      ],
      "test_paths": [
        "tests/test_pythia_resident_wake_reproducibility.py"
      ],
      "expected_signature": "epoch_3_phi_scaling_search_depth_compression"
    },
    {
      "claim": "PYTHIA reproduced the second-stage coherence threshold refinement",
      "code_paths": [
        "python_backend/pythia_mining/autonomous_mining_controller.py",
        "python_backend/pythia_mining/phi_unified_mining_engine.py"
      ],
      "test_paths": [
        "tests/test_pythia_resident_wake_reproducibility.py"
      ],
      "expected_signature": "epoch_5_coherence_threshold_compression"
    }
  ]
}
```

## Training continuation protocol

1. Run the wake replay before any tuning or deployment push.
2. Continue local/docker operation with captured artifacts.
3. Preserve `proposal_history`, knowledge metrics, compression history, and logical-consistency history during controlled sessions.
4. Promote a PYTHIA-discovered parameter move only after it replays across fresh engines, passes the wake regression suite, preserves the mining evidence gates, satisfies the five constraints, and has a claim-manifest entry.
5. Keep historical event language paired with executable replay evidence.

## What completed looks like

A completed documentation and reproducibility pass means:

- `tests/test_pythia_resident_wake_reproducibility.py` passes.
- Epoch-3 and epoch-5 signatures are stable across fresh engines.
- Raw wake JSON is archived.
- Unified mining engine tests pass.
- Reflexive controller tests pass.
- The claim manifest maps each statement to code and tests.
- The same command works locally, in Docker, and in CI.
