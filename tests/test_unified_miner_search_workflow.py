"""Focused regression tests for the live miner search workflow.

These tests keep the basics honest: nonce ranges stay inside the PULVINI
coverage plan, telemetry formatting cannot crash search, the live miner consumes
structured solver candidates, production/live mode refuses dev fixtures, and the
nonce handler feeds the unified engine for both local rejects and pool outcomes.
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

from run_unified_miner import UINT32_MAX, UnifiedMiner  # noqa: E402


@dataclass
class DummyJob:
    job_id: str = "job-1"
    target: int | None = 1


@dataclass
class DummySearchResult:
    nonce: int | None
    search_time: float = 0.01
    strategy_used: str = "phi_scaled_compressed_solver_search"
    phi_resonance_score: float | None = 0.618


@dataclass
class DummyLocalResult:
    valid: bool
    block_hash: str = "00" * 32
    target: int = 1
    reason: str | None = None


@dataclass
class DummyShareResult:
    accepted: bool
    error_code: int | None = None
    error_message: str | None = None
    block_hash: str | None = None
    target: int | None = None


class DummyEngine:
    def __init__(
        self,
        result: DummyLocalResult,
        search_results: list[DummySearchResult] | None = None,
    ) -> None:
        self.result = result
        self.search_results = list(search_results or [])
        self.search_calls: list[Any] = []
        self.submitted: list[tuple[Any, int]] = []
        self.feedback: list[tuple[dict[str, Any], bool]] = []

    async def search(self, job: Any) -> DummySearchResult:
        self.search_calls.append(job)
        if self.search_results:
            return self.search_results.pop(0)
        return DummySearchResult(nonce=123)

    def submit_candidate(self, job: Any, nonce: int) -> DummyLocalResult:
        self.submitted.append((job, nonce))
        return self.result

    async def on_share_result(self, share_info: dict[str, Any], accepted: bool) -> None:
        self.feedback.append((share_info, accepted))


class DummyStratum:
    def __init__(self, result: DummyShareResult) -> None:
        self.result = result
        self.submitted: list[tuple[Any, int]] = []

    async def submit_validated_share(self, job: Any, nonce: int) -> DummyShareResult:
        self.submitted.append((job, nonce))
        return self.result


class FixtureStratum:
    def __init__(self) -> None:
        self.is_connected = True
        self.live_session = None
        self.current_difficulty = 1.0
        self.injected = False

    async def poll_live_event(self, timeout: float) -> None:
        return None

    async def get_active_job_copy(self) -> None:
        return None

    async def inject_dev_fixture_target_job(self, difficulty: float) -> DummyJob:
        self.injected = True
        return DummyJob(job_id="fixture-job")


def _miner_with(engine: DummyEngine, stratum: Any | None = None) -> UnifiedMiner:
    miner = UnifiedMiner.__new__(UnifiedMiner)
    miner.engine = engine
    miner.stratum = stratum
    miner._accepted = 0
    miner._rejected = 0
    miner._locally_invalid = 0
    miner._total_searches = 0
    miner._last_no_job_reason = None
    miner._last_search_skip_reason = None
    miner._last_submit_reason = None
    miner._reason_log_cache = {}
    return miner


def test_solver_ranges_are_clamped_and_invalid_ranges_discarded() -> None:
    assert UnifiedMiner._normalise_solver_ranges(
        [
            (-10, 2),
            (5, 3),
            ("10", "12"),
            (UINT32_MAX, UINT32_MAX + 100),
            "not-a-range",
        ]
    ) == [(0, 2), (10, 12), (UINT32_MAX, UINT32_MAX)]


def test_solver_ranges_fall_back_to_full_nonce_space() -> None:
    assert UnifiedMiner._normalise_solver_ranges([]) == [(0, UINT32_MAX)]
    assert UnifiedMiner._normalise_solver_ranges([(9, 1), "bad"]) == [(0, UINT32_MAX)]


def test_safe_target_hex_cannot_crash_scan_logging() -> None:
    assert UnifiedMiner._safe_target_hex(None) == "unknown"
    assert UnifiedMiner._safe_target_hex("not-an-int") == "unknown"
    assert UnifiedMiner._safe_target_hex(1).startswith("0x")


def test_nonce_plan_telemetry_uses_current_plan_field_names() -> None:
    @dataclass
    class Segment:
        start: int
        end: int

    @dataclass
    class Plan:
        coverage_segments: tuple[Segment, ...]
        complete_coverage: bool
        overlap_free: bool

        @property
        def solver_ranges(self) -> list[tuple[int, int]]:
            return [(segment.start, segment.end) for segment in self.coverage_segments]

    assert UnifiedMiner._nonce_plan_telemetry(
        Plan(
            coverage_segments=(Segment(10, 12), Segment(20, 22)),
            complete_coverage=True,
            overlap_free=True,
        )
    ) == (2, True, True, 2)


def test_production_live_mode_refuses_dev_fixture_jobs(monkeypatch: Any) -> None:
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.delenv("HYBA_ALLOW_DEV_FIXTURES", raising=False)

    stratum = FixtureStratum()
    miner = _miner_with(DummyEngine(DummyLocalResult(valid=False)), stratum)

    job = asyncio.run(miner._next_job(timeout=0.01))

    assert job is None
    assert stratum.injected is False
    assert miner._last_no_job_reason == "live_session_missing_dev_fixture_refused"


def test_dev_fixture_jobs_require_explicit_non_live_non_production_mode(monkeypatch: Any) -> None:
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENV", "development")
    monkeypatch.setenv("NODE_ENV", "development")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "false")

    stratum = FixtureStratum()
    miner = _miner_with(DummyEngine(DummyLocalResult(valid=False)), stratum)

    job = asyncio.run(miner._next_job(timeout=0.01))

    assert job is not None
    assert job.job_id == "fixture-job"
    assert stratum.injected is True
    assert miner._last_no_job_reason == "dev_fixture_injected_explicit_non_live_mode"


def test_structured_search_batch_uses_engine_search_candidate_not_cursor() -> None:
    engine = DummyEngine(
        DummyLocalResult(valid=False, reason="hash_above_target"),
        search_results=[
            DummySearchResult(
                nonce=987_654,
                strategy_used="phi_scaled_compressed_solver_search",
                phi_resonance_score=0.9,
            )
        ],
    )
    miner = _miner_with(engine)

    checked, passed, failed = asyncio.run(
        miner._run_structured_search_batch(DummyJob(), batch_size=1)
    )

    assert checked == 1
    assert passed == 0
    assert failed == 1
    assert len(engine.search_calls) == 1
    assert engine.submitted[0][1] == 987_654
    share_info, accepted = engine.feedback[0]
    assert accepted is False
    assert share_info["strategy_used"] == "phi_scaled_compressed_solver_search"
    assert share_info["phi_resonance_score"] == 0.9


def test_structured_search_batch_does_not_submit_when_solver_returns_no_nonce() -> None:
    engine = DummyEngine(
        DummyLocalResult(valid=False, reason="hash_above_target"),
        search_results=[DummySearchResult(nonce=None)],
    )
    miner = _miner_with(engine)

    checked, passed, failed = asyncio.run(
        miner._run_structured_search_batch(DummyJob(), batch_size=1)
    )

    assert checked == 0
    assert passed == 0
    assert failed == 1
    assert len(engine.search_calls) == 1
    assert engine.submitted == []
    assert engine.feedback == []
    assert miner._last_search_skip_reason == "structured_solver_returned_no_nonce"


def test_local_reject_feeds_back_to_engine() -> None:
    engine = DummyEngine(DummyLocalResult(valid=False, reason="hash_above_target"))
    miner = _miner_with(engine)

    result = asyncio.run(
        miner._handle_nonce_result(
            DummyJob(),
            42,
            strategy_used="test_strategy",
            phi_resonance_score=None,
            search_time=0.0,
        )
    )

    assert result is False
    assert miner._locally_invalid == 1
    assert miner._rejected == 1
    assert miner._last_submit_reason == "local_validation_rejected_before_pool_submit"
    assert len(engine.feedback) == 1
    share_info, accepted = engine.feedback[0]
    assert accepted is False
    assert share_info["error_msg"] == "hash_above_target"
    assert share_info["strategy_used"] == "test_strategy"


def test_pool_outcome_feeds_back_to_engine_after_local_pass() -> None:
    engine = DummyEngine(DummyLocalResult(valid=True, block_hash="ab", target=7))
    stratum = DummyStratum(
        DummyShareResult(
            accepted=False,
            error_code=423,
            error_message="live_share_submit_disabled",
            block_hash=None,
            target=None,
        )
    )
    miner = _miner_with(engine, stratum)

    result = asyncio.run(
        miner._handle_nonce_result(
            DummyJob(),
            99,
            strategy_used="test_strategy",
            phi_resonance_score=0.5,
            search_time=0.1,
        )
    )

    assert result is True
    assert stratum.submitted == [(engine.submitted[0][0], 99)]
    assert miner._rejected == 1
    assert miner._last_submit_reason == "pool_or_submit_guard_rejected_share"
    assert len(engine.feedback) == 1
    share_info, accepted = engine.feedback[0]
    assert accepted is False
    assert share_info["error_code"] == 423
    assert share_info["error_msg"] == "live_share_submit_disabled"
    assert share_info["block_hash"] == "ab"
    assert share_info["target"] == 7
