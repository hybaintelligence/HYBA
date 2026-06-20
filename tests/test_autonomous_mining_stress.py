"""Stress coverage for PYTHIA autonomous mining evidence loops."""

from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path
import sys
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import (  # noqa: E402
    AutonomousConfig,
    AutonomousMiningController,
)


def _controller() -> AutonomousMiningController:
    engine = MagicMock()
    engine.optimizer = MagicMock()
    engine.phi_ensemble = MagicMock(config={})
    engine.solver = MagicMock()
    engine.consciousness = None
    return AutonomousMiningController(engine, AutonomousConfig(persistence_enabled=False))


def test_pool_response_history_is_bounded_under_rapid_load() -> None:
    ctrl = _controller()
    for i in range(10_000):
        ctrl.record_pool_response(
            accepted=i % 3 == 0,
            latency_ms=float(i % 17),
            target="phi_scaling",
            proposal_id=f"proposal-{i % 11}",
            decision_id=f"decision-{i}",
        )
    assert len(ctrl._pool_response_history) == 1000
    assert ctrl._pool_response_history[0]["decision_id"] == "decision-9000"
    assert ctrl.get_reflexive_target_bandit_snapshot()["phi_scaling"]["posterior_mean"] <= 1.0


def test_metrics_generation_stays_fast_after_large_response_window() -> None:
    ctrl = _controller()
    for i in range(2500):
        ctrl.record_pool_response(accepted=i % 2 == 0, response_time_ms=2.5, target="search_depth")
    started = time.perf_counter()
    text = ctrl.get_prometheus_metrics_text_cached(cache_ttl_seconds=5.0)
    elapsed = time.perf_counter() - started
    assert "hyba_pool_feedback_samples 1000" in text
    assert elapsed < 0.25
    assert ctrl.get_prometheus_metrics_text_cached(cache_ttl_seconds=5.0) == text


def test_concurrent_pool_response_ingest_preserves_bounded_window() -> None:
    ctrl = _controller()

    def ingest(offset: int) -> None:
        for i in range(250):
            ctrl.record_pool_response(
                accepted=(offset + i) % 2 == 0,
                latency_ms=float(i),
                target="compression_target",
                decision_id=f"{offset}-{i}",
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(ingest, range(0, 2000, 250)))

    assert len(ctrl._pool_response_history) <= 1000
    assert all("decision_id" in sample for sample in ctrl._pool_response_history)


def test_repeated_reflexive_cycles_keep_internal_histories_bounded() -> None:
    ctrl = _controller()
    for _ in range(275):
        ctrl._phi_density_history.append(ctrl.get_phi_density())
        ctrl._phi_density_history = ctrl._phi_density_history[-200:]
        ctrl._logical_consistency_history.append(0.8)
        ctrl._logical_consistency_history = ctrl._logical_consistency_history[-100:]
        ctrl._compression_seeking_history.append(1.2)
        ctrl._compression_seeking_history = ctrl._compression_seeking_history[-100:]
    assert len(ctrl._phi_density_history) == 200
    assert len(ctrl._logical_consistency_history) == 100
    assert len(ctrl._compression_seeking_history) == 100
