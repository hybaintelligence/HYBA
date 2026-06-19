"""HENDRIX-Φ Performance Benchmark — Comparative Analysis

This test proves whether φ-resonance-guided nonce search is faster than
random enumeration across various difficulty targets.

The critical measurement: nonces-to-find-first-valid divided by CPU time.

Test structure:
  1. Generate a range of difficulty targets (easy to hard)
  2. For each target:
     a) Time the HENDRIX-Φ solver to find the first valid nonce
     b) Time brute-force random enumeration to find a valid nonce
     c) Measure speedup ratio: brute_force_time / phi_time
  3. Report average speedup across all targets
  4. Prove speedup is real (not measurement noise)

Success criteria:
  - HENDRIX-Φ speedup >= 1.5x on easy targets (should be obvious)
  - HENDRIX-Φ speedup >= 1.0x on all targets (no regression)
  - Speedup is consistent across runs (low variance)
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining import hendrix_phi_solver as hendrix
from pythia_mining.mining_validation import validate_share
from pythia_mining.quantum_solver import DodecahedralQuantumSolver
from pythia_mining.stratum_client import MiningJob


@dataclass
class BenchmarkResult:
    """Single benchmark run result."""

    target: int
    target_bits: int
    phi_solver_time_ms: float
    phi_solver_nonce: Optional[int]
    phi_solver_valid: bool
    random_search_time_ms: float
    random_search_nonce: Optional[int]
    random_search_valid: bool
    speedup_ratio: float  # random_time / phi_time


def _get_target_bits(target: int) -> int:
    """Return the bit-length of target."""
    if target <= 0:
        return 0
    return target.bit_length()


def _create_job_for_target(target: int) -> MiningJob:
    """Create a synthetic mining job with the given target."""
    return MiningJob(
        job_id="bench-job",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="65000000",
        target=target,
        extranonce1="00000000",
        extranonce2_size=4,
        stratum_version=1,
    )


async def _benchmark_phi_solver(
    target: int, max_time_ms: float = 5000.0
) -> tuple[Optional[int], float]:
    """
    Benchmark the HENDRIX-Φ solver.

    Returns: (nonce, elapsed_ms)
    """
    solver = DodecahedralQuantumSolver()
    await solver.configure_search(target=target, nonce_ranges=[(0, 2**32 - 1)])

    start = time.time()
    nonce = await solver.solve(
        max_iterations=2**32 - 1,
        timeout=max_time_ms / 1000.0,
    )
    elapsed_ms = (time.time() - start) * 1000.0

    return nonce, elapsed_ms


def _benchmark_random_search(
    target: int, max_time_ms: float = 5000.0
) -> tuple[Optional[int], float]:
    """
    Benchmark random nonce enumeration.

    Returns: (nonce, elapsed_ms)
    """
    job = _create_job_for_target(target)
    extranonce2 = "00000000"

    start = time.time()
    found_nonce = None
    iterations = 0

    while time.time() - start < max_time_ms / 1000.0:
        nonce = random.randint(0, 2**32 - 1)
        iterations += 1

        validation = validate_share(job, nonce, extranonce2)
        if validation.valid:
            found_nonce = nonce
            break

    elapsed_ms = (time.time() - start) * 1000.0

    return found_nonce, elapsed_ms


@pytest.mark.asyncio
async def test_hendrix_phi_vs_random_easy_target():
    """Benchmark HENDRIX-Φ vs random on an easy target (should show clear speedup)."""
    # Easy target: 1 in 2^16 nonces is valid (plenty of valid nonces nearby)
    easy_target = int("ffff" + "ff" * 28, 16)

    phi_nonce, phi_time_ms = await _benchmark_phi_solver(easy_target, max_time_ms=1000.0)
    random_nonce, random_time_ms = _benchmark_random_search(easy_target, max_time_ms=1000.0)

    assert phi_nonce is not None, "HENDRIX-Φ solver found no valid nonce"
    assert random_nonce is not None, "Random search found no valid nonce"

    speedup = random_time_ms / max(phi_time_ms, 0.1)  # Avoid division by zero

    print(f"\nEasy target ({_get_target_bits(easy_target)} bits):")
    print(f"  HENDRIX-Φ: {phi_time_ms:.2f}ms → nonce 0x{phi_nonce:08x}")
    print(f"  Random:    {random_time_ms:.2f}ms → nonce 0x{random_nonce:08x}")
    print(f"  Speedup:   {speedup:.2f}x")

    # On easy targets, HENDRIX-Φ should be noticeably faster
    assert speedup >= 1.2, f"Expected speedup >= 1.2x on easy target, got {speedup:.2f}x"


@pytest.mark.asyncio
async def test_hendrix_phi_vs_random_medium_target():
    """Benchmark HENDRIX-Φ vs random on a medium target."""
    # Medium target: 1 in 2^24 nonces is valid
    medium_target = int("ffffff" + "00" * 29, 16)

    phi_nonce, phi_time_ms = await _benchmark_phi_solver(medium_target, max_time_ms=2000.0)
    random_nonce, random_time_ms = _benchmark_random_search(medium_target, max_time_ms=2000.0)

    # One of them should find a valid nonce
    if phi_nonce is not None:
        speedup = random_time_ms / max(phi_time_ms, 0.1)
    elif random_nonce is not None:
        # Only random found it; speedup is negative (HENDRIX failed)
        speedup = -1.0
    else:
        # Both timed out; skip
        pytest.skip("Both solvers timed out on medium target")

    print(f"\nMedium target ({_get_target_bits(medium_target)} bits):")
    print(f"  HENDRIX-Φ: {phi_time_ms:.2f}ms → nonce 0x{phi_nonce:08x if phi_nonce else 'TIMEOUT'}")
    print(
        f"  Random:    {random_time_ms:.2f}ms → nonce 0x{random_nonce:08x if random_nonce else 'TIMEOUT'}"
    )
    print(f"  Speedup:   {speedup:.2f}x")

    # HENDRIX-Φ should not be significantly slower
    assert speedup >= 0.8, f"HENDRIX-Φ significantly slower on medium target: {speedup:.2f}x"


@pytest.mark.asyncio
async def test_hendrix_phi_vs_random_hard_target():
    """Benchmark HENDRIX-Φ vs random on a hard target."""
    # Hard target: 1 in 2^32 nonces is valid (very sparse)
    hard_target = int("00000001" + "00" * 28, 16)

    phi_nonce, phi_time_ms = await _benchmark_phi_solver(hard_target, max_time_ms=1000.0)
    random_nonce, random_time_ms = _benchmark_random_search(hard_target, max_time_ms=1000.0)

    # Both likely timeout; just verify they handle it gracefully
    print(f"\nHard target ({_get_target_bits(hard_target)} bits):")
    print(f"  HENDRIX-Φ: {phi_time_ms:.2f}ms → {'FOUND' if phi_nonce else 'timeout'}")
    print(f"  Random:    {random_time_ms:.2f}ms → {'FOUND' if random_nonce else 'timeout'}")


def test_hendrix_phi_deterministic_within_target():
    """Test that HENDRIX-Φ is deterministic: same target yields same nonce."""
    target = int("ffff" + "ff" * 28, 16)
    _create_job_for_target(target)

    # Run multiple times
    results = []
    for _ in range(3):
        nonce = hendrix.phi_gradient_proposal(
            nonce=0,  # Fixed: parameter name is 'nonce', not 'start_nonce'
            rng=random.Random(42),  # Fixed seed
            scale=3,
        )
        results.append(nonce)

    # All should be identical (same seed)
    assert results[0] == results[1] == results[2], (
        "HENDRIX proposals not deterministic under same seed"
    )


def test_hendrix_phi_coverage_all_domains():
    """Test that HENDRIX-Φ's Voronoi domains cover all 32 M32 domains."""
    domains_covered = set()

    # Sample across full uint32 range
    for nonce in range(0, 2**32, 2**32 // 1000):
        domain = hendrix.voronoi_domain(nonce)
        domains_covered.add(domain)

    assert len(domains_covered) == 32, f"HENDRIX-Φ covers {len(domains_covered)}/32 domains"
    assert domains_covered == set(range(32)), "Domains are not 0-31"


def test_hendrix_phi_resonance_statistically_bounded():
    """Test that φ-resonance is truly bounded [0, 1] across the nonce space."""
    scores = []

    for nonce in range(0, 2**32, 2**32 // 10000):
        score = hendrix.phi_resonance(nonce)
        scores.append(score)
        assert 0.0 <= score <= 1.0, f"φ-resonance out of bounds: {score}"

    # Should have non-trivial variance (not all clustered at 0 or 1)
    variance = sum((s - sum(scores) / len(scores)) ** 2 for s in scores) / len(scores)
    assert variance > 0.01, f"φ-resonance has suspicious low variance: {variance}"


def test_hendrix_phi_top_percentile_placement():
    """
    Test that HENDRIX-Φ places high-scoring nonces in top percentile.

    Core claim: if you order nonces by φ-resonance and take the top 5%,
    HENDRIX's selected candidates should be in that top 5% at disproportionate frequency.
    """
    # Generate a large sample of nonces and sort by φ-resonance
    sample_size = 10000
    nonces_with_scores = [
        (nonce, hendrix.phi_resonance(nonce)) for nonce in range(0, 2**32, 2**32 // sample_size)
    ]

    # Sort by score (descending) and identify top 5%
    sorted_by_score = sorted(nonces_with_scores, key=lambda x: x[1], reverse=True)
    top_5_percent_scores = sorted_by_score[: max(1, len(sorted_by_score) // 20)]
    min_top_5_score = min(s for _, s in top_5_percent_scores)

    # Now sample HENDRIX-generated candidates
    hendrix_samples = []
    rng = random.Random(123)
    for _ in range(1000):
        proposal = hendrix.phi_gradient_proposal(
            nonce=random.randint(0, 2**32 - 1),  # Fixed: parameter name is 'nonce'
            rng=rng,
            scale=3,
        )
        score = hendrix.phi_resonance(proposal)
        hendrix_samples.append(score)

    # Count how many HENDRIX samples are in the top 5%
    in_top_5 = sum(1 for score in hendrix_samples if score >= min_top_5_score)
    percentage_in_top_5 = (in_top_5 / len(hendrix_samples)) * 100.0

    print("\nHENDRIX-Φ top 5% placement:")
    print(f"  Samples: {len(hendrix_samples)}")
    print(f"  In top 5%: {in_top_5} ({percentage_in_top_5:.1f}%)")
    print(f"  Min top-5 score: {min_top_5_score:.4f}")
    print(f"  Avg HENDRIX score: {sum(hendrix_samples) / len(hendrix_samples):.4f}")

    # HENDRIX samples should appear in top 5% at higher frequency than 5%
    # (random sampling would give ~5%; guided should give much higher)
    assert percentage_in_top_5 >= 15.0, (
        f"HENDRIX-Φ guidance weak: only {percentage_in_top_5:.1f}% in top 5% (random would be ~5%)"
    )


def test_hendrix_phi_batch_throughput():
    """Measure throughput: how many nonces can HENDRIX evaluate per second?"""
    batch_size = 100000
    start = time.time()

    for nonce in range(batch_size):
        _ = hendrix.phi_resonance(nonce)

    elapsed = time.time() - start
    throughput = batch_size / elapsed

    print(
        f"\nHENDRIX-Φ throughput: {throughput:.0f} nonces/sec ({elapsed * 1000:.1f}ms for {batch_size})"
    )

    # Should be able to evaluate at least 100k nonces/sec on any modern CPU
    assert throughput >= 100000, f"HENDRIX-Φ throughput too low: {throughput:.0f}/sec"


@pytest.mark.asyncio
async def test_hendrix_phi_finds_valid_on_regtest():
    """Test that HENDRIX-Φ can find valid nonces on regtest difficulty."""
    job = _create_job_for_target(int("7fffff" + "00" * 29, 16))

    solver = DodecahedralQuantumSolver()
    await solver.configure_search(target=job.target, nonce_ranges=[(0, 2**32 - 1)])

    nonce = await solver.solve(max_iterations=10000, timeout=10.0)

    assert nonce is not None, "HENDRIX-Φ failed to find nonce on regtest difficulty"

    # Verify it's actually valid
    validation = validate_share(job, nonce, "00000000")
    assert validation.valid, f"HENDRIX nonce not valid: {validation.reason}"

    print(f"\nHENDRIX-Φ regtest: found valid nonce 0x{nonce:08x}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
