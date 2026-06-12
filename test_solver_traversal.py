#!/usr/bin/env python3
"""
Solver Traversal Verification Test

Verifies that the quantum solver is actually traversing the compressed plan
and not short-circuiting to a cached nonce.
"""

import sys
import asyncio
from pathlib import Path
from typing import Set

ROOT = Path(__file__).resolve().parents[0]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import numpy as np

# Turn warnings into hard failures
np.seterr(all='raise')

from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver
from pythia_mining.pulvini_nonce_compression import PulviniNonceSpaceCompressor
from pythia_mining.pulvini_overlay import PulviniOverlayConcentrator
from pythia_mining.stratum_client import MiningJob


async def test_solver_traversal():
    """Test that solver traverses compressed plan and doesn't short-circuit."""
    print("=" * 70)
    print("SOLVER TRAVERSAL VERIFICATION TEST")
    print("=" * 70)
    
    # Initialize components
    overlay = PulviniOverlayConcentrator(worker_name="PULVINI.traversal_test")
    solver = PulviniCompressedQuantumSolver()
    
    # Create a test job
    job = MiningJob(
        job_id="traversal_test_001",
        prevhash="00" * 32,
        coinbase_parts=("test", "coinbase"),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="5e9a5c00",
        target=1,
        extranonce1="abcd",
        extranonce2_size=4,
    )
    
    # Register job with overlay
    overlay.register_pool_job(job, pool_name="TestPool")
    
    # Get nonce plan
    plan = overlay.nonce_plan
    print(f"\nNonce Plan:")
    print(f"  Working set dimension: {plan.working_set_dimension}")
    print(f"  Compression ratio: {plan.working_set_compression_ratio:.2f}x")
    print(f"  Complete coverage: {plan.complete_coverage}")
    print(f"  Overlap-free: {plan.overlap_free}")
    
    # Configure solver with compressed plan
    await solver.configure_compressed_search(job.target, plan)
    print(f"\n✓ Solver configured with compressed plan")
    
    # Run multiple solves to check for nonce consistency
    print(f"\nRunning multiple solves to check for nonce consistency...")
    nonces: Set[int] = set()
    solve_times: list[float] = []
    
    for i in range(10):
        import time
        start = time.perf_counter()
        nonce = await solver.solve(max_iterations=16, timeout=5.0)
        end = time.perf_counter()
        solve_time = (end - start) * 1000  # Convert to ms
        
        nonces.add(nonce)
        solve_times.append(solve_time)
        print(f"  Run {i+1}: nonce={nonce}, time={solve_time:.2f}ms")
    
    # Analyze results
    print(f"\nTraversal Analysis:")
    print(f"  Unique nonces found: {len(nonces)}")
    print(f"  Total solves: {len(solve_times)}")
    print(f"  Mean solve time: {np.mean(solve_times):.2f}ms")
    print(f"  Std dev solve time: {np.std(solve_times):.2f}ms")
    print(f"  Min solve time: {np.min(solve_times):.2f}ms")
    print(f"  Max solve time: {np.max(solve_times):.2f}ms")
    
    # Check for short-circuiting
    print(f"\nShort-Circuit Detection:")
    if len(nonces) == 1:
        print(f"  ✗ SHORT-CIRCUIT DETECTED: Same nonce {list(nonces)[0]} in all runs")
        print(f"  → Solver may be using cached nonce instead of traversing plan")
        return False
    elif len(nonces) < 5:
        print(f"  ⚠ LOW NONCE VARIETY: Only {len(nonces)} unique nonces in 10 runs")
        print(f"  → Possible partial short-circuiting or limited search space")
        return False
    else:
        print(f"  ✓ NO SHORT-CIRCUIT: {len(nonces)} unique nonces in 10 runs")
        print(f"  → Solver is genuinely traversing the compressed plan")
    
    # Check solve time consistency
    if np.std(solve_times) < 0.1:
        print(f"  ⚠ SUSPICIOUSLY CONSISTENT TIMING: std dev {np.std(solve_times):.3f}ms")
        print(f"  → May indicate cached computation")
    else:
        print(f"  ✓ NATURAL TIMING VARIATION: std dev {np.std(solve_times):.3f}ms")
        print(f"  → Consistent with genuine computation")
    
    # Check solve time is reasonable for actual traversal
    mean_time = np.mean(solve_times)
    if mean_time < 0.1:
        print(f"  ✗ SUSPICIOUSLY FAST: {mean_time:.3f}ms mean")
        print(f"  → Likely short-circuiting to cached nonce")
        return False
    elif mean_time > 100:
        print(f"  ⚠ SLOW TRAVERSAL: {mean_time:.2f}ms mean")
        print(f"  → May be traversing full space without compression benefits")
    else:
        print(f"  ✓ REASONABLE TIMING: {mean_time:.2f}ms mean")
        print(f"  → Consistent with compressed plan traversal")
    
    print("\n" + "=" * 70)
    print("TRAVERSAL VERIFICATION COMPLETE")
    print("=" * 70)
    
    return len(nonces) >= 5 and mean_time >= 0.1


if __name__ == "__main__":
    success = asyncio.run(test_solver_traversal())
    sys.exit(0 if success else 1)
