<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://ai.google.dev/static/site-assets/images/share-ais-513315318.png" />
</div>

# HYBA Fullstack

This repository contains the HYBA application frontend, backend services, and PYTHIA quantum mining components.

View your app in AI Studio: https://ai.studio/apps/48eebfab-04ed-42cd-bfee-0f1fec7066ad

## Run Locally

**Prerequisites:** Node.js and Python 3.12

1. Install frontend dependencies:
   `npm install`
2. Install backend dependencies:
   `python -m pip install -r python_backend/hyba_genesis_api/requirements.txt`
3. Set local development secrets in `.env.local` or `.env`.
4. Run the app:
   `npm run dev`

## Production readiness

Run the full local release check with:

```bash
npm run prod:check
```

Build the production container with:

```bash
npm run docker:build
```

The production runbook, deployment gates, environment contract, health checks, rollback rules, and regulatory boundary notes are documented in [HYBA_FULLSTACK Production Readiness Runbook](docs/PRODUCTION_READINESS.md).

## Backend validation

Run the backend regression suite with:

```bash
PYTHONPATH=python_backend python3 -m unittest discover -s tests -p "test_*.py"
```

Run the authenticated backend E2E smoke with:

```bash
PYTHONPATH=python_backend python3 scripts/run_backend_e2e.py
```

The suite includes unit, integration-smoke, adversarial validation, MIDAS production-control, and randomized property-style coverage for the HYBA substrate and PYTHIA mining paths.

## PYTHIA Quantum Mining

The quantum mining implementation, configuration contract, mathematical notes, pool degraded-state behavior, and validation procedure are documented in [HYBA Quantum Mining Implementation](docs/QUANTUM_MINING.md).

## HYBA Autonomic Substrate Protocol

The unbounded autonomic substrate extension is documented in [HYBA Autonomic Substrate Protocol v1.0](docs/autonomic-substrate-protocol.md).
