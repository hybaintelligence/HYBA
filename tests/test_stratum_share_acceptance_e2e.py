from __future__ import annotations

import asyncio

from pythia_mining.live_stratum_session import SubmitResult
from pythia_mining.mining_validation import validate_share
from pythia_mining.stratum_client import MiningJob, StratumClient


class AcceptingSession:
    def __init__(self):
        self.calls = 0

    async def submit_share(
        self, *, job_id: str, extranonce2: str, ntime: str, nonce: str
    ):
        self.calls += 1
        return SubmitResult(
            True, None, {"id": self.calls, "result": True, "error": None}
        )

    async def close(self):
        return None


class RetryThenAcceptSession:
    def __init__(self):
        self.calls = 0

    async def submit_share(
        self, *, job_id: str, extranonce2: str, ntime: str, nonce: str
    ):
        self.calls += 1
        if self.calls == 1:
            return SubmitResult(False, None, {"unexpected": "shape"})
        return SubmitResult(
            True, None, {"id": self.calls, "result": True, "error": None}
        )

    async def close(self):
        return None


class RejectingSession:
    async def submit_share(
        self, *, job_id: str, extranonce2: str, ntime: str, nonce: str
    ):
        return SubmitResult(
            False,
            [23, "low difficulty share", None],
            {"id": 1, "result": False, "error": [23, "low difficulty share", None]},
        )

    async def close(self):
        return None


def _job() -> MiningJob:
    # Regtest-style compact target: large enough for deterministic test nonce search,
    # still validated by the same Bitcoin-compatible path as production submissions.
    return MiningJob(
        job_id="e2e-job-1",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="207fffff",
        ntime="5e9a5c00",
        target=int("7fffff" + "00" * 29, 16),
        extranonce1="abcd1234",
        extranonce2_size=4,
        stratum_version=1,
    )


def _winning_nonce(job: MiningJob) -> int:
    extranonce2 = "00" * job.extranonce2_size
    for nonce in range(10_000):
        if validate_share(job, nonce, extranonce2).valid:
            return nonce
    raise AssertionError("test fixture failed to find a valid nonce")


def _client(session) -> StratumClient:
    client = StratumClient(
        pool_url="stratum+tcp://loopback.local:3333",
        username="hendrix.worker",
        password="x",
        pool_name="Loopback Evidence Pool",
        max_share_retry_attempts=2,
        share_retry_backoff_base=0.0,
    )
    client.is_connected = True
    client.is_authenticated = True
    client.connection_state = "AUTHENTICATED"
    client.live_session = session
    return client


def test_connection_to_share_acceptance_records_only_after_pool_ack(monkeypatch):
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _job()
    nonce = _winning_nonce(job)
    client = _client(AcceptingSession())

    result = asyncio.run(client.submit_validated_share(job, nonce))

    assert result.accepted is True
    assert client.shares_submitted == 1
    assert client.shares_accepted == 1
    assert client.shares_rejected == 0
    assert client.last_share_error is None
    assert client.get_status()["performance"]["acceptance_rate"] == 1.0


def test_invalid_pool_response_retries_then_accepts(monkeypatch):
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _job()
    nonce = _winning_nonce(job)
    session = RetryThenAcceptSession()
    client = _client(session)

    result = asyncio.run(client.submit_validated_share(job, nonce))

    assert result.accepted is True
    assert session.calls == 2
    assert client.shares_submitted == 1
    assert client.shares_accepted == 1
    assert client.shares_rejected == 0


def test_pool_rejection_is_reported_not_converted_to_acceptance(monkeypatch):
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    job = _job()
    nonce = _winning_nonce(job)
    client = _client(RejectingSession())

    result = asyncio.run(client.submit_validated_share(job, nonce))

    assert result.accepted is False
    assert result.error_code == 2
    assert "low difficulty share" in str(result.error_message)
    assert client.shares_submitted == 1
    assert client.shares_accepted == 0
    assert client.shares_rejected == 1


def test_live_share_submission_must_be_explicitly_enabled(monkeypatch):
    monkeypatch.delenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", raising=False)
    job = _job()
    nonce = _winning_nonce(job)
    client = _client(AcceptingSession())

    result = asyncio.run(client.submit_validated_share(job, nonce))

    assert result.accepted is False
    assert result.error_code == 423
    assert result.error_message == "live_share_submit_disabled"
    assert client.shares_accepted == 0
