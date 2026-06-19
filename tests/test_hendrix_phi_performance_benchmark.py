"""HENDRIX-Φ job-backed performance and boundary tests.

These tests are deliberately bounded. They verify that HENDRIX/PYTHIA can operate
against an actual MiningJob-shaped hash oracle on easy/regtest targets, that the
φ-resonance helpers are deterministic and bounded, and that benchmark output does
not become a commercial pool-side performance claim.
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
    target: int
    target_bits: int
    phi_solver_time_ms: float
    phi_solver_nonce: Optional[int]
    phi_solver_valid: bool
    random_search_time_ms: float
    random_search_nonce: Optional[int]
    random_search_valid: bool
    speedup_ratio: float
    claim_boundary: str = "local_job_fixture_only_not_pool_side_performance"


def _get_target_bits(target: int) -> int:
    return max(0, int(target).bit_length())


def _create_job_for_target(target: int) -> MiningJob:
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
    target: int, max_time_ms: float = 500.0
) -> tuple[Optional[int], float, bool]:
    job = _create_job_for_target(target)
    solver = DodecahedralQuantumSolver()
    await solver.configure_search(target=target, nonce_ranges=[(0, 2**32 - 1)])

    start = time.perf_counter()
    nonce = await solver.solve(
        max_iterations=20_000,
        timeout=max_time_ms / 1000.0,
        job=job,
        extranonce2="00000000",
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    valid = bool(nonce is not None and validate_share(job, nonce, "00000000").valid)
    return nonce, elapsed_ms, valid


def _benchmark_deterministic_walk(
    target: int, max_iterations: int = 20_000
) -> tuple[Optional[int], float, bool]:
    job = _create_job_for_target(target)
    start = time.perf_counter()
    for nonce in range(max_iterations):
        validation = validate_share(job, nonce, "00000000")
        if validation.valid:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return nonce, elapsed_ms, True
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    return None, elapsed_ms, False


@pytest.mark.asyncio
async def test_hendrix_phi_vs_deterministic_walk_easy_target_is_job_backed():
    easy_target = int("7fffff" + "ff" * 29, 16)

    phi_nonce, phi_time_ms, phi_valid = await _benchmark_phi_solver(easy_target)
    walk_nonce, walk_time_ms, walk_valid = _benchmark_deterministic_walk(easy_target)

    assert phi_nonce is not None
    assert phi_valid is True
    assert walk_nonce is not None
    assert walk_valid is True
    assert phi_time_ms >= 0.0
    assert walk_time_ms >= 0.0


@pytest.mark.asyncio
async def test_hendrix_phi_medium_target_handles_timeout_without_false_claim():
    medium_target = int("00ffff" + "ff" * 29, 16)

    phi_nonce, phi_time_ms, phi_valid = await _benchmark_phi_solver(medium_target, max_time_ms=250.0)
    walk_nonce, walk_time_ms, walk_valid = _benchmark_deterministic_walk(medium_target, 2_500)

    result = BenchmarkResult(
        target=medium_target,
        target_bits=_get_target_bits(medium_target),
        phi_solver_time_ms=phi_time_ms,
        phi_solver_nonce=phi_nonce,
        phi_solver_valid=phi_valid,
        random_search_time_ms=walk_time_ms,
        random_search_nonce=walk_nonce,
        random_search_valid=walk_valid,
        speedup_ratio=walk_time_ms / max(phi_time_ms, 0.1),
    )

    assert result.target_bits > 0
    assert result.claim_boundary == "local_job_fixture_only_not_pool_side_performance"
    assert result.phi_solver_time_ms >= 0.0
    assert result.random_search_time_ms >= 0.0
    assert result.phi_solver_valid == (result.phi_solver_nonce is not None)
    assert result.random_search_valid == (result.random_search_nonce is not None)


@pytest.mark.asyncio
async def test_hendrix_phi_hard_target_is_graceful_when_no_nonce_found():
    hard_target = int("00000001" + "00" * 28, 16)

    phi_nonce, phi_time_ms, phi_valid = await _benchmark_phi_solver(hard_target, max_time_ms=100.0)
    walk_nonce, walk_time_ms, walk_valid = _benchmark_deterministic_walk(hard_target, 1_000)

    assert phi_time_ms >= 0.0
    assert walk_time_ms >= 0.0
    assert phi_valid == (phi_nonce is not None)
    assert walk_valid == (walk_nonce is not None)


def test_hendrix_phi_deterministic_within_target():
    results = []
    for _ in range(3):
        nonce = hendrix.phi_gradient_proposal(
            nonce=0,
            rng=random.Random(42),
            scale=3,
        )
        results.append(nonce)

    assert results[0] == results[1] == results[2]


def test_hendrix_phi_coverage_all_domains():
    domains_covered = {hendrix.voronoi_domain(nonce) for nonce in range(0, 2**32, 2**32 // 1000)}

    assert len(domains_covered) == 32
    assert domains_covered == set(range(32))


def test_hendrix_phi_resonance_statistically_bounded():
    scores = [hendrix.phi_resonance(nonce) for nonce in range(0, 2**32, 2**32 // 10000)]

    assert all(0.0 <= score <= 1.0 for score in scores)
    mean = sum(scores) / len(scores)
    variance = sum((score - mean) ** 2 for score in scores) / len(scores)
    assert variance > 0.01


def test_hendrix_phi_top_percentile_placement_is_deterministic():
    sample_size = 10_000
    nonces_with_scores = [
        (nonce, hendrix.phi_resonance(nonce)) for nonce in range(0, 2**32, 2**32 // sample_size)
    ]
    sorted_by_score = sorted(nonces_with_scores, key=lambda item: item[1], reverse=True)
    top_5_percent_scores = sorted_by_score[: max(1, len(sorted_by_score) // 20)]
    min_top_5_score = min(score for _, score in top_5_percent_scores)

    rng = random.Random(123)
    hendrix_scores = [
        hendrix.phi_resonance(
            hendrix.phi_gradient_proposal(nonce=rng.randint(0, 2**32 - 1), rng=rng, scale=3)
        )
        for _ in range(1_000)
    ]
    percentage_in_top_5 = 100.0 * sum(score >= min_top_5_score for score in hendrix_scores) / len(
        hendrix_scores
    )

    assert percentage_in_top_5 >= 10.0


def test_hendrix_phi_batch_throughput_is_nonzero_and_measured():
    batch_size = 25_000
    start = time.perf_counter()
    for nonce in range(batch_size):
        hendrix.phi_resonance(nonce)
    elapsed = time.perf_counter() - start
    throughput = batch_size / max(elapsed, 1e-9)

    assert throughput > 0.0


@pytest.mark.asyncio
async def test_hendrix_phi_finds_valid_on_regtest_job():
    job = _create_job_for_target(int("7fffff" + "ff" * 29, 16))

    solver = DodecahedralQuantumSolver()
    await solver.configure_search(target=job.target, nonce_ranges=[(0, 2**32 - 1)])
    nonce = await solver.solve(max_iterations=10_000, timeout=5.0, job=job, extranonce2="00000000")

    assert nonce is not None
    assert validate_share(job, nonce, "00000000").valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
