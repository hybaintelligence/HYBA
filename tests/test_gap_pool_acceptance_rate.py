"""Gap test: pool acceptance rate > 95% under controlled mock sessions.

The forensic review found pool acceptance was only mock-tested with single
shares.  This file closes the gap by testing:

1. Acceptance rate reaches ≥ 0.95 when the pool accepts all valid shares.
2. Acceptance rate is correctly computed after mixed accept/reject sequences.
3. Stale-job submissions are counted as rejected, not accepted.
4. The live-share-submit gate (env flag) blocks all submissions when disabled.
5. Counter arithmetic is consistent: submitted = accepted + rejected always.
6. Multi-share session accumulates counters monotonically.
7. get_status() performance dict mirrors raw counters exactly.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python_backend"))

from pythia_mining.live_stratum_session import SubmitResult  # noqa: E402
from pythia_mining.mining_validation import validate_share  # noqa: E402
from pythia_mining.stratum_client import MiningJob, StratumClient  # noqa: E402


# ---------------------------------------------------------------------------
# mock sessions
# ---------------------------------------------------------------------------


class _AlwaysAccept:
    def __init__(self):
        self.calls = 0

    async def submit_share(self, **_):
        self.calls += 1
        return SubmitResult(True, None, {"id": self.calls, "result": True, "error": None})

    async def close(self):
        pass


class _AlwaysReject:
    async def submit_share(self, **_):
        return SubmitResult(
            False,
            [23, "low difficulty share", None],
            {"id": 1, "result": False, "error": [23, "low difficulty share", None]},
        )

    async def close(self):
        pass


class _AcceptNth:
    """Accept every n-th share, reject the rest."""

    def __init__(self, n: int):
        self.n = n
        self.calls = 0

    async def submit_share(self, **_):
        self.calls += 1
        if self.calls % self.n == 0:
            return SubmitResult(True, None, {"id": self.calls, "result": True, "error": None})
        return SubmitResult(
            False,
            [23, "low diff", None],
            {"id": self.calls, "result": False, "error": [23, "low diff", None]},
        )

    async def close(self):
        pass


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _regtest_job(job_id: str = "rate-job") -> MiningJob:
    return MiningJob(
        job_id=job_id,
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="5e9a5c00",
        target=int("7fffff" + "00" * 29, 16),
        extranonce1="abcd1234",
        extranonce2_size=4,
    )


def _client(session) -> StratumClient:
    c = StratumClient(
        pool_url="stratum+tcp://loopback.local:3333",
        username="test.worker",
        password="x",
        pool_name="Mock Pool",
        max_share_retry_attempts=1,
        share_retry_backoff_base=0.0,
    )
    c.is_connected = True
    c.is_authenticated = True
    c.connection_state = "AUTHENTICATED"
    c.live_session = session
    return c


def _find_valid_nonces(job: MiningJob, limit: int = 200):
    e2 = "00000000"
    return [n for n in range(limit) if validate_share(job, n, e2).valid]


# ---------------------------------------------------------------------------
# 1. All-accept session → acceptance rate == 1.0
# ---------------------------------------------------------------------------


def test_all_accept_session_rate_equals_one(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _regtest_job()
    valid = _find_valid_nonces(job)
    assert valid, "need at least one valid nonce"

    client = _client(_AlwaysAccept())

    for nonce in valid[:10]:
        result = asyncio.run(client.submit_validated_share(job, nonce))
        assert result.accepted

    status = client.get_status()
    assert status["performance"]["acceptance_rate"] == 1.0
    assert client.shares_submitted == client.shares_accepted
    assert client.shares_rejected == 0


# ---------------------------------------------------------------------------
# 2. Counter invariant: submitted == accepted + rejected at all times
# ---------------------------------------------------------------------------


def test_counter_invariant_submitted_equals_accepted_plus_rejected(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _regtest_job()
    valid = _find_valid_nonces(job)
    assert len(valid) >= 3

    client = _client(_AcceptNth(2))  # accept every 2nd share

    for nonce in valid[:6]:
        asyncio.run(client.submit_validated_share(job, nonce))
        assert client.shares_submitted == client.shares_accepted + client.shares_rejected, (
            f"invariant broken: submitted={client.shares_submitted} "
            f"accepted={client.shares_accepted} rejected={client.shares_rejected}"
        )


# ---------------------------------------------------------------------------
# 3. Mixed session produces correct acceptance rate (≈ 0.5)
# ---------------------------------------------------------------------------


def test_mixed_session_acceptance_rate_correct(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _regtest_job()
    valid = _find_valid_nonces(job)
    assert len(valid) >= 10

    client = _client(_AcceptNth(2))

    submitted = 10
    for nonce in valid[:submitted]:
        asyncio.run(client.submit_validated_share(job, nonce))

    expected_rate = client.shares_accepted / client.shares_submitted
    status_rate = client.get_status()["performance"]["acceptance_rate"]
    assert abs(status_rate - expected_rate) < 1e-9, (
        f"get_status rate {status_rate} != computed {expected_rate}"
    )


# ---------------------------------------------------------------------------
# 4. Stale-job submission is counted as rejected, not accepted
# ---------------------------------------------------------------------------


def test_stale_job_counted_as_rejected(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _regtest_job(job_id="stale-job")
    valid = _find_valid_nonces(job)
    assert valid

    client = _client(_AlwaysAccept())
    client.stale_job_ids.add("stale-job")

    result = asyncio.run(client.submit_validated_share(job, valid[0]))

    assert result.accepted is False
    assert result.error_code == 410
    assert client.shares_rejected == 1
    assert client.shares_accepted == 0


# ---------------------------------------------------------------------------
# 5. Live-share-submit gate blocks when env flag absent
# ---------------------------------------------------------------------------


def test_gate_blocks_submission_without_env_flag(monkeypatch) -> None:
    monkeypatch.delenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", raising=False)
    job = _regtest_job()
    valid = _find_valid_nonces(job)
    assert valid

    client = _client(_AlwaysAccept())

    result = asyncio.run(client.submit_validated_share(job, valid[0]))

    assert result.accepted is False
    assert result.error_code == 423
    assert client.shares_accepted == 0


# ---------------------------------------------------------------------------
# 6. High-volume session maintains ≥ 0.95 when pool accepts all valid shares
# ---------------------------------------------------------------------------


def test_high_volume_session_maintains_target_acceptance_rate(monkeypatch) -> None:
    """20 valid shares submitted to an always-accepting pool must give rate ≥ 0.95."""
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _regtest_job()
    valid = _find_valid_nonces(job, limit=1000)
    assert len(valid) >= 20, f"need ≥ 20 valid nonces, found {len(valid)}"

    client = _client(_AlwaysAccept())

    for nonce in valid[:20]:
        asyncio.run(client.submit_validated_share(job, nonce))

    rate = client.get_status()["performance"]["acceptance_rate"]
    assert rate >= 0.95, f"acceptance rate {rate} below 0.95 target"


# ---------------------------------------------------------------------------
# 7. get_status performance dict mirrors raw counters exactly
# ---------------------------------------------------------------------------


def test_get_status_performance_mirrors_raw_counters(monkeypatch) -> None:
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _regtest_job()
    valid = _find_valid_nonces(job)
    assert len(valid) >= 4

    client = _client(_AcceptNth(3))

    for nonce in valid[:6]:
        asyncio.run(client.submit_validated_share(job, nonce))

    status = client.get_status()["performance"]
    assert status["shares_submitted"] == client.shares_submitted
    assert status["shares_accepted"] == client.shares_accepted
    assert status["shares_rejected"] == client.shares_rejected
    assert (
        abs(status["acceptance_rate"] - (client.shares_accepted / max(client.shares_submitted, 1)))
        < 1e-9
    )
