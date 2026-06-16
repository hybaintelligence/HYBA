from __future__ import annotations

from pythia_mining.pool_profiles import (
    DEFAULT_POOL_SPECS,
    PoolCredentialConfig,
    build_profile,
    default_pool_config,
    load_pool_profiles,
    split_pool_url_credentials,
    validate_pool_config,
)


def test_braiins_default_profile_is_stratum_v1_job_capable() -> None:
    spec = DEFAULT_POOL_SPECS["braiins"]

    assert spec["stratum_version"] == 1
    assert spec["url"].startswith("stratum+tcp://")
    assert "stratum.braiins.com:3333" in spec["url"]


def test_inline_pool_url_credentials_are_promoted_and_stripped() -> None:
    clean_url, username, password = split_pool_url_credentials(
        "stratum+tcp://worker.name:p%40ssword@stratum.braiins.com:3333"
    )

    assert clean_url == "stratum+tcp://stratum.braiins.com:3333"
    assert username == "worker.name"
    assert password == "p@ssword"

    profile = build_profile(
        "braiins",
        name="Braiins Pool",
        url="stratum+tcp://worker.name:p%40ssword@stratum.braiins.com:3333",
        username="",
        password="",
        stratum_version=1,
    )

    assert profile.url == "stratum+tcp://stratum.braiins.com:3333"
    assert profile.username == "worker.name"
    assert profile.password == "p@ssword"
    assert "@" not in profile.url


def test_validate_pool_config_accepts_inline_credentials_without_separate_fields() -> None:
    config = PoolCredentialConfig(
        pool_id="braiins",
        name="Braiins Pool",
        url="stratum+tcp://worker:x@stratum.braiins.com:3333",
        stratum_version=1,
        tls_required=False,
        credential_mode="username_password",
    )

    checked = validate_pool_config(config)
    profile = checked.to_profile()

    assert profile.username == "worker"
    assert profile.password == "x"
    assert profile.url == "stratum+tcp://stratum.braiins.com:3333"


def test_env_url_only_inline_credentials_load_as_pool_profile(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv(
        "HYBA_POOL_BRAIINS_URL",
        "stratum+tcp://worker.name:token@stratum.braiins.com:3333",
    )
    monkeypatch.setenv("HYBA_POOL_BRAIINS_STRATUM_VERSION", "1")
    monkeypatch.delenv("HYBA_POOL_BRAIINS_USERNAME", raising=False)
    monkeypatch.delenv("HYBA_POOL_BRAIINS_PASSWORD", raising=False)

    profiles = {profile.pool_id: profile for profile in load_pool_profiles()}

    assert "braiins" in profiles
    assert profiles["braiins"].username == "worker.name"
    assert profiles["braiins"].password == "token"
    assert profiles["braiins"].url == "stratum+tcp://stratum.braiins.com:3333"


def test_default_pool_config_redacts_inline_credentials_in_public_dict(monkeypatch) -> None:
    monkeypatch.setenv(
        "HYBA_POOL_BRAIINS_URL",
        "stratum+tcp://worker.name:token@stratum.braiins.com:3333",
    )
    config = default_pool_config("braiins")

    public = config.to_dict(include_secret_fields=False)

    assert public["url"] == "stratum+tcp://stratum.braiins.com:3333"
    assert public["resolved_username"] == "<configured>"
    assert "token" not in str(public)
