from __future__ import annotations

from pythia_mining.metal_sha256_pipeline import (
    CPUParallelVerifier,
    UnifiedBatchVerifier,
    verify_nonce,
)
from pythia_mining.mining_validation import validate_share
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.stratum_client import MiningJob


def _job(target: int = 2**240) -> MiningJob:
    return MiningJob(
        job_id="metal-unit-job",
        prevhash="00" * 32,
        coinbase_parts=("", ""),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="5f5e1000",
        target=target,
        extranonce1="abcd",
        extranonce2_size=4,
    )


def test_verify_nonce_matches_canonical_share_validation() -> None:
    job = _job()
    nonce = 42

    direct = validate_share(job, nonce, "00" * job.extranonce2_size)
    checked = verify_nonce(job, nonce)

    assert checked.valid == direct.valid
    assert checked.block_hash == direct.block_hash
    assert checked.hash_int == direct.hash_int
    assert checked.target == direct.target
    assert checked.header_hex == direct.header_hex
    assert checked.backend == "cpu_parallel_exact_sha256d"


def test_cpu_parallel_verifier_returns_batch_metrics() -> None:
    job = _job()
    verifier = CPUParallelVerifier(workers=4)

    batch = verifier.verify_batch(job, [0, 1, 2, 3])

    assert batch.backend == "cpu_parallel_exact_sha256d"
    assert batch.total_nonces == 4
    assert batch.elapsed_seconds > 0
    assert batch.hashes_per_second > 0
    assert batch.hashrate_ehs >= 0
    assert batch.best_nonce in {0, 1, 2, 3}
    assert batch.best_hash is not None
    assert batch.accepted_count == len(batch.winners)


def test_unified_batch_verifier_falls_back_to_exact_cpu_without_metal() -> None:
    job = _job()
    verifier = UnifiedBatchVerifier(prefer_metal=False, cpu_workers=2)

    status = verifier.status()
    batch = verifier.verify_batch(job, [7, 8, 9])

    assert status["selected_backend"] == "cpu_parallel_exact_sha256d"
    assert batch.backend == "cpu_parallel_exact_sha256d"
    assert batch.total_nonces == 3
    assert verifier.last_batch is batch


def test_unified_engine_exposes_verifier_telemetry() -> None:
    job = _job()
    engine = UnifiedMiningEngine(configured_capacity_ehs=1.0)

    batch = engine.verify_batch(job, [11, 12, 13])
    candidate = engine.submit_candidate(job, 11)
    state = engine.get_unified_state()

    assert batch.total_nonces == 3
    assert candidate.nonce == 11
    assert state["state"]["verifier_backend"] in {
        "cpu_parallel_exact_sha256d",
        "metal_mlx_staged_exact_sha256d",
    }
    assert state["state"]["last_batch_size"] == 3
    assert state["state"]["last_batch_hashrate_hps"] > 0
    assert state["state"]["last_candidate_hash"] == candidate.block_hash
    assert state["verifier"]["configured_capacity_ehs"] == 1.0
    assert state["proofs"]["sha256d_external_oracle"] == "bitcoin_header_double_sha256_pool_target"
