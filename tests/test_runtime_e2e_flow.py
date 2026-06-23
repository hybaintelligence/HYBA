"""Runtime E2E flow tests.

These tests drive the local UnifiedMiner control path with deterministic fakes. They
use no external network and no credentials. The point is to prove that a job moves
through acquisition, structured search, validation, guarded submission, and engine
feedback as one connected system.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import run_unified_miner as miner_module
from run_unified_miner import UnifiedMiner
from pythia_mining.stratum_client import MiningJob, ShareResult


class FakePool:
    def __init__(
        self,
        job: MiningJob | None,
        result: ShareResult | None = None,
        session: object | None = object(),
    ):
        self.is_connected = True
        self.live_session = session
        self.current_difficulty = 1.0
        self.job = job
        self.result = result or ShareResult(
            accepted=False, error_code=423, error_message="guarded"
        )
        self.submissions: list[tuple[MiningJob, int]] = []
        self.fixture_used = False

    async def poll_live_event(self, *, timeout: float = 0.1):
        del timeout
        job, self.job = self.job, None
        return job

    async def get_active_job_copy(self):
        return None

    async def submit_validated_share(self, job: MiningJob, nonce: int):
        self.submissions.append((job, nonce))
        return self.result

    def inject_dev_fixture_target_job(self, *, difficulty: float):
        del difficulty
        self.fixture_used = True
        return make_job("fixture")


class FakeEngine:
    def __init__(
        self, *, nonce: Any = 1, valid: bool = False, reason: str = "local_miss"
    ):
        self.nonce = nonce
        self.valid = valid
        self.reason = reason
        self.searches: list[MiningJob] = []
        self.validations: list[tuple[MiningJob, int]] = []
        self.feedback: list[tuple[dict[str, Any], bool]] = []

    async def search(self, job: MiningJob):
        self.searches.append(job)
        return SimpleNamespace(
            nonce=self.nonce,
            strategy_used="e2e",
            phi_resonance_score=0.5,
            search_time=0.001,
        )

    def submit_candidate(self, job: MiningJob, nonce: int):
        self.validations.append((job, nonce))
        return SimpleNamespace(
            valid=self.valid,
            reason=None if self.valid else self.reason,
            block_hash="00" * 32,
            target=job.target,
        )

    async def on_share_result(self, share_info: dict[str, Any], *, accepted: bool):
        self.feedback.append((dict(share_info), accepted))


def make_job(job_id: str) -> MiningJob:
    return MiningJob(
        job_id=job_id,
        prevhash="11" * 32,
        coinbase_parts=("0100000001", "ffffffff"),
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="6578ab4e",
        target=1,
        extranonce1="0badf00d",
        extranonce2_size=8,
    )


def make_miner(monkeypatch: pytest.MonkeyPatch) -> UnifiedMiner:
    monkeypatch.setattr(miner_module, "RUNNING", True)
    monkeypatch.setenv("HYBA_ENV", "test")
    monkeypatch.setenv("NODE_ENV", "test")
    monkeypatch.delenv("HYBA_ENABLE_LIVE_STRATUM", raising=False)
    monkeypatch.delenv("HYBA_ALLOW_DEV_FIXTURES", raising=False)
    return UnifiedMiner(pool_config_path="config/mining_pools_test.json")


@pytest.mark.asyncio
async def test_e2e_job_to_local_reject_never_calls_guarded_submit(monkeypatch):
    miner = make_miner(monkeypatch)
    job = make_job("local-reject")
    engine = FakeEngine(nonce=99, valid=False, reason="hash_above_target")
    pool = FakePool(job)
    miner.engine = engine
    miner.stratum = pool

    acquired = await miner._next_job(timeout=0.05)
    checked, passed, failed = await miner._run_structured_search_batch(acquired, 1)  # type: ignore[arg-type]

    assert acquired is job
    assert (checked, passed, failed) == (1, 0, 1)
    assert engine.searches == [job]
    assert engine.validations == [(job, 99)]
    assert pool.submissions == []
    assert engine.feedback[-1][1] is False
    assert miner._last_submit_reason == "local_validation_rejected_before_pool_submit"


@pytest.mark.asyncio
async def test_e2e_job_to_guarded_accept_records_feedback(monkeypatch):
    miner = make_miner(monkeypatch)
    job = make_job("accepted")
    engine = FakeEngine(nonce=123, valid=True)
    pool = FakePool(
        job,
        ShareResult(
            accepted=True,
            job_id=job.job_id,
            nonce=123,
            block_hash="aa" * 32,
            target=job.target,
        ),
    )
    miner.engine = engine
    miner.stratum = pool

    acquired = await miner._next_job(timeout=0.05)
    checked, passed, failed = await miner._run_structured_search_batch(acquired, 1)  # type: ignore[arg-type]

    assert acquired is job
    assert (checked, passed, failed) == (1, 1, 0)
    assert pool.submissions == [(job, 123)]
    assert engine.feedback[-1][1] is True
    assert miner._accepted == 1
    assert miner._last_submit_reason == "pool_accepted_share"


@pytest.mark.asyncio
async def test_e2e_job_to_guarded_reject_records_feedback_without_acceptance(
    monkeypatch,
):
    miner = make_miner(monkeypatch)
    job = make_job("guard-reject")
    engine = FakeEngine(nonce=777, valid=True)
    pool = FakePool(
        job,
        ShareResult(
            accepted=False,
            error_code=423,
            error_message="guarded",
            job_id=job.job_id,
            nonce=777,
        ),
    )
    miner.engine = engine
    miner.stratum = pool

    acquired = await miner._next_job(timeout=0.05)
    checked, passed, failed = await miner._run_structured_search_batch(acquired, 1)  # type: ignore[arg-type]

    assert acquired is job
    assert (checked, passed, failed) == (1, 1, 0)
    assert pool.submissions == [(job, 777)]
    assert engine.feedback[-1][1] is False
    assert miner._accepted == 0
    assert miner._rejected == 1
    assert miner._last_submit_reason == "pool_or_submit_guard_rejected_share"


@pytest.mark.asyncio
async def test_e2e_production_without_live_session_stops_before_search(monkeypatch):
    miner = make_miner(monkeypatch)
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    engine = FakeEngine(nonce=1, valid=True)
    pool = FakePool(None, session=None)
    miner.engine = engine
    miner.stratum = pool

    job = await miner._next_job(timeout=0.05)

    assert job is None
    assert engine.searches == []
    assert engine.validations == []
    assert engine.feedback == []
    assert pool.submissions == []
    assert pool.fixture_used is False
    assert miner._last_no_job_reason == "live_session_missing_dev_fixture_refused"
