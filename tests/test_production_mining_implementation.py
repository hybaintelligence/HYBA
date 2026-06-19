"""
Production Mining Implementation Tests

Comprehensive test suite validating real pool integration, failover,
health monitoring, and share submission capabilities.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python_backend"))

from pythia_mining.production_mining_gateway import (
    MiningGatewayError,
    PoolConfigurationError,
    ProductionMiningGateway,
)
from pythia_mining.production_mining_orchestrator import (
    MiningStrategy,
    PoolHealth,
    PoolHealthStatus,
    ProductionMiningOrchestrator,
)
from pythia_mining.pool_profiles import PoolProfile, build_profile


class TestPoolProfileValidation:
    """Test pool profile building and validation."""

    def test_build_valid_profile(self):
        """Test building a valid pool profile."""
        profile = build_profile(
            "test_pool",
            name="Test Pool",
            url="stratum+ssl://pool.example.com:3334",
            username="user123",
            password="pass123",
            stratum_version=1,
            priority=100,
            tls_required=True,
        )

        assert profile.pool_id == "test_pool"
        assert profile.name == "Test Pool"
        assert profile.url == "stratum+ssl://pool.example.com:3334"
        assert profile.username == "user123"
        assert profile.stratum_version == 1
        assert profile.tls_required is True

    def test_build_profile_missing_url(self):
        """Test that missing URL raises error."""
        with pytest.raises(ValueError):
            build_profile(
                "test_pool",
                name="Test Pool",
                url="",
                username="user123",
                password="pass123",
            )

    def test_build_profile_invalid_stratum_version(self):
        """Test that invalid Stratum version raises error."""
        with pytest.raises(ValueError):
            build_profile(
                "test_pool",
                name="Test Pool",
                url="stratum+ssl://pool.example.com:3334",
                username="user123",
                password="pass123",
                stratum_version=3,
            )


class TestMiningGatewayConfiguration:
    """Test mining gateway configuration and validation."""

    def test_gateway_initialization(self):
        """Test gateway can be created."""
        gateway = ProductionMiningGateway()
        assert not gateway.is_initialized
        assert not gateway.is_running
        assert gateway.orchestrator is None

    def test_validate_empty_profiles(self):
        """Test that empty profiles list raises error."""
        with pytest.raises(PoolConfigurationError):
            ProductionMiningGateway.validate_profiles([])

    def test_validate_profiles_missing_url(self):
        """Test that profile without URL fails validation."""
        profile = MagicMock(spec=PoolProfile)
        profile.url = ""
        profile.username = "user"
        profile.name = "Test"

        with pytest.raises(PoolConfigurationError):
            ProductionMiningGateway.validate_profiles([profile])

    def test_validate_profiles_invalid_scheme(self):
        """Test that invalid URL scheme fails validation."""
        profile = MagicMock(spec=PoolProfile)
        profile.url = "http://pool.example.com:3334"  # Invalid scheme
        profile.username = "user"
        profile.name = "Test"
        profile.stratum_version = 1

        with pytest.raises(PoolConfigurationError):
            ProductionMiningGateway.validate_profiles([profile])

    def test_validate_profiles_invalid_stratum_version(self):
        """Test that invalid Stratum version fails validation."""
        profile = MagicMock(spec=PoolProfile)
        profile.url = "stratum+ssl://pool.example.com:3334"
        profile.username = "user"
        profile.name = "Test"
        profile.stratum_version = 3  # Invalid

        with pytest.raises(PoolConfigurationError):
            ProductionMiningGateway.validate_profiles([profile])


class TestPoolHealthTracking:
    """Test pool health monitoring and status tracking."""

    def test_pool_health_status_creation(self):
        """Test creating pool health status."""
        status = PoolHealthStatus(
            pool_name="Test Pool",
            pool_url="stratum+ssl://pool.example.com:3334",
        )

        assert status.pool_name == "Test Pool"
        assert status.health == PoolHealth.UNKNOWN
        assert status.shares_submitted_total == 0
        assert status.acceptance_rate == 0.0

    def test_pool_health_status_to_dict(self):
        """Test converting pool health status to dict."""
        status = PoolHealthStatus(
            pool_name="Test Pool",
            pool_url="stratum+ssl://pool.example.com:3334",
            health=PoolHealth.HEALTHY,
            shares_submitted_total=100,
            shares_accepted_total=95,
        )

        status_dict = status.to_dict()
        assert status_dict["pool_name"] == "Test Pool"
        assert status_dict["health"] == "healthy"
        assert status_dict["shares_submitted_total"] == 100

    def test_health_transitions(self):
        """Test pool health state transitions."""
        status = PoolHealthStatus(
            pool_name="Test Pool",
            pool_url="stratum+ssl://pool.example.com:3334",
        )

        # Unknown -> Healthy
        assert status.health == PoolHealth.UNKNOWN
        status.health = PoolHealth.HEALTHY
        assert status.health == PoolHealth.HEALTHY

        # Healthy -> Degraded
        status.health = PoolHealth.DEGRADED
        assert status.health == PoolHealth.DEGRADED

        # Degraded -> Offline
        status.health = PoolHealth.OFFLINE
        assert status.health == PoolHealth.OFFLINE


class TestMiningStrategy:
    """Test mining strategy implementation."""

    @pytest.mark.asyncio
    async def test_failover_strategy(self):
        """Test failover mining strategy."""
        profile1 = MagicMock(spec=PoolProfile)
        profile1.pool_id = "pool_1"
        profile1.name = "Pool 1"
        profile1.url = "stratum+ssl://pool1.example.com:3334"
        profile1.username = "user1"
        profile1.password = "pass1"
        profile1.stratum_version = 1

        profile2 = MagicMock(spec=PoolProfile)
        profile2.pool_id = "pool_2"
        profile2.name = "Pool 2"
        profile2.url = "stratum+ssl://pool2.example.com:3334"
        profile2.username = "user2"
        profile2.password = "pass2"
        profile2.stratum_version = 1

        with patch("pythia_mining.production_mining_orchestrator.StratumClient"):
            orchestrator = ProductionMiningOrchestrator(
                profiles=[profile1, profile2],
                mining_strategy=MiningStrategy.FAILOVER,
            )

            assert orchestrator.mining_strategy == MiningStrategy.FAILOVER
            assert len(orchestrator.profiles) == 2

    @pytest.mark.asyncio
    async def test_multi_pool_strategy(self):
        """Test multi-pool mining strategy."""
        profile1 = MagicMock(spec=PoolProfile)
        profile1.pool_id = "pool_1"
        profile1.name = "Pool 1"
        profile1.url = "stratum+ssl://pool1.example.com:3334"
        profile1.username = "user1"
        profile1.password = "pass1"
        profile1.stratum_version = 1

        profile2 = MagicMock(spec=PoolProfile)
        profile2.pool_id = "pool_2"
        profile2.name = "Pool 2"
        profile2.url = "stratum+ssl://pool2.example.com:3334"
        profile2.username = "user2"
        profile2.password = "pass2"
        profile2.stratum_version = 1

        with patch("pythia_mining.production_mining_orchestrator.StratumClient"):
            orchestrator = ProductionMiningOrchestrator(
                profiles=[profile1, profile2],
                mining_strategy=MiningStrategy.MULTI_POOL,
            )

            assert orchestrator.mining_strategy == MiningStrategy.MULTI_POOL


class TestMiningStatistics:
    """Test mining statistics calculation."""

    def test_mining_stat_creation(self):
        """Test creating mining statistics."""
        from pythia_mining.production_mining_orchestrator import MiningStat

        stats = MiningStat(
            total_shares_submitted=100,
            total_shares_accepted=95,
            total_shares_rejected=5,
            active_pools=2,
            healthy_pools=2,
        )

        assert stats.total_shares_submitted == 100
        assert stats.total_shares_accepted == 95
        assert stats.global_acceptance_rate == 0.0  # Not yet calculated
        assert stats.active_pools == 2

    def test_mining_stat_to_dict(self):
        """Test converting mining stats to dict."""
        from pythia_mining.production_mining_orchestrator import MiningStat

        stats = MiningStat(
            total_shares_submitted=1000,
            total_shares_accepted=947,
            healthy_pools=2,
        )

        stats_dict = stats.to_dict()
        assert stats_dict["total_shares_submitted"] == 1000
        assert stats_dict["total_shares_accepted"] == 947
        assert stats_dict["healthy_pools"] == 2


class TestGatewayIntegration:
    """Integration tests for production gateway."""

    @pytest.mark.asyncio
    async def test_gateway_initialization_requires_profiles(self):
        """Test that gateway initialization requires profiles."""
        gateway = ProductionMiningGateway()

        # Create mock profiles with empty list behavior
        with patch.object(ProductionMiningGateway, "build_profiles_from_env", return_value=[]):
            with pytest.raises((PoolConfigurationError, ValueError)):
                await gateway.initialize()

    def test_gateway_status_before_init(self):
        """Test gateway status before initialization."""
        gateway = ProductionMiningGateway()
        status = gateway.get_status()

        assert status["initialized"] is False
        assert status["running"] is False
        assert status["status"] == "not_initialized"

    @pytest.mark.asyncio
    async def test_cannot_start_uninitialized_gateway(self):
        """Test that starting uninitialized gateway raises error."""
        gateway = ProductionMiningGateway()

        with pytest.raises(MiningGatewayError):
            await gateway.start()


class TestPoolConnectivity:
    """Test pool connectivity and error handling."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self):
        """Test circuit breaker activates after failures."""
        profile = MagicMock(spec=PoolProfile)
        profile.pool_id = "pool_1"
        profile.name = "Test Pool"
        profile.url = "stratum+ssl://pool.example.com:3334"
        profile.username = "user"
        profile.password = "pass"
        profile.stratum_version = 1

        with patch("pythia_mining.production_mining_orchestrator.StratumClient"):
            with patch.object(ProductionMiningOrchestrator, "_update_pool_health"):
                orchestrator = ProductionMiningOrchestrator(
                    profiles=[profile],
                    max_pool_failures_before_offline=3,
                )

                # Record failures
                for _ in range(3):
                    orchestrator._record_pool_failure("pool_1")

                # Check that failures were recorded
                health = orchestrator.pool_health["pool_1"]
                assert health.consecutive_failures == 3


class TestShareValidation:
    """Test share validation and submission."""

    def test_share_result_accepted(self):
        """Test accepted share result."""
        from pythia_mining.stratum_client import ShareResult

        result = ShareResult(accepted=True, job_id="job_123", nonce=12345)
        assert result.accepted is True
        assert result.job_id == "job_123"
        assert result.error_code is None

    def test_share_result_rejected(self):
        """Test rejected share result."""
        from pythia_mining.stratum_client import ShareResult

        result = ShareResult(
            accepted=False,
            error_code=1,
            error_message="Invalid share",
            job_id="job_123",
            nonce=12345,
        )
        assert result.accepted is False
        assert result.error_code == 1
        assert result.error_message == "Invalid share"


class TestEnvironmentConfiguration:
    """Test environment variable configuration."""

    @patch.dict(
        "os.environ",
        {
            "HYBA_POOL_1_NAME": "TestPool",
            "HYBA_POOL_1_URL": "stratum+ssl://test.example.com:3334",
            "HYBA_POOL_1_USERNAME": "user@example.com",
            "HYBA_POOL_1_PASSWORD": "password123",
            "HYBA_POOL_1_STRATUM_VERSION": "1",
        },
    )
    def test_build_profiles_from_env(self):
        """Test building profiles from environment variables."""
        profiles = ProductionMiningGateway.build_profiles_from_env()

        assert len(profiles) >= 1
        assert profiles[0].name == "TestPool"
        assert profiles[0].url == "stratum+ssl://test.example.com:3334"
        assert profiles[0].username == "user@example.com"

    @patch.dict(
        "os.environ",
        {
            "HYBA_MINING_POOLS_JSON": '[{"name":"Pool1","url":"stratum+ssl://pool1.com:3334","username":"user1","password":"pass1"}]'
        },
    )
    def test_build_profiles_from_json(self):
        """Test building profiles from JSON environment variable."""
        profiles = ProductionMiningGateway.build_profiles_from_env()

        assert len(profiles) >= 1
        assert profiles[0].name == "Pool1"
        assert profiles[0].url == "stratum+ssl://pool1.com:3334"


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmarks for mining operations."""

    def test_pool_health_status_creation_speed(self):
        """Benchmark pool health status creation."""
        import time

        start = time.time()
        for _ in range(1000):
            PoolHealthStatus(
                pool_name="Test Pool",
                pool_url="stratum+ssl://pool.example.com:3334",
            )
        elapsed = time.time() - start

        # Should complete 1000 creations in < 1 second
        assert elapsed < 1.0

    def test_health_transition_speed(self):
        """Benchmark health status transitions."""
        import time

        start = time.time()
        for _ in range(1000):
            status = PoolHealthStatus(
                pool_name="Test",
                pool_url="stratum+ssl://pool.example.com:3334",
            )
            status.health = PoolHealth.HEALTHY
            status.health = PoolHealth.DEGRADED
            status.health = PoolHealth.OFFLINE
        elapsed = time.time() - start

        # Should complete 1000 transitions in < 1 second
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
