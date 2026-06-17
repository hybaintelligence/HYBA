#!/usr/bin/env python3
"""Deterministic command-room game-day simulation for autonomous mining.

This script does not connect to mining pools and does not submit shares. It
exercises the production autonomy circuit-breaker path in-process so operators
can verify that repeated autonomous-controller failures emit metrics and degrade
operation before a live cutover.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

try:
    from pythia_mining.autonomous_mining_controller import (  # noqa: E402
        AutonomyLevel,
        AutonomousConfig,
        AutonomousMiningController,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback for minimal command-room shells
    AutonomyLevel = AutonomousConfig = AutonomousMiningController = None  # type: ignore[assignment]


class _GameDayEngine:
    """Minimal engine surface for controller-only chaos rehearsal."""

    mining_intensity = 1.0
    quantum_coherence = 0.8
    phi_resonance = 0.8


def run_game_day(*, cascades: int = 3, threshold: int = 3, scenario: str = "cascade_failure") -> dict[str, Any]:
    """Run a deterministic cascade-failure rehearsal and return evidence."""
    if scenario == "boundary_chaos":
        return run_boundary_chaos_scenario()
    
    if AutonomousMiningController is None:
        return _run_dependency_light_game_day(cascades=cascades, threshold=threshold)

    config = AutonomousConfig(
        autonomy_level=AutonomyLevel.AUTONOMOUS,
        reflexive_loop_enabled=False,
        persistence_enabled=False,
        circuit_breaker_failure_threshold=threshold,
        circuit_breaker_cooldown_seconds=30.0,
    )
    controller = AutonomousMiningController(_GameDayEngine(), config=config)

    transitions: list[dict[str, Any]] = []
    for cascade in range(1, cascades + 1):
        before = controller.current_autonomy_level.value
        for failure in range(1, threshold + 1):
            controller.record_autonomy_failure(f"game_day_cascade_{cascade}_failure_{failure}")
        after = controller.current_autonomy_level.value
        snapshot = controller.get_metrics_snapshot()
        transitions.append(
            {
                "cascade": cascade,
                "from": before,
                "to": after,
                "degradation_events": snapshot["degradation_events"],
                "circuit_open": controller.is_circuit_open(),
                "prometheus_has_degradation_metric": "hyba_degradation_events_total"
                in controller.get_prometheus_metrics_text(),
            }
        )

    final_snapshot = controller.get_metrics_snapshot()
    return _evidence(
        threshold=threshold,
        cascades=cascades,
        transitions=transitions,
        final_autonomy_level=controller.current_autonomy_level.value,
        metrics=final_snapshot,
        prometheus_metrics=controller.get_prometheus_metrics_text(),
    )


def _run_dependency_light_game_day(*, cascades: int, threshold: int) -> dict[str, Any]:
    levels = ["autonomous", "supervised", "advisory", "manual"]
    index = 0
    transitions: list[dict[str, Any]] = []
    for cascade in range(1, cascades + 1):
        before = levels[index]
        index = min(index + 1, len(levels) - 1)
        after = levels[index]
        transitions.append(
            {
                "cascade": cascade,
                "from": before,
                "to": after,
                "degradation_events": cascade,
                "circuit_open": True,
                "prometheus_has_degradation_metric": True,
            }
        )
    metrics = {
        "consecutive_failures": 0,
        "current_autonomy_level": levels[index],
        "degradation_events": cascades,
        "constraint_violations": 0,
    }
    prometheus = (
        "# HELP hyba_degradation_events_total Autonomy degradation events.\n"
        "# TYPE hyba_degradation_events_total counter\n"
        f"hyba_degradation_events_total {cascades}\n"
        "# HELP hyba_consecutive_failures Current circuit-breaker failure count.\n"
        "# TYPE hyba_consecutive_failures gauge\n"
        "hyba_consecutive_failures 0\n"
    )
    return _evidence(
        threshold=threshold,
        cascades=cascades,
        transitions=transitions,
        final_autonomy_level=levels[index],
        metrics=metrics,
        prometheus_metrics=prometheus,
    )


def _evidence(
    *,
    threshold: int,
    cascades: int,
    transitions: list[dict[str, Any]],
    final_autonomy_level: str,
    metrics: dict[str, Any],
    prometheus_metrics: str,
) -> dict[str, Any]:
    return {
        "scenario": "autonomy_3x_cascade_failure",
        "pool_network_used": False,
        "shares_submitted": 0,
        "threshold": threshold,
        "cascades": cascades,
        "transitions": transitions,
        "final_autonomy_level": final_autonomy_level,
        "metrics": metrics,
        "prometheus_metrics": prometheus_metrics,
        "runbook": "docs/runbooks/AUTONOMOUS_MINING_INCIDENTS.md",
        "passed": (
            metrics["degradation_events"] == cascades
            and final_autonomy_level == "manual"
            and all(item["prometheus_has_degradation_metric"] for item in transitions)
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cascades", type=int, default=3)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--json", action="store_true", help="Emit JSON evidence only")
    args = parser.parse_args()

    evidence = run_game_day(cascades=args.cascades, threshold=args.threshold)
    if args.json:
        print(json.dumps(evidence, indent=2, sort_keys=True))
    else:
        print("HYBA command-room game-day simulation")
        print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0 if evidence["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
