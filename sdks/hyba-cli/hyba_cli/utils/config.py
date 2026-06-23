"""
Configuration management for HYBA CLI
"""

from pathlib import Path
from typing import Any, Optional
import yaml
import json


class ConfigManager:
    """Manages HYBA CLI configuration"""

    def __init__(self):
        self.config_dir = Path.home() / ".hyba"
        self.config_dir.mkdir(exist_ok=True)
        self.config_path = self.config_dir / "config.yaml"
        self._default_config = {
            "api_url": "https://api.hyba.ai",
            "output_format": "table",
            "verbose": False,
            "timeout": 30,
        }

    def load(self) -> dict:
        """Load configuration from file"""
        if not self.config_path.exists():
            return self._default_config.copy()

        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f) or {}
            return {**self._default_config, **config}
        except:
            return self._default_config.copy()

    def save(self, config: dict):
        """Save configuration to file"""
        with open(self.config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        config = self.load()
        return config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value"""
        config = self.load()
        config[key] = value
        self.save(config)
