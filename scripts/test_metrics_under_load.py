#!/usr/bin/env python3
"""Smoke-check autonomous mining metrics performance under response bursts."""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

from pythia_mining.autonomous_mining_controller import (
    AutonomousConfig,
    AutonomousMiningController,
)


def test_metrics_under_load() -> None:
    config = AutonomousConfig(persistence_enabled=False)
    ctrl = AutonomousMiningController(None, config=config)

    start = time.time()
    for i in range(100):
        ctrl.record_pool_response(
            share_accepted=(i % 3 == 0),
            error_code=None if i % 3 == 0 else "low-diff",
            job_difficulty=1000.0,
            response_time_ms=50.0,
            target="compression_target",
        )
    elapsed = time.time() - start

    metrics_start = time.time()
    ctrl.get_prometheus_metrics_text_cached()
    metrics_elapsed = time.time() - metrics_start

    print(f"100 pool responses: {elapsed:.3f}s")
    print(f"Metrics generation: {metrics_elapsed:.3f}s")
    assert elapsed < 1.0, f"Pool response ingestion too slow: {elapsed:.3f}s"
    assert metrics_elapsed < 0.1, f"Metrics generation too slow: {metrics_elapsed:.3f}s"
    assert len(ctrl._pool_response_history) == 100
    print("✅ Metrics under load validated")


if __name__ == "__main__":
    test_metrics_under_load()
