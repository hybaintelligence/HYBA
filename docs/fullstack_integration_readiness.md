# Full-Stack Integration Readiness

This document records the Agent 7 deployment-readiness coverage for the local
HYBA operator stack.

## Scope

The live integration suite in `tests/test_fullstack_connectivity.py` verifies:

- backend availability on `http://127.0.0.1:3001`;
- frontend dev-server availability on `http://127.0.0.1:3000`;
- `/api` proxy routing from the frontend server to the backend;
- health, substrate, mining, and security endpoint reachability;
- CORS preflight behavior for browser-origin requests;
- enterprise error envelopes and request ID propagation;
- basic response latency and concurrent health-request handling.

The tests skip when the required local services are not running, preserving the
offline determinism of the regular unit-test suite while allowing operators to
run a live deployment-readiness gate before release.

## How to Run

Start both services first:

```bash
npm run backend:start
npm run dev
```

Then run the live full-stack suite:

```bash
PYTHONPATH=python_backend python -m pytest tests/test_fullstack_connectivity.py -v
```

Generate a readiness report from the same live checks:

```bash
PYTHONPATH=python_backend python -c "import json; from tests.test_fullstack_connectivity import DeploymentReadinessReport; report = DeploymentReadinessReport(); print(json.dumps(report.generate(), indent=2))"
```

The generated `DEPLOYMENT_READINESS_REPORT.json` is an operator artifact and is
not required to be committed.
