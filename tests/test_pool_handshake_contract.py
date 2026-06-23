"""Pool handshake contract tests for Stratum client integration.

These tests sit above pure protocol parsing and below live network tests.  They
verify that the production client boundary converts pool handshake/events into
observable runtime state.  No real pool, socket, or credential is used.

Why this exists: unit tests can prove protocol helpers while the actual mining
runtime silently fails to authenticate, loses extranonce metadata, misses
``mining.set_difficulty``/``mining.notify``, or treats rejected authorization as
connected.  These tests pin that system boundary.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import pythia_mining.stratum_client as stratum_client_module
from pythia_mining.live_stratum_session import LiveStratumSessionError, SessionHandshake
from pythia_mining.stratum_client import MiningJob, StratumClient


class _AuthenticatedLiveSession:
    """Deterministic live-session fake for successful v1 handshake tests."""

    instances: list["_AuthenticatedLiveSession"] = []

    def __init__(self, profile):
        self.profile = profile
        self.connected = False
        self.closed = False
        self.subscribe_authorize_called = False
        _AuthenticatedLiveSession.instances.append(self)

    async def connect(self) -> None:
        self.connected = True

    async def subscribe_and_authorize(self) -> SessionHandshake:
        self.subscribe_authorize_called = True
        return SessionHandshake(
            pool_id=self.profile.pool_id,
            extranonce1="0badf00d",
            extranonce2_size=8,
            authorized=True,
        )

    async def close(self) -> None:
        self.closed = True


class _RejectedAuthorizationSession(_AuthenticatedLiveSession):
    """Fake that models a pool rejecting ``mining.authorize``."""

    async def subscribe_and_authorize(
        self,
    ) -> SessionHandshake:  # pragma: no cover - raises
        self.subscribe_authorize_called = True
        raise LiveStratumSessionError("pool rejected authorization")


class _QueuedEventSession:
    """Minimal live-session fake for Stratum event polling."""

    def __init__(self, events):
        self.events = list(events)
        self.closed = False

    async def read_event(self, *, timeout=0.1):
        if not self.events:
            raise TimeoutError("no events queued")
        return self.events.pop(0)

    async def close(self) -> None:
        self.closed = True


async def _disable_block_height_oracle(self) -> None:
    """Keep event tests isolated from external blockchain tip lookups."""
    return None


@pytest.mark.asyncio
async def test_live_v1_pool_handshake_sets_authenticated_runtime_state(monkeypatch):
    """A successful live v1 subscribe+authorize handshake must hydrate client state."""

    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.delenv("NODE_ENV", raising=False)
    monkeypatch.setattr(
        stratum_client_module, "LiveStratumSession", _AuthenticatedLiveSession
    )
    _AuthenticatedLiveSession.instances.clear()

    client = StratumClient(
        "stratum+tcp://pool.example.test:3333",
        username="hyba.worker",
        password="secret",
        pool_name="UnitPool",
        stratum_version=1,
    )

    connected = await client.connect()

    assert connected is True
    assert client.is_connected is True
    assert client.is_authenticated is True
    assert client.connection_state == "AUTHENTICATED"
    assert client.extranonce1 == "0badf00d"
    assert client.extranonce2_size == 8
    assert client.avg_latency is not None
    assert client.connection_failures == 0
    assert _AuthenticatedLiveSession.instances
    assert _AuthenticatedLiveSession.instances[0].connected is True
    assert _AuthenticatedLiveSession.instances[0].subscribe_authorize_called is True

    await client.disconnect()
    assert _AuthenticatedLiveSession.instances[0].closed is True


@pytest.mark.asyncio
async def test_live_v1_pool_authorization_rejection_fails_closed(monkeypatch):
    """Rejected pool authorization must not leave the client connected/authenticated."""

    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.delenv("NODE_ENV", raising=False)
    monkeypatch.setattr(
        stratum_client_module, "LiveStratumSession", _RejectedAuthorizationSession
    )

    client = StratumClient(
        "stratum+tcp://pool.example.test:3333",
        username="hyba.worker",
        password="bad-secret",
        pool_name="RejectPool",
        stratum_version=1,
        max_reconnect_attempts=1,
    )

    connected = await client.connect()

    assert connected is False
    assert client.is_connected is False
    assert client.is_authenticated is False
    assert "pool rejected authorization" in client.connection_state
    assert client.connection_failures == 1
    assert client.live_session is None


@pytest.mark.asyncio
async def test_live_pool_difficulty_event_updates_target_context(monkeypatch):
    """``mining.set_difficulty`` must update client difficulty before job target creation."""

    monkeypatch.setattr(
        StratumClient,
        "_check_block_height_for_stale_jobs",
        _disable_block_height_oracle,
    )
    payload = SimpleNamespace(difficulty=16384.0)
    client = StratumClient(
        "stratum+tcp://pool.example.test:3333",
        username="hyba.worker",
        password="secret",
        pool_name="DiffPool",
    )
    client.live_session = _QueuedEventSession([("mining.set_difficulty", payload)])
    client.is_connected = True
    client.is_authenticated = True

    job = await client.poll_live_event(timeout=0.01)

    assert job is None
    assert client.current_difficulty == 16384.0
    await client.disconnect()


@pytest.mark.asyncio
async def test_live_pool_notify_creates_active_job_with_handshake_metadata(monkeypatch):
    """``mining.notify`` must create an active job carrying extranonce metadata."""

    monkeypatch.setattr(
        StratumClient,
        "_check_block_height_for_stale_jobs",
        _disable_block_height_oracle,
    )
    notify = SimpleNamespace(
        job_id="job-42",
        prevhash="11" * 32,
        coinbase1="0100000001",
        coinbase2="ffffffff",
        merkle_branch=["22" * 32],
        version="20000000",
        nbits="1d00ffff",
        ntime="6578ab4e",
        clean_jobs=True,
    )
    client = StratumClient(
        "stratum+tcp://pool.example.test:3333",
        username="hyba.worker",
        password="secret",
        pool_name="NotifyPool",
    )
    client.extranonce1 = "c0ffee"
    client.extranonce2_size = 8
    client.current_difficulty = 4096.0
    client.live_session = _QueuedEventSession([("mining.notify", notify)])
    client.is_connected = True
    client.is_authenticated = True

    job = await client.poll_live_event(timeout=0.01)

    assert isinstance(job, MiningJob)
    assert job.job_id == "job-42"
    assert job.extranonce1 == "c0ffee"
    assert job.extranonce2_size == 8
    assert job.target > 0
    assert client.active_job_id == "job-42"
    assert client.jobs_received == 1
    assert client.current_jobs["job-42"] is job
    await client.disconnect()


@pytest.mark.asyncio
async def test_clean_jobs_notify_marks_existing_jobs_stale(monkeypatch):
    """A clean Stratum job must invalidate prior active jobs before accepting the new job."""

    monkeypatch.setattr(
        StratumClient,
        "_check_block_height_for_stale_jobs",
        _disable_block_height_oracle,
    )
    client = StratumClient(
        "stratum+tcp://pool.example.test:3333",
        username="hyba.worker",
        password="secret",
        pool_name="CleanJobsPool",
    )
    old_job = MiningJob(
        job_id="old-job",
        prevhash="00" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="6578ab4e",
        target=1,
        extranonce1="aa",
        extranonce2_size=4,
    )
    client.current_jobs[old_job.job_id] = old_job
    client.active_job_id = old_job.job_id

    notify = SimpleNamespace(
        job_id="new-job",
        prevhash="33" * 32,
        coinbase1="0100000001",
        coinbase2="ffffffff",
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="6578ab4f",
        clean_jobs=True,
    )
    client.live_session = _QueuedEventSession([("mining.notify", notify)])
    client.is_connected = True
    client.is_authenticated = True

    new_job = await client.poll_live_event(timeout=0.01)

    assert new_job is not None
    assert "old-job" in client.stale_job_ids
    assert "old-job" not in client.current_jobs
    assert client.active_job_id == "new-job"
    assert set(client.current_jobs) == {"new-job"}
    await client.disconnect()
