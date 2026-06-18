"""Production secret-gate invariants for live mining.

The live miner may use development fixture bypasses only in explicit non-live,
non-production development mode.  When production or live mining flags are set,
HYBA_ALLOW_DEV_FIXTURES must fail closed before any pool/job/search path can run.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

from pythia_mining.phi_config import initialize_production_secrets  # noqa: E402


def _clear_gate_env(monkeypatch: Any) -> None:
    for name in (
        "HYBA_ALLOW_DEV_FIXTURES",
        "HYBA_ENV",
        "NODE_ENV",
        "HYBA_ENABLE_LIVE_STRATUM",
        "HYBA_ENABLE_LIVE_SHARE_SUBMIT",
        "JWT_SECRET",
        "HYBA_OPERATOR_CREDENTIALS",
        "POOL_PRIMARY_CREDENTIALS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_dev_fixture_bypass_is_refused_in_production(monkeypatch: Any) -> None:
    _clear_gate_env(monkeypatch)
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENV", "production")

    with pytest.raises(SystemExit):
        initialize_production_secrets()


def test_dev_fixture_bypass_is_refused_when_live_stratum_enabled(monkeypatch: Any) -> None:
    _clear_gate_env(monkeypatch)
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")

    with pytest.raises(SystemExit):
        initialize_production_secrets()


def test_dev_fixture_bypass_is_refused_when_live_submit_enabled(monkeypatch: Any) -> None:
    _clear_gate_env(monkeypatch)
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")

    with pytest.raises(SystemExit):
        initialize_production_secrets()


def test_dev_fixture_bypass_is_allowed_only_in_explicit_non_live_development(monkeypatch: Any) -> None:
    _clear_gate_env(monkeypatch)
    monkeypatch.setenv("HYBA_ALLOW_DEV_FIXTURES", "true")
    monkeypatch.setenv("HYBA_ENV", "development")
    monkeypatch.setenv("NODE_ENV", "development")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "false")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "false")

    assert initialize_production_secrets() == {"status": "DEV_PASS"}


def test_secure_production_secrets_pass_without_fixture_bypass(monkeypatch: Any) -> None:
    _clear_gate_env(monkeypatch)
    monkeypatch.setenv("HYBA_ENV", "production")
    monkeypatch.setenv("NODE_ENV", "production")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_STRATUM", "true")
    monkeypatch.setenv("HYBA_ENABLE_LIVE_SHARE_SUBMIT", "true")
    monkeypatch.setenv("JWT_SECRET", "x" * 64)
    monkeypatch.setenv("HYBA_OPERATOR_CREDENTIALS", "argon2id$operator$hash$example")
    monkeypatch.setenv("POOL_PRIMARY_CREDENTIALS", "pool-credential-material")

    assert initialize_production_secrets() == {"status": "SEC_SECURE"}
