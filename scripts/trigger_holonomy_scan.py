#!/usr/bin/env python3
"""
Trigger Multi-Agent Holonomy Scan Mission

Executes the holonomy scan using real MPS parallel transport.
Every number comes from actual computation — no analytic formulas
with φ baked in to guarantee a result.

Usage:
    python scripts/trigger_holonomy_scan.py [--sites N] [--bond D] [--steps K]
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "python_backend"
sys.path.insert(0, str(backend_path))

from pythia_mining.holonomy_scan_mission import (
    HolonomyScanMission,
    YANG_MILLS_THRESHOLD,
    EXPECTED_MASS_GAP,
)
from pythia_mining.holonomy_websocket_broadcaster import HolonomyWebSocketBroadcaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("hyba.holonomy_trigger")


async def main(
    num_sites: int, max_bond_dim: int, scan_resolution: int, loop_steps: int
) -> None:
    print("\n" + "=" * 78)
    print("HYBA FULLSTACK — Multi-Agent Holonomy Scan")
    print("Real MPS parallel transport. Every number is measured, not assumed.")
    print("=" * 78 + "\n")

    print("Configuration:")
    print(f"  MPS sites:       {num_sites}")
    print(f"  Bond dimension:  {max_bond_dim}")
    print(f"  Scan points:     {scan_resolution}")
    print(f"  Loop steps:      {loop_steps}")
    print(f"  λ range:         [0.4, 0.6]")
    print(f"  Yang-Mills ref:  (3-φ) = {YANG_MILLS_THRESHOLD:.6f}")
    print(f"  Mass gap ref:    {EXPECTED_MASS_GAP:.6f} GeV\n")

    mission = HolonomyScanMission(
        num_sites=num_sites,
        max_bond_dim=max_bond_dim,
        scan_resolution=scan_resolution,
        loop_steps=loop_steps,
    )
    broadcaster = HolonomyWebSocketBroadcaster()

    print("Running mission...\n")
    result = await mission.execute_mission()

    d = result["diagnosis"]
    p = result["planning"]
    e = result["execution"]
    v = result["verification"]

    print("=" * 78)
    print("MISSION RESULTS")
    print("=" * 78 + "\n")

    print("Phase 1 — Diagnosis Agent")
    print(f"  λ* (QFI peak):        {d['lambda_critical']:.6f}")
    print(f"  QFI at λ*:            {d['qfi_at_critical']:.6f}")
    print(f"  d²QFI/dλ² at λ*:      {d['second_derivative_peak']:.4e}")
    print(f"  Scan points:          {d['scan_resolution']}")
    print()

    print("Phase 2 — Planning Agent")
    print(f"  SLD gradient norm:    {p['sld_gradient_norm']:.6f}")
    print(
        f"  Wilson action proxy:  {p['wilson_action']:.6f}  (ref: {YANG_MILLS_THRESHOLD:.6f})"
    )
    print(f"  Mass gap satisfied:   {p['mass_gap_satisfied']}")
    print()

    print("Phase 3 — Executor Agent")
    print(f"  Berry phase:          {e['berry_phase']:.6f} rad")
    print(f"  Chern number:         {e['chern_number']}")
    print(f"  Topological charge:   {e['topological_charge']:.6f}")
    print(f"  Transition detected:  {e['transition_detected']}")
    print(f"  Loop states:          {e['loop_states']}")
    print(f"  Min overlap:          {e['min_overlap']:.6f}")
    print()

    print("Phase 4 — Verification Agent")
    print(f"  Certificate:          {v.certificate_status}")
    print(f"  λ* validated:         {v.lambda_critical:.6f}")
    print(f"  Berry phase:          {v.berry_phase:.6f} rad")
    print(f"  Chern number:         {v.chern_number}")
    print(
        f"  Star-discrepancy:     {v.star_discrepancy:.4e}  (φ-bound: {v.phi_bound:.4e})"
    )
    print(f"  Within φ-bound:       {v.discrepancy_within_bound}")
    print(f"  Mass gap satisfied:   {v.mass_gap_satisfied}")
    print()

    # Broadcast
    print("Phase 5 — WebSocket Broadcast")
    await broadcaster.broadcast_topological_transition(
        room="CEO",
        lambda_critical=v.lambda_critical,
        chern_number=v.chern_number,
        berry_phase=v.berry_phase,
        certificate=v.certificate_status,
        wilson_action=v.wilson_action,
    )
    await broadcaster.broadcast_star_discrepancy_certificate(
        room="CEO",
        d_n_star=v.star_discrepancy,
        phi_bound=v.phi_bound,
        status="WITHIN_BOUND" if v.discrepancy_within_bound else "EXCEEDS_BOUND",
    )
    await broadcaster.broadcast_qfi_gradient_update(
        room="CEO",
        qfi_value=d["qfi_at_critical"],
        gradient_norm=p["sld_gradient_norm"],
        convergence_status=(
            "OPTIMAL" if v.certificate_status == "GOLDEN_OPTIMAL" else "PARTIAL"
        ),
    )
    await broadcaster.broadcast_resource_consumption(
        room="CTO",
        defect_count=0,
        pairing_weight=0.0,
        circuit_depth=loop_steps,
        compute_units=float(loop_steps * num_sites),
    )
    await broadcaster.broadcast_backpressure_flow(
        room="Dev",
        active_tasks=4,
        queue_depth=0,
        throughput=float(scan_resolution) / (result["elapsed_ms"] / 1000.0),
        latency_ms=result["elapsed_ms"],
    )
    print("  CEO terminal: topological transition")
    print("  CEO terminal: star-discrepancy certificate")
    print("  CEO terminal: QFI gradient")
    print("  CTO terminal: resource consumption")
    print("  Dev terminal: flow metrics")

    print()
    print("=" * 78)
    cert = v.certificate_status
    if cert == "GOLDEN_OPTIMAL":
        print("RESULT: GOLDEN_OPTIMAL")
        print(f"  Chern {v.chern_number}, Berry phase {v.berry_phase:.4f} rad")
        print("  Mass gap satisfied. Star-discrepancy within φ-LCG bound.")
    elif cert == "PARTIAL":
        print("RESULT: PARTIAL")
        print(f"  Chern {v.chern_number}, Berry phase {v.berry_phase:.4f} rad")
        print("  Topology detected. Mass gap or discrepancy criterion not fully met.")
        print(
            "  Increase loop_steps or bond dimension before promoting to GOLDEN_OPTIMAL."
        )
    else:
        print("RESULT: NOT_ELEVATED")
        print(f"  Chern {v.chern_number}, Berry phase {v.berry_phase:.4f} rad")
        print("  No non-trivial topology detected at this resolution.")
        print("  Try larger num_sites, bond dimension, or scan resolution.")

    print()
    print(f"Elapsed: {result['elapsed_ms']:.1f} ms")
    print()
    print("Claim boundary:")
    print(f"  {v.claim_boundary}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sites",
        type=int,
        default=16,
        help="MPS sites (default 16, use 50+ for higher resolution)",
    )
    parser.add_argument(
        "--bond", type=int, default=8, help="MPS bond dimension (default 8)"
    )
    parser.add_argument(
        "--scan", type=int, default=20, help="Number of λ scan points (default 20)"
    )
    parser.add_argument(
        "--steps", type=int, default=16, help="Berry phase loop steps (default 16)"
    )
    args = parser.parse_args()
    asyncio.run(main(args.sites, args.bond, args.scan, args.steps))
