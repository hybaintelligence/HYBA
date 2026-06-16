"""Focused regression tests for the live miner search workflow.

These tests keep the basics honest: nonce ranges stay inside the PULVINI
coverage plan, telemetry formatting cannot crash search, and the nonce handler
feeds the unified engine for both local rejects and pool outcomes.
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
    def __init__(self, result: DummyLocalResult) -> None:
        self.result = result
        self.submitted: list[tuple[Any, int]] = []
        self.feedback: list[tuple[dict[str, Any], bool]] = []

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


def _miner_with(engine: DummyEngine, stratum: Any | None = None) -> UnifiedMiner:
    miner = UnifiedMiner.__new__(UnifiedMiner)
    miner.engine = engine
    miner.stratum = stratum
    miner._accepted = 0
    miner._rejected = 0
    miner._locally_invalid = 0
    miner._total_searches = 0
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
    assert len(engine.feedback) == 1
    share_info, accepted = engine.feedback[0]
    assert accepted is False
    assert share_info["error_code"] == 423
    assert share_info["error_msg"] == "live_share_submit_disabled"
    assert share_info["block_hash"] == "ab"
    assert share_info["target"] == 7
