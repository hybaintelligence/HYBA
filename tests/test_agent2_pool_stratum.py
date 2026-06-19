"""Agent 2 coverage for pool profiles, Stratum protocol sessions, clients, and transport."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pythia_mining.live_stratum_session import LiveStratumSession, LiveStratumSessionError
from pythia_mining.pool_profiles import (
    PoolCredentialConfig,
    PoolProfile,
    PoolProfileError,
    build_profile,
    default_pool_config,
    load_pool_profiles,
    load_runtime_pool_configs,
    order_profiles,
    save_runtime_pool_config,
    split_pool_url_credentials,
    validate_pool_config,
    validate_pool_url,
    validate_profile,
)
from pythia_mining.stratum_client import (
    AllPoolsOfflineError,
    MiningJob,
    PoolManager,
    ProductionConfigurationError,
    StratumClient,
    _difficulty_to_target,
)
from pythia_mining.stratum_protocol import (
    StratumProtocolError,
    build_submit,
    parse_server_message,
    parse_subscribe_result,
)
from pythia_mining.stratum_transport import (
    StratumLineTransport,
    StratumTransportError,
    parse_endpoint,
)


def profile(**overrides) -> PoolProfile:
    data = dict(
        pool_id="alpha",
        name="Alpha Pool",
        url="stratum+tcp://pool.example:3333",
        username="worker.1",
        password="x",
    )
    data.update(overrides)
    return build_profile(**data)


class FakeTransport:
    def __init__(self, lines=None):
        self.lines = list(lines or [])
        self.sent = []
        self.connected = False
        self.closed = False

    async def connect(self):
        self.connected = True

    async def send_line(self, line: str):
        self.sent.append(json.loads(line))

    async def read_line(self, *, timeout=None):
        if not self.lines:
            raise StratumTransportError("timed out waiting for Stratum line")
        return self.lines.pop(0)

    async def close(self):
        self.closed = True


class NullAudit:
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None

        return _noop


class NullMetrics:
    def record_connection_event(self, **kwargs):
        return None

    def record_share_submission(self, **kwargs):
        return None

    def record_pool_metrics(self, metrics):
        return None


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")
    c = StratumClient("stratum+tcp://pool.example:3333", "worker", "x", "Pool")
    c.audit_logger = NullAudit()
    c.metrics_store = NullMetrics()
    c._persist_metrics = AsyncMock()
    return c


def test_pool_profile_masks_credentials_by_default():
    p = profile(username="secret", password="token")
    payload = p.to_dict()
    assert payload["username"] == "<configured>"
    assert payload["password"] == "<configured>"
    assert p.to_dict(include_secret_fields=True)["username"] == "secret"


def test_pool_profile_extracts_inline_credentials_and_sanitizes_url():
    clean, username, password = split_pool_url_credentials(
        "stratum+tcp://user%2E1:p%40ss@host:3333"
    )
    assert clean == "stratum+tcp://host:3333"
    assert username == "user.1"
    assert password == "p@ss"


def test_build_profile_uses_inline_credentials_when_fields_empty():
    p = build_profile(
        "Inline", name="Inline", url="stratum+tcp://u:p@host:3333", username="", password=""
    )
    assert p.pool_id == "inline"
    assert p.url == "stratum+tcp://host:3333"
    assert (p.username, p.password) == ("u", "p")


@pytest.mark.parametrize(
    "url", ["http://host:3333", "stratum+tcp://host", "stratum+tcp://host:3336"]
)
def test_validate_pool_url_rejects_invalid_or_mismatched_urls(url):
    with pytest.raises(PoolProfileError):
        validate_pool_url(url)


def test_validate_pool_url_enforces_tls_requirement():
    with pytest.raises(PoolProfileError, match="TLS is required"):
        validate_pool_url("stratum+tcp://host:3333", tls_required=True)
    assert (
        validate_pool_url("stratum+ssl://host:443", tls_required=True) == "stratum+ssl://host:443"
    )


def test_validate_profile_normalizes_url_credentials():
    raw = PoolProfile("p", "Pool", "stratum+tcp://u:p@host:3333", "u", "p")
    assert validate_profile(raw).url == "stratum+tcp://host:3333"


@pytest.mark.parametrize(
    "kwargs",
    [{"pool_id": ""}, {"username": ""}, {"password": ""}, {"priority": -1}, {"stratum_version": 9}],
)
def test_validate_profile_rejects_required_field_errors(kwargs):
    data = dict(pool_id="p", name="Pool", url="stratum+tcp://host:3333", username="u", password="p")
    data.update(kwargs)
    with pytest.raises(PoolProfileError):
        validate_profile(PoolProfile(**data))


def test_pool_credential_config_resolves_ckpool_and_nicehash_usernames():
    ck = PoolCredentialConfig(
        "ckpool", "CK", "stratum+tcp://host:3333", 1, False, "btc_address", btc_address="bc1qq"
    )
    nh = PoolCredentialConfig(
        "nicehash",
        "NH",
        "stratum+ssl://host:443",
        1,
        True,
        "nicehash_worker_pool_id",
        nicehash_pool_id="wallet",
        worker="rig",
    )
    assert ck.resolved_username() == "bc1qq"
    assert ck.resolved_password() == "x"
    assert nh.resolved_username() == "wallet.rig"


def test_pool_config_to_dict_redacts_runtime_secrets():
    cfg = PoolCredentialConfig(
        "viabtc",
        "Via",
        "stratum+tcp://user:pass@host:3333",
        1,
        False,
        "username_password",
        username="u",
        password="p",
    )
    payload = cfg.to_dict()
    assert payload["url"] == "stratum+tcp://host:3333"
    assert payload["username"] == "<configured>"
    assert payload["resolved_username"] == "<configured>"


def test_order_profiles_sorts_by_priority_then_pool_id():
    ordered = order_profiles(
        [
            profile(pool_id="b", priority=2),
            profile(pool_id="a", priority=2),
            profile(pool_id="c", priority=1),
        ]
    )
    assert [p.pool_id for p in ordered] == ["c", "a", "b"]


def test_default_pool_config_reads_env_priority(monkeypatch):
    monkeypatch.setenv("HYBA_POOL_VIABTC_PRIORITY", "7")
    assert default_pool_config("viabtc").priority == 7


def test_load_runtime_pool_configs_env_takes_precedence_over_file(tmp_path, monkeypatch):
    path = tmp_path / "pools.json"
    path.write_text(
        json.dumps(
            {
                "pools": {
                    "viabtc": {
                        "username": "file",
                        "password": "file",
                        "url": "stratum+tcp://file:3333",
                    }
                }
            }
        )
    )
    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(path))
    monkeypatch.setenv("HYBA_POOL_VIABTC_USERNAME", "env")
    monkeypatch.setenv("HYBA_POOL_VIABTC_PASSWORD", "envpass")
    cfg = load_runtime_pool_configs()["viabtc"]
    assert cfg.source == "env"
    assert cfg.username == "env"
    assert cfg.url != "stratum+tcp://file:3333"


def test_save_runtime_pool_config_writes_0600_and_load_pool_profiles(tmp_path, monkeypatch):
    path = tmp_path / "pools.json"
    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(path))
    save_runtime_pool_config(
        PoolCredentialConfig(
            "viabtc",
            "Via",
            "stratum+tcp://host:3333",
            1,
            False,
            "username_password",
            username="u",
            password="p",
            priority=3,
        )
    )
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    loaded = [p for p in load_pool_profiles() if p.pool_id == "viabtc"][0]
    assert loaded.username == "u"


def test_validate_pool_config_rejects_missing_credentials():
    with pytest.raises(PoolProfileError):
        validate_pool_config(
            PoolCredentialConfig(
                "viabtc", "Via", "stratum+tcp://host:3333", 1, False, "username_password"
            )
        )


@pytest.mark.parametrize(
    "url,tls",
    [
        ("stratum+tcp://host:3333", False),
        ("stratum+ssl://host:443", True),
        ("stratum2+tls://host:3336", True),
    ],
)
def test_parse_endpoint_recognizes_tls_and_ports(url, tls):
    endpoint = parse_endpoint(url)
    assert endpoint.host == "host"
    assert endpoint.use_tls is tls


def test_parse_endpoint_rejects_unsupported_scheme_and_missing_host():
    with pytest.raises(StratumTransportError):
        parse_endpoint("http://host:3333")
    with pytest.raises(StratumTransportError):
        parse_endpoint("stratum+tcp://")


async def test_transport_send_line_appends_newline_and_requires_connection():
    transport = StratumLineTransport("stratum+tcp://host:3333")
    with pytest.raises(StratumTransportError):
        await transport.send_line("{}")
    writer = SimpleNamespace(
        is_closing=lambda: False,
        buffer=b"",
        write=lambda payload: setattr(writer, "buffer", payload),
        drain=AsyncMock(),
    )
    transport.writer = writer
    await transport.send_line("{}")
    assert writer.buffer == b"{}\n"


async def test_transport_read_line_decodes_and_detects_closed_stream():
    transport = StratumLineTransport("stratum+tcp://host:3333")
    transport.reader = SimpleNamespace(readline=AsyncMock(return_value=b'{"id":1}\n'))
    assert await transport.read_line() == '{"id":1}'
    transport.reader.readline = AsyncMock(return_value=b"")
    with pytest.raises(StratumTransportError, match="closed"):
        await transport.read_line()


def test_json_rpc_submit_formatting_and_hex_normalization():
    payload = json.loads(build_submit(9, "worker", "job", "AABB", "5E9A5C00", "0000000F"))
    assert payload == {
        "id": 9,
        "method": "mining.submit",
        "params": ["worker", "job", "aabb", "5e9a5c00", "0000000f"],
    }


@pytest.mark.parametrize(
    "line", ["not-json", "[]", json.dumps({"method": "mining.notify", "params": []})]
)
def test_malformed_json_and_protocol_messages_raise(line):
    with pytest.raises(StratumProtocolError):
        parse_server_message(line)


def test_parse_subscribe_result_falls_back_empty_extranonce_and_limits_size():
    result = parse_subscribe_result({"id": 1, "result": [[], "", 4], "error": None})
    assert result.extranonce1 == "00000001"
    with pytest.raises(StratumProtocolError):
        parse_subscribe_result({"id": 1, "result": [[], "aa", 33]})


async def test_live_session_connection_handshake_ignores_interleaved_notifications():
    lines = [
        json.dumps({"method": "mining.set_difficulty", "params": [4]}),
        json.dumps({"id": 1, "result": [[], "abcd", 4], "error": None}),
        json.dumps({"id": 2, "result": True, "error": None}),
    ]
    transport = FakeTransport(lines)
    session = LiveStratumSession(profile(), transport=transport)
    await session.connect()
    handshake = await session.subscribe_and_authorize()
    assert transport.connected is True
    assert handshake.to_dict() == {
        "pool_id": "alpha",
        "extranonce1": "abcd",
        "extranonce2_size": 4,
        "authorized": True,
    }
    assert [item["method"] for item in transport.sent] == ["mining.subscribe", "mining.authorize"]


async def test_live_session_authentication_failure_raises():
    transport = FakeTransport(
        [json.dumps({"id": 1, "result": [[], "aa", 4]}), json.dumps({"id": 2, "result": False})]
    )
    with pytest.raises(LiveStratumSessionError, match="rejected authorization"):
        await LiveStratumSession(profile(), transport=transport).subscribe_and_authorize()


async def test_live_session_read_event_skips_responses_by_default():
    notify = {"method": "mining.set_difficulty", "params": [8]}
    session = LiveStratumSession(
        profile(),
        transport=FakeTransport([json.dumps({"id": 99, "result": True}), json.dumps(notify)]),
    )
    event, payload = await session.read_event()
    assert event == "mining.set_difficulty"
    assert payload.difficulty == 8


async def test_live_session_submit_share_requires_authorization_and_records_rejection():
    session = LiveStratumSession(profile(), transport=FakeTransport([]))
    with pytest.raises(LiveStratumSessionError):
        await session.submit_share(
            job_id="j", extranonce2="00000000", ntime="5e9a5c00", nonce="00000000"
        )
    session.authorized = True
    session.transport = FakeTransport(
        [json.dumps({"id": 1, "result": None, "error": [21, "stale", None]})]
    )
    result = await session.submit_share(
        job_id="j", extranonce2="00000000", ntime="5e9a5c00", nonce="00000000"
    )
    assert result.accepted is False
    assert result.error[1] == "stale"


async def test_live_session_close_delegates_to_transport():
    transport = FakeTransport([])
    await LiveStratumSession(profile(), transport=transport).close()
    assert transport.closed is True


def test_difficulty_to_target_rejects_zero_and_decreases_with_difficulty():
    low = _difficulty_to_target(1)
    high = _difficulty_to_target(2)
    assert high < low
    with pytest.raises(ValueError):
        _difficulty_to_target(0)


def test_client_backoff_is_deterministic_and_capped(client):
    client.reconnect_attempts = 10
    first = client._calculate_backoff_delay()
    assert first == client._calculate_backoff_delay()
    assert first <= client.reconnect_backoff_max * 1.1


def test_client_circuit_breaker_opens_and_half_opens_after_timeout(client, monkeypatch):
    for _ in range(client._circuit_breaker_threshold):
        client._circuit_breaker_record_failure()
    assert client._circuit_breaker_allow_request() is False
    monkeypatch.setattr(
        "pythia_mining.stratum_client.time.time", lambda: client._circuit_breaker_last_failure + 61
    )
    assert client._circuit_breaker_allow_request() is True
    assert client._circuit_breaker_state == "half_open"
    client._circuit_breaker_record_success()
    assert client._circuit_breaker_state == "closed"


@pytest.mark.parametrize(
    "response", [{}, {"id": 1}, {"id": 1, "error": {"bad": "shape"}}, {"id": 1, "result": True}]
)
def test_client_pool_response_validation(client, response):
    expected = response == {"id": 1, "result": True}
    assert client._validate_pool_response(response) is expected


async def test_client_poll_live_event_records_difficulty(client):
    client.live_session = SimpleNamespace(
        read_event=AsyncMock(return_value=("mining.set_difficulty", SimpleNamespace(difficulty=16)))
    )
    assert await client.poll_live_event() is None
    assert client.current_difficulty == 16
    client._persist_metrics.assert_awaited()


async def test_client_poll_live_event_adds_notify_job_and_marks_clean_jobs_stale(client):
    client.current_jobs["old"] = MiningJob(
        "old", "00" * 32, ("aa", "bb"), [], "20000000", "1d00ffff", "5e9a5c00", 1
    )
    payload = SimpleNamespace(
        job_id="new",
        prevhash="11" * 32,
        coinbase1="aa",
        coinbase2="bb",
        merkle_branch=[],
        version="20000000",
        nbits="1d00ffff",
        ntime="5e9a5c00",
        clean_jobs=True,
    )
    client.live_session = SimpleNamespace(
        read_event=AsyncMock(return_value=("mining.notify", payload))
    )
    job = await client.poll_live_event()
    assert job.job_id == "new"
    assert "old" in client.stale_job_ids
    assert client.active_job_id == "new"


async def test_client_poll_live_event_handles_extranonce_and_unknown_events(client):
    client.live_session = SimpleNamespace(
        read_event=AsyncMock(
            return_value=(
                "mining.set_extranonce",
                SimpleNamespace(extranonce1="ff", extranonce2_size=8),
            )
        )
    )
    assert await client.poll_live_event() is None
    assert (client.extranonce1, client.extranonce2_size) == ("ff", 8)
    client.live_session.read_event = AsyncMock(
        return_value=("unknown", {"method": "vendor.message"})
    )
    assert await client.poll_live_event() is None


async def test_client_poll_live_event_timeout_returns_none_and_checks_stale(client):
    client.live_session = SimpleNamespace(
        read_event=AsyncMock(side_effect=StratumTransportError("timeout"))
    )
    client._check_block_height_for_stale_jobs = AsyncMock()
    assert await client.poll_live_event() is None
    client._check_block_height_for_stale_jobs.assert_awaited_once()


def test_client_health_score_penalizes_failures_latency_rejections_and_stale_jobs(client):
    client.connection_failures = 3
    client._circuit_breaker_state = "open"
    client.shares_submitted = 20
    client.shares_accepted = 10
    client.avg_latency = 2500
    client.stale_job_ids.add("old")
    assert 0 <= client.get_health_score() < 0.5


def test_client_status_reports_precise_last_job_reason(client):
    status = client.get_status()
    assert status["last_job_null_reason"] == "not_connected"
    assert status["production_state"] == "blocked"


async def test_client_disconnect_closes_live_session_and_records_state(client):
    client.live_session = SimpleNamespace(close=AsyncMock())
    client.is_connected = client.is_authenticated = True
    await client.disconnect()
    assert client.live_session is None
    assert client.connection_state == "DISCONNECTED"


def test_client_production_requires_credentials(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "production")
    with pytest.raises(ProductionConfigurationError):
        StratumClient("stratum+tcp://pool.example:3333", "", "", "Pool")


def test_dev_fixture_job_injection_disabled_in_production(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "production")
    c = StratumClient("stratum+tcp://pool.example:3333", "u", "p", "Pool")
    with pytest.raises(ProductionConfigurationError):
        c.inject_dev_fixture_target_job(1)


async def test_pool_manager_selects_current_healthy_pool(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")
    mgr = PoolManager({"a": {"url": "stratum+tcp://a:3333", "username": "u", "password": "p"}})
    pool = next(iter(mgr.pools.values()))
    pool.is_connected = pool.is_authenticated = True
    mgr.current_pool_key = "a"
    assert await mgr.get_best_pool() is pool


async def test_pool_manager_fails_over_to_secondary(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")
    mgr = PoolManager(
        {
            "primary": {
                "url": "stratum+tcp://p:3333",
                "username": "u",
                "password": "p",
                "priority": 1,
            },
            "secondary": {
                "url": "stratum+tcp://s:3333",
                "username": "u",
                "password": "p",
                "priority": 2,
            },
        }
    )
    primary, secondary = mgr.pools["primary"], mgr.pools["secondary"]
    primary.connect = AsyncMock(return_value=False)
    secondary.connect = AsyncMock(return_value=True)
    best = await mgr.get_best_pool()
    assert best is secondary
    assert mgr.current_pool_key == "secondary"


async def test_pool_manager_raises_when_all_pools_offline(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")
    mgr = PoolManager({"a": {"url": "stratum+tcp://a:3333", "username": "u", "password": "p"}})
    pool = mgr.pools["a"]
    pool.connect = AsyncMock(return_value=False)
    pool.connection_state = "ERROR"
    with pytest.raises(AllPoolsOfflineError):
        await mgr.get_best_pool()


def test_pool_manager_status_marks_active_pool(monkeypatch):
    monkeypatch.setenv("NODE_ENV", "development")
    mgr = PoolManager({"a": {"url": "stratum+tcp://a:3333", "username": "u", "password": "p"}})
    mgr.current_pool_key = "a"
    status = mgr.get_all_pools_status()[0]
    assert status["pool_id"] == "a"
    assert status["is_active"] is True
