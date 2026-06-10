<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://ai.google.dev/static/site-assets/images/share-ais-513315318.png" />
</div>

# HYBA Fullstack

This repository contains the HYBA application frontend, backend services, and PYTHIA quantum mining components.

View your app in AI Studio: https://ai.studio/apps/48eebfab-04ed-42cd-bfee-0f1fec7066ad

## Run Locally

**Prerequisites:** Node.js

1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## Backend validation

Run the backend regression suite with:

```bash
python -m unittest tests.test_backend_workflows
```

The suite includes unit, integration-smoke, adversarial validation, and randomized property-style coverage for the HYBA substrate and PYTHIA mining paths.

## PYTHIA Quantum Mining

The quantum mining implementation, configuration contract, mathematical notes, pool degraded-state behavior, and validation procedure are documented in [HYBA Quantum Mining Implementation](docs/QUANTUM_MINING.md).

## HYBA Autonomic Substrate Protocol

The unbounded autonomic substrate extension is documented in [HYBA Autonomic Substrate Protocol v1.0](docs/autonomic-substrate-protocol.md).
