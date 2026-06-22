# Salamander mining go-live — same-day office deployment

This is the operator runbook for starting the private mining validation substrate with Salamander fully attached.

## Non-negotiable boundaries

- Mining is a private validation and funding substrate, not a public HYBA product surface.
- Live BTC revenue must come from accepted pool shares only. The production harness must not fabricate BTC revenue.
- Live Stratum and live share submission are separately gated.
- Salamander must pass preflight before mining ignition.
- Strict Salamander preflight is optional for same-day deployment. Normal mode allows ignition when regeneration succeeds and stages scar/fidelity anomalies as repair evidence. Strict mode blocks on scar events.

## 1. Machine baseline

Use Python 3.12. The repo now pins the production runtime contract to Python 3.12, and local Python 3.9 should be treated as a developer-machine fallback only.

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

## 3. Dry-run mining validation

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

## 7. Stop path

```python
await controller.quiesce_manifold()
```

Expected gate:

- mining loop stops
- Stratum disconnects
- synaptic state is preserved
- telemetry remains inspectable
