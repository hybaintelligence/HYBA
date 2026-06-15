# Mac M3 MLX/Metal Local Evidence Gate

Current as of: 2026-06-15  
Repository: HYBA_FULLSTACK  
Status: optional Apple Silicon acceleration evidence layer

## Bottom line

HYBA_FULLSTACK can run locally on a Mac M3 without Docker for a controlled evidence session.

Docker remains useful for packaging and cloud parity. It is not required for a one-hour local Mac M3 measurement run.

For Apple Silicon, the correct native path for AI tensor workloads is MLX/Metal with CPU fallback. This repository now contains an optional MLX/Metal evidence gate that verifies the hardware path when MLX is installed and the host is Apple Silicon.

## What this gate proves

The gate proves only what it measures:

- host is Apple Silicon Darwin;
- MLX can be imported;
- a deterministic phi-weighted tensor workload executes through the MLX GPU path;
- the same workload executes through the MLX CPU path;
- GPU and CPU results agree within bounded tolerance;
- a signed evidence packet is written.

## What this gate does not prove

This gate does not prove:

- accepted-share evidence;
- Bitcoin block discovery;
- general mining speedup;
- cloud production parity;
- pool-side acceptance;
- unattended production safety.

Those remain governed by the funding and accepted-share gates.

## Commands

Install MLX on the Mac M3 local environment:

```bash
python -m pip install mlx
```

Run the non-strict gate:

```bash
export PYTHONPATH=python_backend
python scripts/apple_silicon_metal_gate.py
```

Run the strict Mac M3 gate:

```bash
export PYTHONPATH=python_backend
python scripts/apple_silicon_metal_gate.py --require-mlx
```

Via npm:

```bash
npm run test:elevation:metal
npm run elevation:metal
npm run elevation:metal:require
```

## Evidence files

The gate writes:

```text
artifacts/apple_silicon_metal/apple_silicon_metal_packet.json
artifacts/apple_silicon_metal/apple_silicon_metal_manifest.json
```

Preserve those artifacts in the command-room evidence folder. Do not commit live evidence packets if they include host or session details that should remain private.

## Production compatibility

The MLX/Metal gate is additive and optional.

It does not change:

- production API routes;
- mining/funding semantics;
- accepted-share requirements;
- Docker entrypoint;
- Linux/cloud runtime requirements;
- operator credential validation.

## Canonical formulation

> On Apple Silicon, HYBA_FULLSTACK may use MLX/Metal as an optional first-class local acceleration evidence path for AI tensor workloads. The gate measures GPU/CPU execution and writes a signed packet. It does not replace accepted-share evidence, production readiness gates, or pool-side proof.
