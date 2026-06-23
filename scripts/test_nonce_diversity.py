#!/usr/bin/env python3
"""Test nonce diversity after φ-tiled full space exploration fix."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver
from pythia_mining.pulvini_nonce_compression import build_pulvini_nonce_plan


def test_nonce_diversity():
    """Verify that nonce generation explores full 2^32 space without cycling."""
    print("=" * 70)
    print("NONCE DIVERSITY TEST")
    print("=" * 70)

    # Create solver
    solver = PulviniCompressedQuantumSolver()

    # Build compressed plan
    plan = build_pulvini_nonce_plan()
    print(
        f"\nCompressed plan: {plan.working_set_dimension} coordinates, {plan.original_lanes} original lanes"
    )

    # Configure solver
    import asyncio

    async def configure():
        await solver.configure_compressed_search(
            0x00000000FFFF0000000000000000000000000000000000000000000000000000, plan
        )

    asyncio.run(configure())

    # Generate 1000 nonces and check diversity
    nonces = []
    for i in range(1000):
        solver._solve_counter = i
        # Simulate the coordinate collapse and walk
        coordinate = solver._collapse_coordinate()
        walked = solver._walk_coordinate(coordinate, max_iterations=100)
        nonce = solver._tunnel_anneal_project_nonce(walked)
        nonces.append(nonce)

    # Check diversity
    unique_nonces = len(set(nonces))
    print(f"\nGenerated {len(nonces)} nonces")
    print(f"Unique nonces: {unique_nonces}")
    print(f"Diversity ratio: {unique_nonces / len(nonces):.2%}")

    # Check if we're cycling through only ~20 values
    if unique_nonces < 50:
        print(
            "\n❌ FAIL: Nonce diversity is too low - likely cycling through small set"
        )
        return False
    else:
        print(f"\n✅ PASS: Nonce diversity is good ({unique_nonces} unique values)")

    # Check distribution across 2^32 space
    min_nonce = min(nonces)
    max_nonce = max(nonces)
    print(f"\nNonce range: {min_nonce} to {max_nonce}")
    print(f"Range coverage: {(max_nonce - min_nonce) / 2**32:.2%} of full space")

    # Check for clustering in small regions
    sorted_nonces = sorted(nonces)
    gaps = [
        sorted_nonces[i + 1] - sorted_nonces[i] for i in range(len(sorted_nonces) - 1)
    ]
    avg_gap = sum(gaps) / len(gaps) if gaps else 0
    print(f"Average gap between consecutive nonces: {avg_gap:.0f}")

    # Expected average gap for uniform distribution across 2^32 with 1000 samples
    expected_gap = 2**32 / 1000
    print(f"Expected gap for uniform distribution: {expected_gap:.0f}")

    if avg_gap < expected_gap * 0.1:
        print("\n⚠️  WARNING: Nonces are clustered in small region")
    else:
        print("\n✅ Nonces are well-distributed across space")

    # Check the solver metrics
    metrics = solver.get_metrics()
    print(f"\nSolver exploration mode: {metrics.get('exploration_mode', 'unknown')}")
    print(
        f"Compressed working set size: {metrics.get('compressed_working_set_size', 'unknown')}"
    )
    print(f"Retained kernel lanes: {metrics.get('retained_kernel_lanes', 'unknown')}")

    if metrics.get("exploration_mode") == "phi_tiled_van_der_corput_full_2e32":
        print("\n✅ PASS: Exploration mode is correctly set to full space")
    else:
        print(f"\n❌ FAIL: Exploration mode is {metrics.get('exploration_mode')}")
        return False

    if metrics.get("compressed_working_set_size") == 2**32:
        print("✅ PASS: Working set size is full 2^32")
    else:
        print(
            f"❌ FAIL: Working set size is {metrics.get('compressed_working_set_size')}"
        )
        return False

    print("\n" + "=" * 70)
    print("NONCE DIVERSITY TEST COMPLETE")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_nonce_diversity()
    sys.exit(0 if success else 1)
