#!/usr/bin/env python3
"""PYTHIA autonomous bootstrap.

Runs PYTHIA's internal self-heal/self-optimise bootstrap before the local stack
is declared ready. This does not edit source code, mutate credentials, or submit
network shares directly. It wakes the autonomous controller, refreshes the live
repository surroundings graph, binds a deterministic virtual mining simulator,
sets the configured autonomy level, performs reflexive optimisation epochs,
persists learned state, and writes a boot evidence packet for the
command-room/runtime surface.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.autonomous_mining_controller import AutonomyLevel  # noqa: E402
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine  # noqa: E402
from pythia_mining.runtime_reflexive_introspection import (  # noqa: E402
    bind_runtime_reflexive_adapters,
)

TRUE_VALUES = {"1", "true", "yes", "on"}
ARTIFACT_DIR = ROOT / "artifacts" / "autonomous_mining"


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUE_VALUES


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _autonomy_level() -> AutonomyLevel:
    raw = os.getenv("HYBA_AUTONOMY_LEVEL", "autonomous").strip().lower()
    try:
        return AutonomyLevel(raw)
    except ValueError:
        return AutonomyLevel.AUTONOMOUS


def _serialise_report(report: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(report, default=str))


async def run_bootstrap(epochs: int, capacity_ehs: float) -> dict[str, Any]:
    engine = UnifiedMiningEngine(configured_capacity_ehs=capacity_ehs)
    controller = engine.autonomous_controller
    runtime_introspection = bind_runtime_reflexive_adapters(
        controller,
        package_root=PYTHON_BACKEND / "pythia_mining",
    )
    level = _autonomy_level()
    controller.set_autonomy_level(level)

    before = {
        "phi_density": controller.get_phi_density(),
        "efficiency": controller.get_current_efficiency(),
        "autonomy_level": controller.current_autonomy_level.value,
        "metrics": controller.get_metrics_snapshot(),
        "surroundings": {
            "module_count": len(controller.surroundings.module_names),
            "edge_count": len(controller.surroundings.codebase_graph_edges),
            "invariant_count": len(controller.surroundings.mathematical_invariants),
            "entropy_source_count": len(controller.surroundings.entropy_sources),
            "stable_core_count": len(controller.surroundings.stable_core),
        },
    }

    epoch_reports: list[dict[str, Any]] = []
    for _ in range(max(0, epochs)):
        epoch_reports.append(_serialise_report(await controller.seek_improvement()))

    after = {
        "phi_density": controller.get_phi_density(),
        "efficiency": controller.get_current_efficiency(),
        "autonomy_level": controller.current_autonomy_level.value,
        "metrics": controller.get_metrics_snapshot(),
        "status": _serialise_report(controller.get_autonomy_status()),
        "surroundings": {
            "module_count": len(controller.surroundings.module_names),
            "edge_count": len(controller.surroundings.codebase_graph_edges),
            "invariant_count": len(controller.surroundings.mathematical_invariants),
            "entropy_source_count": len(controller.surroundings.entropy_sources),
            "stable_core_count": len(controller.surroundings.stable_core),
        },
    }

    return {
        "schema": "HYBA_PYTHIA_AUTONOMOUS_BOOTSTRAP_V2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "enabled": _env_bool("HYBA_ENABLE_AUTONOMOUS_MINING", True),
        "capacity_ehs_requested": capacity_ehs,
        "autonomy_level": level.value,
        "epochs_requested": epochs,
        "epochs_executed": len(epoch_reports),
        "runtime_introspection": runtime_introspection,
        "before": before,
        "epochs": epoch_reports,
        "after": after,
        "self_healing": {
            "stale_state_lock_recoveries": after["metrics"].get(
                "stale_state_lock_recoveries"
            ),
            "degradation_events": after["metrics"].get("degradation_events"),
            "autonomous_circuit_open": after["metrics"].get("autonomous_circuit_open"),
        },
        "self_optimising": {
            "reflexive_cycle_count": after["metrics"].get("reflexive_cycle_count"),
            "proposal_acceptance_rate": after["metrics"].get(
                "proposal_acceptance_rate"
            ),
            "last_reflexive_cycle_duration_ms": after["metrics"].get(
                "last_reflexive_cycle_duration_ms"
            ),
            "virtual_mining_simulation": runtime_introspection.get(
                "virtual_mining_simulation"
            ),
        },
    }


def write_report(report: dict[str, Any], output: Path | None = None) -> Path:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    path = output or ARTIFACT_DIR / "pythia_autonomous_bootstrap_latest.json"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run PYTHIA autonomous bootstrap epochs."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=_env_int("HYBA_BOOTSTRAP_REFLEXIVE_EPOCHS", 2),
        help="Number of reflexive self-optimisation epochs to execute.",
    )
    parser.add_argument(
        "--capacity-ehs",
        type=float,
        default=_env_float("HYBA_QUANTUM_CAPACITY_EHS", 1.0),
        help="Configured capacity passed into the unified mining engine.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional JSON report output path.",
    )
    args = parser.parse_args()

    if not _env_bool("HYBA_ENABLE_AUTONOMOUS_MINING", True):
        report = {
            "schema": "HYBA_PYTHIA_AUTONOMOUS_BOOTSTRAP_V2",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "enabled": False,
            "status": "skipped_by_env",
        }
    else:
        report = asyncio.run(run_bootstrap(args.epochs, args.capacity_ehs))

    path = write_report(report, args.output)
    payload = {**report, "artifact_path": str(path)}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
