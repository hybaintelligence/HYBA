"""Integration tests for API endpoint connectivity."""
from __future__ import annotations
import pytest
import json
from pathlib import Path


class TestAPIEndpointDiscovery:
    """Verify API endpoint manifests are properly structured."""

    def test_manifest_exists(self):
        """Verify manifest.json exists and is valid JSON."""
        manifest_path = Path("config/manifest.json")
        assert manifest_path.exists(), "manifest.json not found"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert isinstance(manifest, dict)
        assert len(manifest) > 0

    def test_frontend_seed_data_valid(self):
        """Verify frontend seed data is valid JSON."""
        seed_path = Path("config/frontend_seed_data.json")
        assert seed_path.exists(), "frontend_seed_data.json not found"
        with open(seed_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestAPIEndpointStructure:
    """Verify API endpoint structure conventions."""

    def test_backend_routes_exist(self):
        """Verify backend API directory contains route files."""
        api_dir = Path("python_backend/hyba_genesis_api/api")
        assert api_dir.exists(), "API directory not found"
        py_files = list(api_dir.glob("*.py"))
        assert len(py_files) > 10, f"Expected many API files, found {len(py_files)}"

    def test_health_endpoint_exists(self):
        """Verify health endpoint module exists."""
        health_path = Path("python_backend/hyba_genesis_api/api/health.py")
        assert health_path.exists(), "Health endpoint not found"