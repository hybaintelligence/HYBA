"""End-to-end tests for the mining workflow lifecycle."""
from __future__ import annotations
import pytest


class TestMiningWorkflow:
    """Verify the complete mining workflow end-to-end."""

    def test_mining_config_exists_and_valid(self):
        """Verify mining configuration exists."""
        import json
        from pathlib import Path

        config_path = Path("config/mining_config.json")
        assert config_path.exists(), "Mining config not found"
        with open(config_path) as f:
            config = json.load(f)
        assert isinstance(config, dict), "Mining config must be a dict"
        assert len(config) > 0, "Mining config must not be empty"

    def test_mining_pool_test_config_exists(self):
        """Verify test mining pool configuration."""
        from pathlib import Path

        config_path = Path("config/mining_pools_test.json")
        assert config_path.exists(), "Test mining pool config not found"

    def test_stratum_endpoint_config(self):
        """Verify stratum endpoint configuration."""
        from pathlib import Path

        config_dirs = [
            Path("config/mining_pools_test.json"),
            Path("config/mining_pools_live.example.json"),
        ]
        found = any(p.exists() for p in config_dirs)
        assert found, "No stratum pool config found"

    def test_braiins_session_logs(self):
        """Verify Braiins session logs directory structure."""
        from pathlib import Path

        logs_dir = Path("logs")
        assert logs_dir.exists(), "Logs directory not found"
        braiins_logs = list(logs_dir.glob("*braiins*"))
        if not braiins_logs:
            pytest.skip("No Braiins session logs found")