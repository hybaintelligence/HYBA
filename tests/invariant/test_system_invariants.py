"""Invariant tests for system-level properties that must always hold."""
from __future__ import annotations
import pytest
import json
from pathlib import Path


class TestDatabaseInvariants:
    """Verify database schema invariants."""

    def test_migrations_exist(self):
        """Verify database migration files exist."""
        migrations_dir = Path("python_backend/migrations/versions")
        assert migrations_dir.exists(), "Migrations directory not found"
        migration_files = list(migrations_dir.glob("*.py"))
        assert len(migration_files) > 0, "No migration files found"

    def test_model_files_exist(self):
        """Verify database model files exist."""
        models_dir = Path("python_backend/hyba_genesis_api/models")
        assert models_dir.exists(), "Models directory not found"
        model_files = list(models_dir.glob("*.py"))
        assert len(model_files) > 0, "No model files found"


class TestDeploymentInvariants:
    """Verify deployment configuration invariants."""

    def test_dockerfile_exists(self):
        """Verify Dockerfile exists."""
        assert Path("Dockerfile").exists(), "Dockerfile not found"
        assert Path("Dockerfile.prod").exists(), "Dockerfile.prod not found"

    def test_docker_compose_exists(self):
        """Verify docker-compose configuration exists."""
        assert Path("docker-compose.yml").exists(), "docker-compose.yml not found"

    def test_kubernetes_config_exists(self):
        """Verify K8s configuration files exist."""
        k8s_dir = Path("k8s")
        assert k8s_dir.exists(), "K8s directory not found"
        k8s_files = list(k8s_dir.glob("*.yaml"))
        assert len(k8s_files) > 0, "No K8s config files found"

    def test_terraform_config_exists(self):
        """Verify Terraform configuration exists."""
        tf_dir = Path("terraform")
        assert tf_dir.exists(), "Terraform directory not found"


class TestSecurityInvariants:
    """Verify security-related invariants."""

    def test_gitignore_exists(self):
        """Verify .gitignore exists and covers sensitive files."""
        assert Path(".gitignore").exists(), ".gitignore not found"
        with open(".gitignore") as f:
            content = f.read()
        assert ".env" in content, ".env not in gitignore"
        assert "node_modules" in content, "node_modules not in gitignore"

    def test_secret_hygiene(self):
        """Verify no hardcoded secrets in config files.
        
        Note: passwordHash (camelCase) is a legitimate schema field name.
        Test configs like mining_pools_test.json use 'password': 'test' as placeholder.
        We only flag non-test configs with actual plaintext passwords.
        """
        import re
        config_dir = Path("config")
        for config_file in config_dir.glob("*.json"):
            # Skip test configs and example templates that use placeholder values
            if "_test" in config_file.stem or "_test.json" in config_file.name or ".example" in config_file.name:
                continue
            with open(config_file) as f:
                content = f.read()
            # Check for actual hardcoded password values (not schema field names)
            hardcoded_password = re.search(r'"password"\s*:\s*"[^"]{3,}"', content, re.IGNORECASE)
            if hardcoded_password:
                # Allow passwordHash as schema field, flag actual password values
                val = hardcoded_password.group()
                if "hash" not in val.lower():
                    pytest.fail(f"Possible hardcoded password in {config_file}: {val}")


class TestDocumentationInvariants:
    """Verify documentation files exist."""

    def test_readme_exists(self):
        """Verify README exists."""
        assert Path("README.md").exists(), "README.md not found"

    def test_license_exists(self):
        """Verify LICENSE exists."""
        assert Path("LICENSE").exists(), "LICENSE not found"