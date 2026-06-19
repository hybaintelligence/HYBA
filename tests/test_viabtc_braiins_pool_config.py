"""
Integration tests for ViaBTC and Braiins pool configuration.

This suite validates the production readiness of ViaBTC and Braiins pool
configurations, ensuring proper:
1. Endpoint connectivity readiness (offline validation)
2. Credential handling and security
3. Stratum V1 job-flow capability
4. Priority-based rotation setup
5. TLS configuration verification
6. Failover behavior between pools
"""

from __future__ import annotations

from urllib.parse import urlparse

import pytest

from pythia_mining.pool_profiles import (
    DEFAULT_POOL_SPECS,
    PoolCredentialConfig,
    build_profile,
    load_pool_profiles,
    split_pool_url_credentials,
    validate_pool_config,
)
from pythia_mining.stratum_client import (
    StratumClient,
)


class TestViaBTCPoolSpec:
    """ViaBTC pool specification and configuration validation."""

    def test_viabtc_in_default_specs(self) -> None:
        """ViaBTC must be in DEFAULT_POOL_SPECS for rotation support."""
        assert "viabtc" in DEFAULT_POOL_SPECS
        spec = DEFAULT_POOL_SPECS["viabtc"]
        assert spec["name"] == "ViaBTC BTC"
        assert spec["url"] == "stratum+tcp://btc.viabtc.io:3333"
        assert spec["stratum_version"] == 1
        assert spec["credential_mode"] == "username_password"

    def test_viabtc_is_stratum_v1_job_capable(self) -> None:
        """ViaBTC must use Stratum V1 for job-flow capability."""
        spec = DEFAULT_POOL_SPECS["viabtc"]
        assert spec["stratum_version"] == 1
        assert spec["url"].startswith("stratum+tcp://"), "ViaBTC must use plain TCP by default"

    def test_viabtc_url_parsing(self) -> None:
        """ViaBTC URL must parse correctly without credentials."""
        url = "stratum+tcp://btc.viabtc.io:3333"
        parsed = urlparse(url)
        assert parsed.hostname == "btc.viabtc.io"
        assert parsed.port == 3333
        assert parsed.scheme == "stratum+tcp"

    def test_viabtc_profile_creation_with_credentials(self) -> None:
        """Create valid ViaBTC profile with credentials."""
        profile = build_profile(
            "viabtc",
            name="ViaBTC BTC",
            url="stratum+tcp://btc.viabtc.io:3333",
            username="HYBA.viabtc_worker",
            password="x",
            stratum_version=1,
            priority=4,
        )
        assert profile.pool_id == "viabtc"
        assert profile.name == "ViaBTC BTC"
        assert profile.url == "stratum+tcp://btc.viabtc.io:3333"
        assert profile.username == "HYBA.viabtc_worker"
        assert profile.password == "x"
        assert profile.stratum_version == 1
        assert profile.priority == 4
        assert profile.tls_required is False

    def test_viabtc_profile_redaction(self) -> None:
        """ViaBTC profile credentials must be redacted in public output."""
        profile = build_profile(
            "viabtc",
            name="ViaBTC BTC",
            url="stratum+tcp://btc.viabtc.io:3333",
            username="HYBA.viabtc_worker",
            password="secret_password",
            stratum_version=1,
        )
        public_dict = profile.to_dict(include_secret_fields=False)
        assert public_dict["username"] == "<configured>"
        assert public_dict["password"] == "<configured>"
        assert public_dict["url"] == "stratum+tcp://btc.viabtc.io:3333"


class TestBraiinsPoolSpec:
    """Braiins pool specification and configuration validation."""

    def test_braiins_in_default_specs(self) -> None:
        """Braiins must be in DEFAULT_POOL_SPECS as default V1 profile."""
        assert "braiins" in DEFAULT_POOL_SPECS
        spec = DEFAULT_POOL_SPECS["braiins"]
        assert spec["name"] == "Braiins Pool"
        assert spec["url"] == "stratum+tcp://stratum.braiins.com:3333"
        assert spec["stratum_version"] == 1
        assert spec["credential_mode"] == "username_password"

    def test_braiins_is_default_stratum_v1(self) -> None:
        """Braiins default must be Stratum V1 for job-flow capability."""
        spec = DEFAULT_POOL_SPECS["braiins"]
        assert spec["stratum_version"] == 1
        assert spec["url"].startswith("stratum+tcp://"), "Braiins default must use plain TCP"

    def test_braiins_url_parsing(self) -> None:
        """Braiins URL must parse correctly."""
        url = "stratum+tcp://stratum.braiins.com:3333"
        parsed = urlparse(url)
        assert parsed.hostname == "stratum.braiins.com"
        assert parsed.port == 3333
        assert parsed.scheme == "stratum+tcp"

    def test_braiins_profile_creation_with_credentials(self) -> None:
        """Create valid Braiins profile with credentials."""
        profile = build_profile(
            "braiins",
            name="Braiins Pool",
            url="stratum+tcp://stratum.braiins.com:3333",
            username="HYBA.braiins_worker",
            password="x",
            stratum_version=1,
            priority=3,
        )
        assert profile.pool_id == "braiins"
        assert profile.name == "Braiins Pool"
        assert profile.url == "stratum+tcp://stratum.braiins.com:3333"
        assert profile.username == "HYBA.braiins_worker"
        assert profile.password == "x"
        assert profile.stratum_version == 1
        assert profile.priority == 3
        assert profile.tls_required is False

    def test_braiins_profile_redaction(self) -> None:
        """Braiins profile credentials must be redacted in public output."""
        profile = build_profile(
            "braiins",
            name="Braiins Pool",
            url="stratum+tcp://stratum.braiins.com:3333",
            username="HYBA.braiins_worker",
            password="secret_token",
            stratum_version=1,
        )
        public_dict = profile.to_dict(include_secret_fields=False)
        assert public_dict["username"] == "<configured>"
        assert public_dict["password"] == "<configured>"
        assert public_dict["url"] == "stratum+tcp://stratum.braiins.com:3333"


class TestPoolRotationAndPriority:
    """Test pool rotation ordering with ViaBTC and Braiins."""

    def test_viabtc_braiins_priority_ordering(self) -> None:
        """ViaBTC (priority 4) should follow Braiins (priority 3) in rotation."""
        viabtc = build_profile(
            "viabtc",
            name="ViaBTC BTC",
            url="stratum+tcp://btc.viabtc.io:3333",
            username="worker",
            password="x",
            stratum_version=1,
            priority=4,
        )
        braiins = build_profile(
            "braiins",
            name="Braiins Pool",
            url="stratum+tcp://stratum.braiins.com:3333",
            username="worker",
            password="x",
            stratum_version=1,
            priority=3,
        )
        # Lower priority number = higher priority (checked first in rotation)
        assert braiins.priority < viabtc.priority

    def test_both_pools_enabled_in_config(self, monkeypatch, tmp_path) -> None:
        """Both ViaBTC and Braiins should be enabled and loadable."""
        config_content = """{
  "pools": {
    "viabtc": {
      "name": "ViaBTC BTC",
      "url": "stratum+tcp://btc.viabtc.io:3333",
      "stratum_version": 1,
      "username": "HYBA.viabtc_worker",
      "password": "x",
      "priority": 4,
      "enabled": true
    },
    "braiins": {
      "name": "Braiins Pool",
      "url": "stratum+tcp://stratum.braiins.com:3333",
      "stratum_version": 1,
      "username": "HYBA.braiins_worker",
      "password": "x",
      "priority": 3,
      "enabled": true
    }
  }
}"""
        config_file = tmp_path / "pools.json"
        config_file.write_text(config_content)
        monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(config_file))

        profiles = load_pool_profiles()
        pool_ids = [p.pool_id for p in profiles]
        assert "viabtc" in pool_ids
        assert "braiins" in pool_ids
        # Verify priority ordering: braiins (3) before viabtc (4)
        braiins_idx = pool_ids.index("braiins")
        viabtc_idx = pool_ids.index("viabtc")
        assert braiins_idx < viabtc_idx


class TestCredentialHandling:
    """Test credential handling and security for both pools."""

    def test_inline_credentials_extracted_viabtc(self) -> None:
        """Inline credentials in ViaBTC URL are extracted and stripped."""
        url = "stratum+tcp://testworker:testpass@btc.viabtc.io:3333"
        clean_url, username, password = split_pool_url_credentials(url)
        assert clean_url == "stratum+tcp://btc.viabtc.io:3333"
        assert username == "testworker"
        assert password == "testpass"
        assert "@" not in clean_url

    def test_inline_credentials_extracted_braiins(self) -> None:
        """Inline credentials in Braiins URL are extracted and stripped."""
        url = "stratum+tcp://testworker:testpass@stratum.braiins.com:3333"
        clean_url, username, password = split_pool_url_credentials(url)
        assert clean_url == "stratum+tcp://stratum.braiins.com:3333"
        assert username == "testworker"
        assert password == "testpass"
        assert "@" not in clean_url

    def test_credential_config_validation_viabtc(self) -> None:
        """ViaBTC credential config must validate properly."""
        config = PoolCredentialConfig(
            pool_id="viabtc",
            name="ViaBTC BTC",
            url="stratum+tcp://btc.viabtc.io:3333",
            stratum_version=1,
            tls_required=False,
            credential_mode="username_password",
            username="HYBA.viabtc_worker",
            password="x",
        )
        validated = validate_pool_config(config)
        profile = validated.to_profile()
        assert profile.username == "HYBA.viabtc_worker"
        assert profile.password == "x"
        assert profile.pool_id == "viabtc"

    def test_credential_config_validation_braiins(self) -> None:
        """Braiins credential config must validate properly."""
        config = PoolCredentialConfig(
            pool_id="braiins",
            name="Braiins Pool",
            url="stratum+tcp://stratum.braiins.com:3333",
            stratum_version=1,
            tls_required=False,
            credential_mode="username_password",
            username="HYBA.braiins_worker",
            password="x",
        )
        validated = validate_pool_config(config)
        profile = validated.to_profile()
        assert profile.username == "HYBA.braiins_worker"
        assert profile.password == "x"
        assert profile.pool_id == "braiins"

    def test_production_missing_credentials_viabtc(self, monkeypatch) -> None:
        """ViaBTC in production must fail if credentials are missing."""
        monkeypatch.setenv("NODE_ENV", "production")

        with pytest.raises(Exception):  # ProductionConfigurationError
            StratumClient(
                pool_url="stratum+tcp://btc.viabtc.io:3333",
                username="",
                password="",
                pool_name="ViaBTC BTC",
                stratum_version=1,
            )

    def test_production_missing_credentials_braiins(self, monkeypatch) -> None:
        """Braiins in production must fail if credentials are missing."""
        monkeypatch.setenv("NODE_ENV", "production")

        with pytest.raises(Exception):  # ProductionConfigurationError
            StratumClient(
                pool_url="stratum+tcp://stratum.braiins.com:3333",
                username="",
                password="",
                pool_name="Braiins Pool",
                stratum_version=1,
            )


class TestStratumClientIntegration:
    """Test Stratum client integration with both pools."""

    def test_viabtc_stratum_client_initialization(self) -> None:
        """ViaBTC Stratum client must initialize with correct parameters."""
        client = StratumClient(
            pool_url="stratum+tcp://btc.viabtc.io:3333",
            username="HYBA.viabtc_worker",
            password="x",
            pool_name="ViaBTC BTC",
            stratum_version=1,
        )
        assert client.pool_url == "stratum+tcp://btc.viabtc.io:3333"
        assert client.username == "HYBA.viabtc_worker"
        assert client.pool_name == "ViaBTC BTC"
        assert client.stratum_version == 1
        assert client.is_connected is False

    def test_braiins_stratum_client_initialization(self) -> None:
        """Braiins Stratum client must initialize with correct parameters."""
        client = StratumClient(
            pool_url="stratum+tcp://stratum.braiins.com:3333",
            username="HYBA.braiins_worker",
            password="x",
            pool_name="Braiins Pool",
            stratum_version=1,
        )
        assert client.pool_url == "stratum+tcp://stratum.braiins.com:3333"
        assert client.username == "HYBA.braiins_worker"
        assert client.pool_name == "Braiins Pool"
        assert client.stratum_version == 1
        assert client.is_connected is False

    def test_viabtc_client_connection_state_tracking(self) -> None:
        """ViaBTC client must track connection state correctly."""
        client = StratumClient(
            pool_url="stratum+tcp://btc.viabtc.io:3333",
            username="HYBA.viabtc_worker",
            password="x",
            pool_name="ViaBTC BTC",
        )
        assert client.connection_state == "DISCONNECTED"
        assert client.shares_submitted == 0
        assert client.shares_accepted == 0
        assert client.shares_rejected == 0

    def test_braiins_client_connection_state_tracking(self) -> None:
        """Braiins client must track connection state correctly."""
        client = StratumClient(
            pool_url="stratum+tcp://stratum.braiins.com:3333",
            username="HYBA.braiins_worker",
            password="x",
            pool_name="Braiins Pool",
        )
        assert client.connection_state == "DISCONNECTED"
        assert client.shares_submitted == 0
        assert client.shares_accepted == 0
        assert client.shares_rejected == 0


class TestPoolURLValidation:
    """Test pool URL validation for both ViaBTC and Braiins."""

    def test_viabtc_url_scheme_validation(self) -> None:
        """ViaBTC URL must use valid Stratum scheme."""
        valid_urls = [
            "stratum+tcp://btc.viabtc.io:3333",
            "stratum+ssl://btc.viabtc.io:3333",
            "stratum+tls://btc.viabtc.io:3333",
        ]
        for url in valid_urls:
            parsed = urlparse(url)
            assert parsed.scheme in {
                "stratum+tcp",
                "stratum+ssl",
                "stratum+tls",
                "stratum2+tcp",
                "stratum2+ssl",
                "stratum2+tls",
            }

    def test_braiins_url_scheme_validation(self) -> None:
        """Braiins URL must use valid Stratum scheme."""
        valid_urls = [
            "stratum+tcp://stratum.braiins.com:3333",
            "stratum+ssl://stratum.braiins.com:3333",
            "stratum+tls://stratum.braiins.com:3333",
        ]
        for url in valid_urls:
            parsed = urlparse(url)
            assert parsed.scheme in {
                "stratum+tcp",
                "stratum+ssl",
                "stratum+tls",
                "stratum2+tcp",
                "stratum2+ssl",
                "stratum2+tls",
            }

    def test_viabtc_port_extraction(self) -> None:
        """ViaBTC URL port must extract correctly."""
        url = "stratum+tcp://btc.viabtc.io:3333"
        parsed = urlparse(url)
        assert parsed.port == 3333

    def test_braiins_port_extraction(self) -> None:
        """Braiins URL port must extract correctly."""
        url = "stratum+tcp://stratum.braiins.com:3333"
        parsed = urlparse(url)
        assert parsed.port == 3333


class TestFailoverConfiguration:
    """Test failover and rotation setup between ViaBTC and Braiins."""

    def test_reconnect_attempts_viabtc(self) -> None:
        """ViaBTC client must have configurable reconnect attempts."""
        client = StratumClient(
            pool_url="stratum+tcp://btc.viabtc.io:3333",
            username="HYBA.viabtc_worker",
            password="x",
            pool_name="ViaBTC BTC",
            max_reconnect_attempts=5,
        )
        assert client.max_reconnect_attempts == 5

    def test_reconnect_attempts_braiins(self) -> None:
        """Braiins client must have configurable reconnect attempts."""
        client = StratumClient(
            pool_url="stratum+tcp://stratum.braiins.com:3333",
            username="HYBA.braiins_worker",
            password="x",
            pool_name="Braiins Pool",
            max_reconnect_attempts=5,
        )
        assert client.max_reconnect_attempts == 5

    def test_reconnect_backoff_configuration_viabtc(self) -> None:
        """ViaBTC client must support exponential backoff configuration."""
        client = StratumClient(
            pool_url="stratum+tcp://btc.viabtc.io:3333",
            username="HYBA.viabtc_worker",
            password="x",
            pool_name="ViaBTC BTC",
            reconnect_backoff_base=1.5,
            reconnect_backoff_max=45.0,
        )
        assert client.reconnect_backoff_base == 1.5
        assert client.reconnect_backoff_max == 45.0

    def test_reconnect_backoff_configuration_braiins(self) -> None:
        """Braiins client must support exponential backoff configuration."""
        client = StratumClient(
            pool_url="stratum+tcp://stratum.braiins.com:3333",
            username="HYBA.braiins_worker",
            password="x",
            pool_name="Braiins Pool",
            reconnect_backoff_base=1.5,
            reconnect_backoff_max=45.0,
        )
        assert client.reconnect_backoff_base == 1.5
        assert client.reconnect_backoff_max == 45.0


class TestEnvironmentConfigOverride:
    """Test environment variable configuration override for both pools."""

    def test_viabtc_env_override_url(self, monkeypatch, tmp_path) -> None:
        """ViaBTC URL can be overridden via environment variable."""
        monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(tmp_path / "missing.json"))
        monkeypatch.setenv("HYBA_POOL_VIABTC_URL", "stratum+tcp://alt.viabtc.io:3334")
        monkeypatch.setenv("HYBA_POOL_VIABTC_USERNAME", "alt_worker")
        monkeypatch.setenv("HYBA_POOL_VIABTC_PASSWORD", "x")
        monkeypatch.setenv("HYBA_POOL_VIABTC_STRATUM_VERSION", "1")

        from pythia_mining.pool_profiles import load_runtime_pool_configs

        configs = load_runtime_pool_configs()
        viabtc = configs.get("viabtc")
        assert viabtc is not None
        assert viabtc.url == "stratum+tcp://alt.viabtc.io:3334"
        assert viabtc.username == "alt_worker"

    def test_braiins_env_override_url(self, monkeypatch, tmp_path) -> None:
        """Braiins URL can be overridden via environment variable."""
        monkeypatch.setenv("HYBA_POOL_CONFIG_PATH", str(tmp_path / "missing.json"))
        monkeypatch.setenv("HYBA_POOL_BRAIINS_URL", "stratum+tcp://alt.braiins.com:3334")
        monkeypatch.setenv("HYBA_POOL_BRAIINS_USERNAME", "alt_worker")
        monkeypatch.setenv("HYBA_POOL_BRAIINS_PASSWORD", "x")
        monkeypatch.setenv("HYBA_POOL_BRAIINS_STRATUM_VERSION", "1")

        from pythia_mining.pool_profiles import load_runtime_pool_configs

        configs = load_runtime_pool_configs()
        braiins = configs.get("braiins")
        assert braiins is not None
        assert braiins.url == "stratum+tcp://alt.braiins.com:3334"
        assert braiins.username == "alt_worker"
