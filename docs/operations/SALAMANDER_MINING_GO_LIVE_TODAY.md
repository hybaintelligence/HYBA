# Salamander mining go-live — same-day treasury deployment

This is the operator runbook for starting the private HYBA treasury mining substrate with Salamander fully attached.

HYBA_FULLSTACK remains the discrete deployable runtime for today. HYBA_Unified_Backend fusion is intentionally deferred until mining creates runway, equipment/workspace is stabilised, and GitHub subscription/agent capacity is available.

## Non-negotiable boundaries

- Mining is a private HYBA treasury and validation substrate, not a public HYBA product surface.
- Mining exists to fund the vision, equipment, workspace, and operational runway.
- Live BTC revenue must come from accepted pool shares only. The production harness must not fabricate BTC revenue.
- Live Stratum and live share submission are separately gated.
- Salamander must pass preflight before mining ignition.
- Strict Salamander preflight is optional for same-day deployment. Normal mode allows ignition when regeneration succeeds and stages scar/fidelity anomalies as repair evidence. Strict mode blocks on scar events.
- Do not merge HYBA_Unified_Backend into HYBA_FULLSTACK during same-day treasury mining operations.

## 1. Machine baseline

Use Python 3.12. The repo pins the production runtime contract to Python 3.12, and local Python 3.9 should be treated as a developer-machine fallback only.

```bash
cd /Users/demouser/Desktop/HYBA_FULLSTACK
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## 2. Salamander + regeneration certification

```bash
PYTHONPATH=python_backend python -m pytest \
  tests/test_quantum_regeneration_properties.py \
  tests/test_salamander_frontier.py \
  tests/test_regeneration_manager_api.py \
  tests/test_salamander_mining_integration.py \
  -v --timeout=120
```

Expected gate: all selected tests pass. The regeneration property suite and Salamander frontier suite have already shown clean local passes in the 2026-06-22 operator run.

## 3. Dry-run treasury validation

Dry-run confirms that the fault-tolerant mining controller, Salamander mining guard, session evidence, and revenue-accounting boundaries are alive without submitting live shares.

```bash
export PYTHONPATH=python_backend
export HYBA_MINING_MODE=dry_run
export HYBA_SALAMANDER_STRICT_PREFLIGHT=false
python -m pythia_mining.production_mining_system
```

Expected gate:

- `SALAMANDER GATE: READY`
- session file written under `artifacts/mining_sessions/`
- `Observed Revenue: 0.00000000 BTC` unless a real pool result was supplied
- no fabricated BTC revenue

## 4. Live pool environment

Populate real pool values locally only. Never commit `.env.local`.

```bash
export NODE_ENV=production
export HYBA_ENV=production
export PYTHONPATH=python_backend

export HYBA_ENABLE_LIVE_STRATUM=true
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=false
export HYBA_ENABLE_MINING_AUTOCONNECT=false
export HYBA_OPERATOR_APPROVAL_REQUIRED=true
export HYBA_LIVE_SHARE_APPROVAL_ID="operator-approved-$(date -u +%Y%m%dT%H%M%SZ)"

export HYBA_MINING_POOL_URL="stratum+tcp://<pool-host>:3333"
export HYBA_MINING_POOL_NAME="<pool-name>"
export HYBA_MINING_WORKER="<account.worker>"
export HYBA_MINING_PASSWORD="<pool-worker-password>"
export HYBA_SALAMANDER_STRICT_PREFLIGHT=false
```

Live share submission remains disabled above. Turn it on only after pool subscribe/authorize, telemetry, cooling, power, and operator approval are confirmed:

```bash
export HYBA_ENABLE_LIVE_SHARE_SUBMIT=true
```

## 5. Live ignition path

Live ignition should use `MiningExecutiveController` with `StratumClient`, not the dry-run validation harness. The executive controller now runs the Salamander mining gate before any pool connection or mining loop ignition.

Minimal operator script shape:

```python
import asyncio
from pythia_mining.mining_executive_controller import MiningExecutiveController
from pythia_mining.stratum_client import StratumClient

async def main():
    client = StratumClient(
        pool_url="stratum+tcp://<pool-host>:3333",
        username="<account.worker>",
        password="<pool-worker-password>",
        pool_name="<pool-name>",
        stratum_version=1,
    )
    controller = MiningExecutiveController()
    controller.set_stratum_client(client)
    result = await controller.ignite_manifold()
    print(result)
    print(controller.get_nervous_system_telemetry())

asyncio.run(main())
```

Expected gate:

- `success: true`
- `status: IGNITED`
- `salamander_gate.ready: true`
- Stratum connected/authenticated in nervous-system telemetry

## 6. Office readiness checklist

Before enabling live share submission, confirm:

- Machines have Python 3.12 and repo dependencies installed.
- Pool account, worker, and password are valid.
- Network egress to the pool host/port is allowed.
- Power, cooling, fire safety, and noise constraints are ready for sustained load.
- Operator approval ID is recorded.
- Monitoring is visible to the people in the office.
- Kill switch is known: call `quiesce_manifold()` or stop the process.
- A treasury record is kept for any BTC earned, pool payout thresholds, wallet movements, hardware purchases, workspace costs, and runway allocation.

## 7. Treasury allocation order

This is not a product launch. This is a treasury ignition sequence. Use mined proceeds in this order unless the chairman overrides it:

1. keep machines online safely,
2. secure/upgrade mining and development hardware,
3. stabilise workspace/Airbnb/office logistics,
4. pay for GitHub subscription and agent capacity,
5. fund controlled HYBA_Unified_Backend fusion,
6. preserve runway for product work.

## 8. Stop path

```python
await controller.quiesce_manifold()
```

Expected gate:

- mining loop stops
- Stratum disconnects
- synaptic state is preserved
- telemetry remains inspectable
