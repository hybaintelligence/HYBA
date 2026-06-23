from __future__ import annotations

import os
import re
from argparse import Namespace
from pathlib import Path

import importlib.util

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "create_mining_env.py"
spec = importlib.util.spec_from_file_location("create_mining_env", SCRIPT_PATH)
assert spec and spec.loader
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def _args(**overrides: object) -> Namespace:
    defaults = {
        "node_env": "production",
        "hyba_env": "production",
        "host": "127.0.0.1",
        "port": 3000,
        "backend_url": "http://127.0.0.1:3001",
        "log_level": "info",
        "jwt_secret": None,
        "internal_health_token": None,
        "pool_primary_credentials": None,
        "operator_user": "operator",
        "operator_password": "local-password",
        "operator_hash": "$argon2id$v=19$m=65536,t=3,p=2$c2FsdA$ZGlnZXN0",
        "operator_role": "mining_operator",
        "live_stratum": True,
        "live_share_submit": False,
        "approval_id": None,
        "autoconnect": False,
        "capacity_ehs": 1.0,
        "autonomy_level": "supervised",
        "operator_approval_required": True,
        "max_hashrate_ehs": 0.001,
        "max_power_watts": 500.0,
        "viabtc_url": "stratum+tcp://btc.viabtc.io:3333",
        "viabtc_user": "PYTHIA.001",
        "viabtc_password": "123",
        "viabtc_stratum_version": "1",
    }
    defaults.update(overrides)
    return Namespace(**defaults)


def test_build_env_sets_required_clean_run_secrets() -> None:
    env = cli.build_env(_args())

    assert len(env["JWT_SECRET"]) >= 32
    assert len(env["HYBA_INTERNAL_HEALTH_TOKEN"]) >= 32
    assert len(env["POOL_PRIMARY_CREDENTIALS"]) >= 16
    assert re.match(
        r"operator:\$argon2id\$.*:mining_operator", env["HYBA_OPERATOR_CREDENTIALS"]
    )
    assert env["HYBA_POOL_VIABTC_USERNAME"] == "PYTHIA.001"
    assert env["HYBA_POOL_VIABTC_PASSWORD"] == "123"
    assert env["HYBA_ENABLE_LIVE_SHARE_SUBMIT"] == "false"
    assert env["HYBA_AUTONOMY_LEVEL"] == "supervised"


def test_write_env_uses_private_permissions(tmp_path: Path) -> None:
    env_file = tmp_path / ".env.mining.local"

    cli.write_env(env_file, cli.build_env(_args(jwt_secret="x" * 48)), overwrite=False)

    assert env_file.read_text(encoding="utf-8").startswith(
        "# HYBA local mining configuration"
    )
    assert oct(os.stat(env_file).st_mode & 0o777) == "0o600"


def test_validator_accepts_cli_viabtc_numeric_pool_password(monkeypatch) -> None:
    import importlib.util

    validator_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "validate_production_env.py"
    )
    spec = importlib.util.spec_from_file_location(
        "validate_production_env", validator_path
    )
    assert spec and spec.loader
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)

    env = cli.build_env(_args())
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    assert validator.main() == 0
