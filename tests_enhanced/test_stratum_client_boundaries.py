from __future__ import annotations

import time

import pytest

from pythia_mining.stratum_client import ProductionConfigurationError, StratumClient


def test_production_pool_credentials_are_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NODE_ENV", "production")

    with pytest.raises(ProductionConfigurationError):
        StratumClient(
            pool_url="stratum+tcp://pool.example:3333",
            username="",
            password="",
            pool_name="missing-creds",
        )


def test_circuit_breaker_opens_after_threshold_and_blocks_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NODE_ENV", "development")
    client = StratumClient(
        pool_url="stratum+tcp://pool.example:3333",
        username="worker",
        password="x",
        pool_name="breaker-review",
    )

    for _ in range(client._circuit_breaker_threshold):
        client._circuit_breaker_record_failure()

    assert client._circuit_breaker_state == "open"
    assert client._circuit_breaker_allow_request() is False


def test_circuit_breaker_half_open_after_timeout_then_closes_on_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NODE_ENV", "development")
    client = StratumClient(
        pool_url="stratum+tcp://pool.example:3333",
        username="worker",
        password="x",
        pool_name="half-open-review",
    )
    for _ in range(client._circuit_breaker_threshold):
        client._circuit_breaker_record_failure()

    client._circuit_breaker_last_failure = (
        time.time() - client._circuit_breaker_timeout - 1
    )

    assert client._circuit_breaker_allow_request() is True
    assert client._circuit_breaker_state == "half_open"

    client._circuit_breaker_record_success()
    assert client._circuit_breaker_state == "closed"
    assert client._circuit_breaker_failures == 0


def test_reconnect_backoff_is_bounded_and_non_decreasing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NODE_ENV", "development")
    client = StratumClient(
        pool_url="stratum+tcp://pool.example:3333",
        username="worker",
        password="x",
        pool_name="backoff-review",
        reconnect_backoff_base=0.5,
        reconnect_backoff_max=8.0,
    )

    delays = []
    for attempt in range(8):
        client.reconnect_attempts = attempt
        delays.append(client._calculate_backoff_delay())

    assert all(delay >= 0.5 for delay in delays)
    assert all(
        delay <= 8.8 for delay in delays
    )  # 10% deterministic jitter above max cap
    assert delays[-1] >= delays[0]
