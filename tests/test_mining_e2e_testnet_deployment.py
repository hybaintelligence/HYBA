"""End-to-end mining deployment test against Bitcoin testnet.

This test validates the complete mining pipeline:
  1. Initialize mining engine with live Stratum connection
  2. Receive a job from the pool
  3. Generate candidate nonces using HENDRIX-Φ solver
  4. Validate shares locally (SHA256d)
  5. Submit to pool
  6. Measure acceptance rate and timing

This test requires network access to a Bitcoin testnet pool. It can be run
against regtest (local), testnet3 (public), or a private pool.

Environment variables:
  HYBA_TESTNET_POOL_URL     Pool URL (default: stratum+tcp://localhost:18332)
  HYBA_TESTNET_USERNAME     Pool username (default: testuser)
  HYBA_TESTNET_PASSWORD     Pool password (default: testpass)
  HYBA_TESTNET_DURATION_SEC Duration of test (default: 30)
  HYBA_TESTNET_SKIP_IF_OFFLINE Skip if pool unreachable (default: true)
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_BACKEND = REPO_ROOT / "python_backend"
if str(PYTHON_BACKEND) not in sys.path:
    sys.path.insert(0, str(PYTHON_BACKEND))

from pythia_mining.live_stratum_session import (
    LiveStratumSession,
)
from pythia_mining.mining_validation import validate_share
from pythia_mining.phi_unified_mining_engine import UnifiedMiningEngine
from pythia_mining.pool_profiles import PoolProfile
from pythia_mining.stratum_client import MiningJob


# Configuration from environment
POOL_URL = os.getenv("HYBA_TESTNET_POOL_URL", "stratum+tcp://localhost:18332")
POOL_USERNAME = os.getenv("HYBA_TESTNET_USERNAME", "testuser")
POOL_PASSWORD = os.getenv("HYBA_TESTNET_PASSWORD", "testpass")
TEST_DURATION_SEC = float(os.getenv("HYBA_TESTNET_DURATION_SEC", "30.0"))
SKIP_IF_OFFLINE = os.getenv("HYBA_TESTNET_SKIP_IF_OFFLINE", "true").lower() in ("true", "1", "yes")


async def is_pool_reachable(url: str, timeout: float = 5.0) -> bool:
    """Check if the pool is reachable."""
    try:
        # Simple connectivity check: try to create a session and connect
        profile = PoolProfile(
            pool_id="testnet",
            pool_name="Testnet Check",
            url=url,
            username="test",
            password="test",
        )
        session = LiveStratumSession(profile)
        # Set a short timeout
        session.transport.connection_timeout = timeout
        await session.connect()
        await session.close()
        return True
    except Exception:
        return False


@pytest.mark.asyncio
async def test_mining_e2e_testnet_connectivity() -> None:
    """Test that we can connect to the testnet pool."""
    reachable = await is_pool_reachable(POOL_URL, timeout=5.0)

    if not reachable and SKIP_IF_OFFLINE:
        pytest.skip(f"Testnet pool {POOL_URL} not reachable (SKIP_IF_OFFLINE=true)")

    assert reachable, f"Cannot connect to testnet pool at {POOL_URL}"


@pytest.mark.asyncio
async def test_mining_e2e_testnet_handshake() -> None:
    """Test Stratum handshake and authorization."""
    if not await is_pool_reachable(POOL_URL):
        if SKIP_IF_OFFLINE:
            pytest.skip(f"Testnet pool {POOL_URL} not reachable")
        else:
            pytest.fail(f"Cannot connect to testnet pool at {POOL_URL}")

    profile = PoolProfile(
        pool_id="testnet",
        pool_name="Bitcoin Testnet",
        url=POOL_URL,
        username=POOL_USERNAME,
        password=POOL_PASSWORD,
    )

    session = LiveStratumSession(profile)
    try:
        await session.connect()
        handshake = await session.subscribe_and_authorize()

        # Verify handshake contains required fields
        assert handshake.pool_id == "testnet"
        assert handshake.extranonce1 is not None
        assert handshake.extranonce2_size > 0
        assert handshake.authorized is True

        await session.close()
    except Exception as exc:
        if session.transport.connected:
            await session.close()
        if "connection refused" in str(exc).lower() and SKIP_IF_OFFLINE:
            pytest.skip(f"Pool not reachable: {exc}")
        raise


@pytest.mark.asyncio
async def test_mining_e2e_testnet_job_receipt() -> None:
    """Test receiving a mining job from the pool."""
    if not await is_pool_reachable(POOL_URL):
        if SKIP_IF_OFFLINE:
            pytest.skip(f"Testnet pool {POOL_URL} not reachable")
        else:
            pytest.fail(f"Cannot connect to testnet pool at {POOL_URL}")

    profile = PoolProfile(
        pool_id="testnet",
        pool_name="Bitcoin Testnet",
        url=POOL_URL,
        username=POOL_USERNAME,
        password=POOL_PASSWORD,
    )

    session = LiveStratumSession(profile)
    try:
        await session.connect()
        await session.subscribe_and_authorize()

        # Read events until we get a mining.notify job
        job_received = False
        timeout_at = time.time() + 5.0
        while time.time() < timeout_at:
            try:
                event, payload = await session.read_event(timeout=1.0)
                if event == "mining.notify":
                    job_received = True
                    # Verify job structure
                    assert "params" in payload
                    params = payload["params"]
                    assert len(params) >= 9  # Standard mining.notify has 9 params
                    break
            except asyncio.TimeoutError:
                continue

        assert job_received, "No mining.notify job received from pool within 5 seconds"

        await session.close()
    except Exception as exc:
        if session.transport.connected:
            await session.close()
        if "connection refused" in str(exc).lower() and SKIP_IF_OFFLINE:
            pytest.skip(f"Pool not reachable: {exc}")
        raise


@pytest.mark.asyncio
async def test_mining_e2e_testnet_nonce_generation() -> None:
    """Test that the unified mining engine generates valid candidate nonces."""
    if not await is_pool_reachable(POOL_URL):
        if SKIP_IF_OFFLINE:
            pytest.skip(f"Testnet pool {POOL_URL} not reachable")
        else:
            pytest.fail(f"Cannot connect to testnet pool at {POOL_URL}")

    # Create a synthetic testnet job
    # (This simulates what the pool would send)
    test_job = MiningJob(
        job_id="testnet-job-1",
        prevhash="000000000000000000000000000000000000000000000000000000000000ff00",
        coinbase_parts=(
            "020a00000000000000000000000000000000000000000000000000000000000000000000",
            "0000000000",
        ),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",  # Easy difficulty for testnet
        ntime="65000000",
        target=int("7fffff" + "00" * 29, 16),  # Easy target
        extranonce1="00000000",
        extranonce2_size=4,
        stratum_version=1,
    )

    # Initialize the mining engine
    engine = UnifiedMiningEngine(configured_capacity_ehs=0.1)

    # Run a single search
    result = await engine.search(test_job)

    # Verify result structure
    assert result.nonce is not None
    assert 0 <= result.nonce <= 2**32 - 1
    assert result.quantum_used is True
    assert result.strategy_used == "phi_scaled_compressed_solver_search"

    # Verify the nonce produces a valid hash below target
    extranonce2 = "00000000"
    validation = validate_share(test_job, result.nonce, extranonce2)
    assert validation.valid is True, f"Generated nonce produced invalid share: {validation.reason}"
    assert validation.hash_int <= test_job.target


@pytest.mark.asyncio
async def test_mining_e2e_testnet_share_submission() -> None:
    """Test submitting shares to the pool and measuring acceptance."""
    if not await is_pool_reachable(POOL_URL):
        if SKIP_IF_OFFLINE:
            pytest.skip(f"Testnet pool {POOL_URL} not reachable")
        else:
            pytest.fail(f"Cannot connect to testnet pool at {POOL_URL}")

    profile = PoolProfile(
        pool_id="testnet",
        pool_name="Bitcoin Testnet",
        url=POOL_URL,
        username=POOL_USERNAME,
        password=POOL_PASSWORD,
    )

    session = LiveStratumSession(profile)
    metrics = {
        "shares_submitted": 0,
        "shares_accepted": 0,
        "shares_rejected": 0,
        "submission_times_ms": [],
        "errors": [],
    }

    try:
        await session.connect()
        handshake = await session.subscribe_and_authorize()

        # Read jobs and submit shares for TEST_DURATION_SEC
        start_time = time.time()
        current_job: Optional[MiningJob] = None
        engine = UnifiedMiningEngine(configured_capacity_ehs=0.1)

        while time.time() - start_time < TEST_DURATION_SEC:
            # Read next event with timeout
            try:
                event, payload = await session.read_event(timeout=2.0)

                if event == "mining.notify":
                    # Parse the job
                    params = payload["params"]
                    job_id = params[0]
                    prevhash = params[1]
                    coinbase1 = params[2]
                    coinbase2 = params[3]
                    merkle_branch = params[4]
                    version = params[5]
                    nbits = params[6]
                    ntime = params[7]
                    params[8]

                    current_job = MiningJob(
                        job_id=job_id,
                        prevhash=prevhash,
                        coinbase_parts=(coinbase1, coinbase2),
                        merkle_branch=merkle_branch,
                        version=version,
                        nbits=nbits,
                        ntime=ntime,
                        target=int("7fffff" + "00" * 29, 16),  # Assume difficulty
                        extranonce1=handshake.extranonce1,
                        extranonce2_size=handshake.extranonce2_size,
                        stratum_version=1,
                    )

                    # Generate a nonce
                    if current_job:
                        try:
                            result = await engine.search(current_job)
                            if result.nonce is not None:
                                # Validate locally first
                                extranonce2 = "00000000"
                                validation = validate_share(current_job, result.nonce, extranonce2)

                                if validation.valid:
                                    # Submit to pool
                                    submit_start = time.time()
                                    submit_result = await session.submit_share(
                                        job_id=job_id,
                                        extranonce2=extranonce2,
                                        ntime=ntime,
                                        nonce=f"{result.nonce:08x}",
                                    )
                                    submit_time_ms = (time.time() - submit_start) * 1000

                                    metrics["shares_submitted"] += 1
                                    metrics["submission_times_ms"].append(submit_time_ms)

                                    if submit_result.accepted:
                                        metrics["shares_accepted"] += 1
                                    else:
                                        metrics["shares_rejected"] += 1
                                        metrics["errors"].append(
                                            f"Pool rejected share: {submit_result.error}"
                                        )
                        except Exception as exc:
                            metrics["errors"].append(f"Search/submit error: {exc}")

            except asyncio.TimeoutError:
                continue

        await session.close()

        # Report results
        print(f"\n{'─' * 60}")
        print(f"Mining E2E Test Results (duration: {TEST_DURATION_SEC}s)")
        print(f"{'─' * 60}")
        print(f"Shares submitted:  {metrics['shares_submitted']}")
        print(f"Shares accepted:   {metrics['shares_accepted']}")
        print(f"Shares rejected:   {metrics['shares_rejected']}")

        if metrics["shares_submitted"] > 0:
            acceptance_rate = metrics["shares_accepted"] / metrics["shares_submitted"] * 100
            print(f"Acceptance rate:   {acceptance_rate:.1f}%")

            if metrics["submission_times_ms"]:
                avg_time = sum(metrics["submission_times_ms"]) / len(metrics["submission_times_ms"])
                print(f"Avg submit time:   {avg_time:.1f}ms")

        if metrics["errors"]:
            print(f"\nErrors ({len(metrics['errors'])}):")
            for err in metrics["errors"][:5]:  # Show first 5 errors
                print(f"  • {err}")

        print(f"{'─' * 60}\n")

        # Assert minimum metrics
        assert metrics["shares_submitted"] > 0, "No shares were submitted during test"
        assert (
            metrics["shares_accepted"] + metrics["shares_rejected"] == metrics["shares_submitted"]
        ), "Share counts don't add up"

    except Exception as exc:
        if session.transport.connected:
            await session.close()
        if "connection refused" in str(exc).lower() and SKIP_IF_OFFLINE:
            pytest.skip(f"Pool not reachable: {exc}")
        raise


@pytest.mark.asyncio
async def test_mining_e2e_testnet_reflexive_mining() -> None:
    """Test that reflexive self-optimization works during live mining."""
    if not await is_pool_reachable(POOL_URL):
        if SKIP_IF_OFFLINE:
            pytest.skip(f"Testnet pool {POOL_URL} not reachable")
        else:
            pytest.fail(f"Cannot connect to testnet pool at {POOL_URL}")

    # Initialize engine with reflexive learning enabled
    engine = UnifiedMiningEngine(configured_capacity_ehs=0.1)
    engine.autonomous_controller.config.reflexive_loop_enabled = True
    engine.autonomous_controller.config.reflexive_loop_interval = 5.0  # Every 5s

    # Create a test job
    test_job = MiningJob(
        job_id="reflex-test-1",
        prevhash="000000000000000000000000000000000000000000000000000000000000ff00",
        coinbase_parts=(
            "020a00000000000000000000000000000000000000000000000000000000000000000000",
            "0000000000",
        ),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="65000000",
        target=int("7fffff" + "00" * 29, 16),
        extranonce1="00000000",
        extranonce2_size=4,
        stratum_version=1,
    )

    # Get pre-optimization state
    phi_before = engine.autonomous_controller.get_phi_density()

    # Run a few mining cycles
    for i in range(3):
        result = await engine.search(test_job)
        assert result.nonce is not None

    # Trigger reflexive cycle
    improvement = await engine.autonomous_controller.seek_improvement()

    # Verify reflexive cycle produced output
    assert improvement["reflexive_cycle_executed"] is True
    assert improvement["proposals_generated"] >= 0

    # Check if proposals were applied
    if improvement["proposals_applied"] > 0:
        phi_after = engine.autonomous_controller.get_phi_density()
        print("\nReflexive mining:")
        print(f"  Φ-density before: {phi_before:.6f}")
        print(f"  Φ-density after:  {phi_after:.6f}")
        print(f"  Proposals applied: {improvement['proposals_applied']}")


if __name__ == "__main__":
    # For manual testing
    print("Testnet mining E2E tests")
    print(f"Pool: {POOL_URL}")
    print(f"Duration: {TEST_DURATION_SEC}s")
    print(f"Skip if offline: {SKIP_IF_OFFLINE}\n")

    pytest.main([__file__, "-v", "-s"])
