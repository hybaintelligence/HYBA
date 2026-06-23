from __future__ import annotations

from pythia_mining.pool_profiles import (
    DEFAULT_POOL_SPECS,
    PoolCredentialConfig,
    build_profile,
    default_pool_config,
    load_pool_profiles,
    order_profiles,
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


def test_validate_pool_config_accepts_inline_credentials_without_separate_fields() -> (
    None
):
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


def test_env_url_only_inline_credentials_load_as_pool_profile(
    monkeypatch, tmp_path
) -> None:
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


def test_default_pool_config_redacts_inline_credentials_in_public_dict(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "HYBA_POOL_BRAIINS_URL",
        "stratum+tcp://worker.name:token@stratum.braiins.com:3333",
    )
    config = default_pool_config("braiins")

    public = config.to_dict(include_secret_fields=False)

    assert public["url"] == "stratum+tcp://stratum.braiins.com:3333"
    assert public["resolved_username"] == "<configured>"
    assert "token" not in str(public)


def test_env_configured_pool_overrides_disabled_runtime_config(
    monkeypatch, tmp_path
) -> None:
    """Env-configured pools should enable even if runtime config has enabled=false."""
    runtime_config_file = tmp_path / "pools.json"
    runtime_config_file.write_text(
        """{
      "pools": {
        "braiins": {
          "url": "stratum+tcp://stratum.braiins.com:3333",
          "stratum_version": 1,
          "username": "",
          "password": "",
          "enabled": false,
          "priority": 20
        }
      }
    }"""
    )

    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(runtime_config_file))
    monkeypatch.setenv("HYBA_POOL_BRAIINS_USERNAME", "worker")
    monkeypatch.setenv("HYBA_POOL_BRAIINS_PASSWORD", "x")

    profiles = {profile.pool_id: profile for profile in load_pool_profiles()}

    assert "braiins" in profiles
    assert profiles["braiins"].username == "worker"
    assert profiles["braiins"].password == "x"


def test_runtime_pool_config_disabled_flag_respected_without_env_override(
    monkeypatch, tmp_path
) -> None:
    """Without env vars, runtime config enabled=false should prevent profile from loading."""
    runtime_config_file = tmp_path / "pools.json"
    runtime_config_file.write_text(
        """{
      "pools": {
        "braiins": {
          "url": "stratum+tcp://stratum.braiins.com:3333",
          "stratum_version": 1,
          "username": "stored_worker",
          "password": "stored_pass",
          "enabled": false,
          "priority": 20
        }
      }
    }"""
    )

    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(runtime_config_file))
    monkeypatch.delenv("HYBA_POOL_BRAIINS_USERNAME", raising=False)
    monkeypatch.delenv("HYBA_POOL_BRAIINS_PASSWORD", raising=False)

    profiles = {profile.pool_id: profile for profile in load_pool_profiles()}

    assert "braiins" not in profiles


def test_rotation_pools_all_stratum_v1_job_capable(monkeypatch, tmp_path) -> None:
    """All rotation pool defaults must be job-flow capable (Stratum V1)."""
    monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(tmp_path / "missing.json"))
    monkeypatch.setenv("HYBA_POOL_VIABTC_USERNAME", "viabtc_worker")
    monkeypatch.setenv("HYBA_POOL_VIABTC_PASSWORD", "x")
    monkeypatch.setenv("HYBA_POOL_BRAIINS_USERNAME", "braiins_worker")
    monkeypatch.setenv("HYBA_POOL_BRAIINS_PASSWORD", "x")
    monkeypatch.setenv("HYBA_POOL_NICEHASH_WORKER", "nicehash_worker")
    monkeypatch.setenv("HYBA_POOL_NICEHASH_NH_POOL_ID", "pool123")
    monkeypatch.setenv(
        "HYBA_POOL_CKPOOL_BTC_ADDRESS", "1A1z7agoat4xFrqyqyUeGvW1vKjjzJ8D2s"
    )

    profiles = {profile.pool_id: profile for profile in load_pool_profiles()}

    for pool_id in ("viabtc", "braiins", "nicehash", "ckpool"):
        assert pool_id in profiles, f"{pool_id} not loaded"
        profile = profiles[pool_id]
        assert (
            profile.stratum_version == 1
        ), f"{pool_id} must be Stratum V1, got {profile.stratum_version}"
        assert profile.username, f"{pool_id} missing username"
        assert profile.password, f"{pool_id} missing password"


# ---------------------------------------------------------------------------
# TLS enforcement
# ---------------------------------------------------------------------------


def test_non_tls_url_rejected_when_tls_required() -> None:
    """validate_pool_url must reject plain stratum+tcp when tls_required=True."""
    from pythia_mining.pool_profiles import PoolProfileError, validate_pool_url
    import pytest

    with pytest.raises(PoolProfileError, match="TLS"):
        validate_pool_url(
            "stratum+tcp://sha256.auto.nicehash.com:443", tls_required=True
        )


def test_tls_url_accepted_when_tls_required() -> None:
    """validate_pool_url must accept stratum+ssl when tls_required=True."""
    from pythia_mining.pool_profiles import validate_pool_url

    url = validate_pool_url(
        "stratum+ssl://sha256.auto.nicehash.com:443", tls_required=True
    )
    assert "sha256.auto.nicehash.com" in url


def test_nicehash_default_spec_requires_tls() -> None:
    """NiceHash default spec must declare tls_required=True."""
    assert DEFAULT_POOL_SPECS["nicehash"]["tls_required"] is True
    assert DEFAULT_POOL_SPECS["nicehash"]["url"].startswith("stratum+ssl://")


# ---------------------------------------------------------------------------
# Priority ordering and failover sequencing
# ---------------------------------------------------------------------------


def test_order_profiles_produces_ascending_priority() -> None:
    """order_profiles must sort profiles by ascending priority value."""
    profiles = [
        build_profile(
            "b",
            name="B",
            url="stratum+tcp://b.example.com:3333",
            username="u",
            password="x",
            priority=30,
        ),
        build_profile(
            "a",
            name="A",
            url="stratum+tcp://a.example.com:3333",
            username="u",
            password="x",
            priority=10,
        ),
        build_profile(
            "c",
            name="C",
            url="stratum+tcp://c.example.com:3333",
            username="u",
            password="x",
            priority=20,
        ),
    ]
    ordered = order_profiles(profiles)
    priorities = [p.priority for p in ordered]
    assert priorities == sorted(priorities)
    assert [p.pool_id for p in ordered] == ["a", "c", "b"]


def test_all_default_specs_have_unique_priorities() -> None:
    """Each default pool spec must have a unique priority to guarantee stable failover order."""
    priorities = [spec["priority"] for spec in DEFAULT_POOL_SPECS.values()]
    assert len(set(priorities)) == len(
        priorities
    ), f"duplicate priorities in DEFAULT_POOL_SPECS: {priorities}"


def test_viabtc_has_highest_priority_among_defaults() -> None:
    """ViaBTC is configured as primary and must have the lowest priority number."""
    specs = DEFAULT_POOL_SPECS
    viabtc_priority = specs["viabtc"]["priority"]
    for pool_id, spec in specs.items():
        if pool_id != "viabtc":
            assert (
                viabtc_priority < spec["priority"]
            ), f"viabtc priority {viabtc_priority} not lower than {pool_id} priority {spec['priority']}"


# ---------------------------------------------------------------------------
# Credential redaction in public status surfaces
# ---------------------------------------------------------------------------


def test_pool_profile_to_dict_redacts_username_and_password() -> None:
    """to_dict(include_secret_fields=False) must replace credentials with '<configured>'."""
    profile = build_profile(
        "redact_test",
        name="Redact Test",
        url="stratum+tcp://test.example.com:3333",
        username="real_worker_name",
        password="real_secret_password",
    )
    public = profile.to_dict(include_secret_fields=False)

    assert "real_worker_name" not in str(public)
    assert "real_secret_password" not in str(public)
    assert public["username"] == "<configured>"
    assert public["password"] == "<configured>"


def test_pool_profile_to_dict_exposes_credentials_when_requested() -> None:
    """to_dict(include_secret_fields=True) must return actual values for internal use."""
    profile = build_profile(
        "expose_test",
        name="Expose Test",
        url="stratum+tcp://test.example.com:3333",
        username="internal_worker",
        password="internal_pass",
    )
    internal = profile.to_dict(include_secret_fields=True)

    assert internal["username"] == "internal_worker"
    assert internal["password"] == "internal_pass"


# ---------------------------------------------------------------------------
# PoolProfile validation rejects malformed configs at construction time
# ---------------------------------------------------------------------------


def test_validate_profile_rejects_empty_username() -> None:
    """build_profile must raise PoolProfileError when username is empty."""
    import pytest
    from pythia_mining.pool_profiles import PoolProfileError

    with pytest.raises(PoolProfileError, match="username"):
        build_profile(
            "no_user",
            name="No User",
            url="stratum+tcp://test.example.com:3333",
            username="",
            password="x",
        )


def test_validate_profile_rejects_unsupported_scheme() -> None:
    """build_profile must raise PoolProfileError for unsupported URL schemes."""
    import pytest
    from pythia_mining.pool_profiles import PoolProfileError

    with pytest.raises(PoolProfileError):
        build_profile(
            "bad_scheme",
            name="Bad Scheme",
            url="http://test.example.com:3333",
            username="worker",
            password="x",
        )


def test_validate_profile_rejects_missing_port() -> None:
    """build_profile must raise PoolProfileError when the URL has no port."""
    import pytest
    from pythia_mining.pool_profiles import PoolProfileError

    with pytest.raises(PoolProfileError, match="port"):
        build_profile(
            "no_port",
            name="No Port",
            url="stratum+tcp://test.example.com",
            username="worker",
            password="x",
        )


# ---------------------------------------------------------------------------
# Stratum V2 scheme contract
# ---------------------------------------------------------------------------


def test_stratumv2_default_spec_uses_stratum2_scheme() -> None:
    """The stratumv2 default spec must use a stratum2+ URL scheme, not stratum+."""
    spec = DEFAULT_POOL_SPECS["stratumv2"]
    assert spec["url"].startswith(
        "stratum2+"
    ), f"stratumv2 URL must start with 'stratum2+', got: {spec['url']}"
    assert spec["stratum_version"] == 2


def test_stratum_v1_url_on_v2_port_3336_is_rejected() -> None:
    """stratum+ scheme on port 3336 must be rejected (V2 port requires stratum2+ scheme)."""
    import pytest
    from pythia_mining.pool_profiles import PoolProfileError, validate_pool_url

    with pytest.raises(PoolProfileError):
        validate_pool_url("stratum+tcp://pool.example.com:3336")


# ---------------------------------------------------------------------------
# Claim-boundary: no revenue/financial fabrication in telemetry paths
# ---------------------------------------------------------------------------


def test_solver_without_configured_capacity_reports_no_hashrate() -> None:
    """An unconfigured solver must not report a hashrate — claim boundary enforced at source."""
    import sys

    sys.path.insert(
        0,
        str(
            __import__("pathlib").Path(__file__).resolve().parents[1] / "python_backend"
        ),
    )
    from pythia_mining.dodecahedral_solver import DodecahedralQuantumSolver

    solver = DodecahedralQuantumSolver()  # no configured_capacity_ehs
    metrics = solver.get_metrics()

    assert (
        metrics["hashrate_ehs"] is None
    ), f"unconfigured solver reported hashrate_ehs={metrics['hashrate_ehs']}"
    assert metrics["capacity_source"] == "not_configured"
    assert metrics["telemetry_source"] == "derived_runtime_state"


def test_benchmark_projection_only_mode_reports_no_effective_hashrate() -> None:
    """benchmark_vs_asic without measured input must not claim an effective hashrate."""
    import sys

    sys.path.insert(
        0,
        str(
            __import__("pathlib").Path(__file__).resolve().parents[1] / "python_backend"
        ),
    )
    from pythia_mining.phi_scaling_engine import benchmark_vs_asic

    result = benchmark_vs_asic(measured_hashes_per_second=None)

    assert result["benchmark_mode"] == "projection_only"
    assert result["effective_hashes_per_second"] is None
    assert result["projected_vs_asic_ratio"] is None
    assert result["measured_hashes_per_second"] is None


def test_benchmark_measured_mode_exposes_ratio_as_finite() -> None:
    """benchmark_vs_asic with measured input must produce a finite ratio, not None."""
    import math
    import sys

    sys.path.insert(
        0,
        str(
            __import__("pathlib").Path(__file__).resolve().parents[1] / "python_backend"
        ),
    )
    from pythia_mining.phi_scaling_engine import benchmark_vs_asic

    result = benchmark_vs_asic(measured_hashes_per_second=1_000_000.0)

    assert result["benchmark_mode"] == "measured_input"
    assert result["effective_hashes_per_second"] is not None
    assert result["projected_vs_asic_ratio"] is not None
    assert math.isfinite(result["projected_vs_asic_ratio"])
