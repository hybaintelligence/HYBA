#!/usr/bin/env python3
"""Run a deterministic PULVINI three-node live-cut drill.

The drill uses the production autonomics, overlay, and readiness-gate code paths.
It does not connect to a mining pool and it does not disconnect hardware; it
creates a synthetic active job, severs the requested node ids through the
GeometricRebalancer, applies the resulting lattice re-point commands to the
runtime overlay, writes a PYTHIA-compatible state export, and evaluates the
post-cut invariants.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from pythia_mining.pulvini_autonomics import (  # noqa: E402
        NodeTelemetry,
        PulviniAutonomicsEngine,
    )
    from pythia_mining.pulvini_overlay import PulviniOverlayConcentrator  # noqa: E402
    from pythia_mining.pulvini_verifier import (  # noqa: E402
        PULVINI_BINARY_HEADER_SIZE,
        PULVINI_BINARY_MAGIC,
        SubstateVerifier,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - exercised in dependency-poor shells.
    NodeTelemetry = None  # type: ignore[assignment]
    PulviniAutonomicsEngine = None  # type: ignore[assignment]
    PulviniOverlayConcentrator = None  # type: ignore[assignment]
    PULVINI_BINARY_HEADER_SIZE = None  # type: ignore[assignment]
    PULVINI_BINARY_MAGIC = None  # type: ignore[assignment]
    SubstateVerifier = None  # type: ignore[assignment]
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None

from scripts.pulvini_live_cut_readiness import evaluate_live_cut_state  # noqa: E402


def _parse_nodes(value: str) -> list[int]:
    nodes = sorted({int(item.strip()) for item in value.split(",") if item.strip()})
    if not nodes:
        raise argparse.ArgumentTypeError("at least one node id is required")
    invalid = [node for node in nodes if node < 0 or node >= 32]
    if invalid:
        raise argparse.ArgumentTypeError(f"node ids must be in [0, 31], got {invalid}")
    return nodes


def _healthy_telemetry(node_id: int):
    if NodeTelemetry is None:
        raise RuntimeError(f"PULVINI numerical dependencies are unavailable: {IMPORT_ERROR}")
    return NodeTelemetry(
        node_id=node_id,
        tres=25.0,
        phi_eff=0.98,
        chi_sync=0.96,
        thermal_entropy=0.30,
        hash_rate=1_000.0,
    )


def run_live_cut_drill(
    nodes: list[int],
    *,
    min_purity: float,
    min_fidelity_fixed: int,
    state_path: Path,
) -> dict[str, Any]:
    if (
        IMPORT_ERROR is not None
        or PulviniOverlayConcentrator is None
        or PulviniAutonomicsEngine is None
        or SubstateVerifier is None
    ):
        raise RuntimeError(
            "PULVINI live-cut simulation requires the Phase Transition numerical dependencies "
            f"(missing: {IMPORT_ERROR})"
        )
    overlay = PulviniOverlayConcentrator(worker_name="PULVINI.singularity")
    overlay.mark_pool_bound("PhaseTransitionPool", "stratum+tcp://phase-transition.local:3333", 2)
    job = SimpleNamespace(job_id="phase-transition-live-cut", target=1, extranonce2_size=4)
    overlay.register_pool_job(job, pool_name="PhaseTransitionPool")

    engine = PulviniAutonomicsEngine(lattice_repoint_sink=overlay.apply_lattice_repoint)
    engine.ingest_telemetry(_healthy_telemetry(node_id) for node_id in range(32))
    rebalance = engine.rebalancer.rebalance_lattice_topology(nodes, reason="simulated_live_cut")
    overlay.apply_autonomic_distribution(
        engine.homeostasis.rho.diagonal().tolist(), reason="simulated_live_cut"
    )

    verifier = SubstateVerifier()
    passport = verifier.generate_passport(
        target=int(getattr(job, "target", 0)),
        rho=engine.homeostasis.rho.rho,
        reference_rho=engine.homeostasis.rho.rho,
        timestamp_ns=time.time_ns(),
    )
    binary_header = passport.to_binary_header()
    fidelity_passed = passport.fidelity_fixed >= int(min_fidelity_fixed)

    overlay_snapshot = overlay.snapshot()
    autonomics_snapshot = engine.snapshot()
    state = {
        "running": True,
        "uptime_seconds": 0.0,
        "active_pool": overlay_snapshot["active_pool_name"],
        "active_pool_id": "phase_transition",
        "current_job_id": overlay_snapshot["active_job_id"],
        "current_job": overlay_snapshot["active_job_id"],
        "pool_visible_worker_identity": overlay_snapshot["worker_name"],
        "pool_visible_workers": overlay_snapshot["pool_visible_workers"],
        "internal_pulvini_nodes": overlay_snapshot["internal_nodes"],
        "system_health": "HEALING" if rebalance.coverage_maintained else "DEGRADED",
        "pulvini_overlay": overlay_snapshot,
        "pulvini_autonomics": autonomics_snapshot,
        "autonomic_repairs": 1,
        "latest_autonomic_event": rebalance.to_dict(),
        "substate_passport": {
            "binary_header_hex": binary_header.hex(),
            "binary_header_size": len(binary_header),
            "fidelity_fixed": passport.fidelity_fixed,
            "fidelity_passed": fidelity_passed,
            "magic": PULVINI_BINARY_MAGIC.decode("ascii"),
            "min_fidelity_fixed": int(min_fidelity_fixed),
            "passport_hash": passport.passport_hash,
            "purity_fixed": passport.purity_fixed,
            "rho_hash": passport.rho_hash,
            "topology_hash": passport.structural_hash,
        },
        "timestamp": time.time(),
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    report = evaluate_live_cut_state(
        state,
        mode="postcut",
        min_purity=min_purity,
        expected_severed_nodes=nodes,
        state_path=str(state_path),
    )
    readiness = report.to_dict()
    passed = bool(readiness["passed"] and fidelity_passed)
    return {
        "state_path": str(state_path),
        "severed_nodes": nodes,
        "manifold_purity": report.manifold_purity,
        "rho_trace": autonomics_snapshot["rho"]["trace"],
        "healing_ranges_overlap_free": overlay_snapshot["healing_ranges_overlap_free"],
        "pool_identity_stable": overlay_snapshot["pool_visible_workers"] == 1,
        "substate_passport": state["substate_passport"],
        "binary_header_size": PULVINI_BINARY_HEADER_SIZE,
        "fidelity_fixed": passport.fidelity_fixed,
        "fidelity_passed": fidelity_passed,
        "passed": passed,
        "readiness": readiness,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Simulate a PULVINI live-cut and report post-cut purity"
    )
    parser.add_argument(
        "--nodes",
        type=_parse_nodes,
        default=[0, 1, 2],
        help="Comma-separated node ids to cut",
    )
    parser.add_argument(
        "--state", type=Path, default=Path("python_backend/pythia_state.live_cut.json")
    )
    parser.add_argument("--min-purity", type=float, default=0.9)
    parser.add_argument("--min-fidelity-fixed", type=int, default=900_000_000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        payload = run_live_cut_drill(
            args.nodes,
            min_purity=args.min_purity,
            min_fidelity_fixed=args.min_fidelity_fixed,
            state_path=args.state,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should emit operator-safe error.
        print(f"PULVINI live-cut drill failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        status = "PASS" if payload["passed"] else "FAIL"
        print(f"PULVINI live-cut drill: {status}")
        print(f"state_path={payload['state_path']}")
        print(f"severed_nodes={payload['severed_nodes']}")
        print(f"manifold_purity={payload['manifold_purity']}")
        print(f"rho_trace={payload['rho_trace']}")
        print(f"healing_ranges_overlap_free={payload['healing_ranges_overlap_free']}")
        print(f"pool_identity_stable={payload['pool_identity_stable']}")
        print(f"binary_header_size={payload['binary_header_size']}")
        print(f"fidelity_fixed={payload['fidelity_fixed']}")
        print(f"fidelity_passed={payload['fidelity_passed']}")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
