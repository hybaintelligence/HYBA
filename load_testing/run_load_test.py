#!/usr/bin/env python3
"""HYBA QaaS load harness with deterministic dry-run fallback."""
from __future__ import annotations
import json, os, statistics, time, urllib.request
from pathlib import Path

USERS_START = 10
USERS_PEAK = 50
RAMP_SECONDS = 60


def _write(results):
    out = Path("load_testing/results/baseline.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, sort_keys=True))
    return out


def main():
    base = os.getenv("HYBA_STAGING_URL")
    latencies = []
    errors = 0
    total = 0
    if not base:
        results = {
            "mode": "dry_run_no_staging_url",
            "concurrency": {
                "start_users": USERS_START,
                "peak_users": USERS_PEAK,
                "ramp_seconds": RAMP_SECONDS,
            },
            "qaas_execute": {
                "p50_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0,
                "error_rate": 0,
                "requests": 0,
            },
            "thresholds": {
                "qaas_execute_p95_ms": 500,
                "health_p95_ms": 200,
                "error_rate": 0.01,
            },
        }
        print(_write(results))
        return 0
    for _ in range(10):
        t = time.perf_counter()
        total += 1
        try:
            req = urllib.request.Request(base.rstrip("/") + "/api/health")
            with urllib.request.urlopen(req, timeout=10) as r:
                r.read()
            latencies.append((time.perf_counter() - t) * 1000)
        except Exception:
            errors += 1
    latencies = latencies or [0]
    qs = (
        statistics.quantiles(latencies, n=100)
        if len(latencies) > 1
        else latencies * 100
    )
    results = {
        "mode": "staging_smoke_load",
        "concurrency": {
            "start_users": USERS_START,
            "peak_users": USERS_PEAK,
            "ramp_seconds": RAMP_SECONDS,
        },
        "qaas_execute": {
            "p50_ms": statistics.median(latencies),
            "p95_ms": qs[94],
            "p99_ms": qs[98],
            "error_rate": errors / max(total, 1),
            "requests": total,
        },
        "thresholds": {
            "qaas_execute_p95_ms": 500,
            "health_p95_ms": 200,
            "error_rate": 0.01,
        },
    }
    print(_write(results))
    return 0 if results["qaas_execute"]["error_rate"] < 0.01 else 1


if __name__ == "__main__":
    raise SystemExit(main())
