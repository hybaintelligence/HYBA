from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "python_backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from pythia_mining.pulvini_compressed_solver import PulviniCompressedQuantumSolver  # noqa: E402
from pythia_mining.pulvini_nonce_compression import build_pulvini_nonce_plan  # noqa: E402
from pythia_mining.stratum_client import StratumClient  # noqa: E402


@given(
    attempt=st.integers(min_value=0, max_value=20),
    base=st.floats(
        min_value=0.01, max_value=5.0, allow_nan=False, allow_infinity=False
    ),
    cap=st.floats(
        min_value=5.0, max_value=120.0, allow_nan=False, allow_infinity=False
    ),
)
@settings(max_examples=75)
def test_property_backoff_is_bounded_and_deterministic_without_random_runtime(
    attempt: int, base: float, cap: float
) -> None:
    client = StratumClient(
        pool_url="stratum+tcp://example.com:3333",
        username="worker",
        password="x",
        pool_name="Property Pool",
        reconnect_backoff_base=base,
        reconnect_backoff_max=cap,
    )
    client.reconnect_attempts = attempt

    first = client._calculate_backoff_delay()
    second = client._calculate_backoff_delay()
    nominal = min(base * (2**attempt), cap)

    assert first == second
    assert nominal <= first <= nominal * 1.1


@given(
    target=st.integers(min_value=1, max_value=2**256 - 1),
    iterations=st.integers(min_value=1, max_value=64),
)
@settings(max_examples=50, deadline=None)
def test_property_compressed_solver_outputs_uint32_nonce_inside_complete_plan(
    target: int, iterations: int
) -> None:
    async def run_case() -> tuple[int | None, PulviniCompressedQuantumSolver]:
        plan = build_pulvini_nonce_plan()
        solver = PulviniCompressedQuantumSolver(configured_capacity_ehs=1.0)
        await solver.configure_compressed_search(target, plan)
        nonce = await solver.solve(max_iterations=iterations, timeout=5.0)
        return nonce, solver

    nonce, solver = asyncio.run(run_case())

    assert nonce is not None
    assert 0 <= nonce <= 2**32 - 1
    assert solver.get_metrics()["complete_nonce_coverage"] is True
    assert solver.get_metrics()["hashrate_ehs"] <= 1.0


@given(
    submitted=st.integers(min_value=0, max_value=1_000_000),
    accepted=st.integers(min_value=0, max_value=1_000_000),
    rejected=st.integers(min_value=0, max_value=1_000_000),
)
@settings(max_examples=100)
def test_property_pool_status_acceptance_rate_never_exceeds_one(
    submitted: int, accepted: int, rejected: int
) -> None:
    client = StratumClient(
        pool_url="stratum+tcp://example.com:3333",
        username="worker",
        password="x",
        pool_name="Property Pool",
    )
    client.shares_submitted = submitted
    client.shares_accepted = min(accepted, submitted)
    client.shares_rejected = rejected

    rate = client.get_status()["performance"]["acceptance_rate"]

    assert 0.0 <= rate <= 1.0


@given(
    size=st.integers(min_value=1, max_value=8),
    response_id=st.integers(min_value=1, max_value=20),
)
@settings(max_examples=25)
def test_property_matching_response_reader_skips_notifications(
    size: int, response_id: int
) -> None:
    from pythia_mining.live_stratum_session import LiveStratumSession
    from pythia_mining.pool_profiles import build_profile

    class Transport:
        def __init__(self) -> None:
            self.lines = [
                '{"id": null, "method": "mining.set_difficulty", "params": [1]}'
                for _ in range(size)
            ] + [f'{{"id": {response_id}, "result": true, "error": null}}']

        async def connect(self) -> None:
            return None

        async def send_line(self, line: str) -> None:
            return None

        async def read_line(self, timeout: float | None = None) -> str:
            return self.lines.pop(0)

        async def close(self) -> None:
            return None

    async def run_case() -> dict:
        session = LiveStratumSession(
            build_profile(
                "p",
                name="Pool",
                url="stratum+tcp://example.com:3333",
                username="w",
                password="x",
            ),
            transport=Transport(),
        )
        return await session._read_response_for_id(response_id)

    payload = asyncio.run(run_case())

    assert payload["id"] == response_id
    assert payload["result"] is True
