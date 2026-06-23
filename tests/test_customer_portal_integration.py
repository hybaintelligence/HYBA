"""
Customer Portal Integration Tests
Verify customer API endpoints work correctly.
"""

import pytest
import sys
from pathlib import Path

# Add python_backend to path
backend_path = Path(__file__).parent.parent / "python_backend"
sys.path.insert(0, str(backend_path))

from hyba_genesis_api.api.customer_portal import (
    generate_api_key,
    get_customer_tier,
    calculate_usage,
)


def test_api_key_generation():
    """Test API key generation produces valid format."""
    api_key, hashed_key = generate_api_key()

    # Verify format
    assert api_key.startswith("hyba_")
    assert len(api_key) > 40

    # Verify hash is SHA256 (64 hex characters)
    assert len(hashed_key) == 64
    assert all(c in "0123456789abcdef" for c in hashed_key)

    # Verify keys are different each time
    api_key2, hashed_key2 = generate_api_key()
    assert api_key != api_key2
    assert hashed_key != hashed_key2


def test_customer_tier_structure():
    """Test customer tier info has required fields."""
    tier_info = get_customer_tier("test_customer_id")

    assert "tier" in tier_info
    assert "compute_units_quota" in tier_info
    assert "cost_per_unit" in tier_info
    assert "currency" in tier_info

    assert tier_info["tier"] in ["developer", "production", "sovereign"]
    assert tier_info["compute_units_quota"] > 0
    assert tier_info["cost_per_unit"] > 0
    assert tier_info["currency"] == "USD"


def test_usage_calculation():
    """Test usage calculation returns breakdown."""
    from datetime import datetime

    period_start = datetime(2026, 6, 1)
    period_end = datetime(2026, 6, 30)

    usage = calculate_usage("test_customer", period_start, period_end)

    # Verify breakdown structure
    assert "qaas" in usage
    assert "qiaas" in usage
    assert "ciaas" in usage
    assert "quantum_finance" in usage

    # Verify all are non-negative integers
    for service, units in usage.items():
        assert isinstance(units, int)
        assert units >= 0


def test_database_schema():
    """Test database schema initializes correctly."""
    from hyba_genesis_api.database import initialize_database, get_db_connection

    # Initialize
    initialize_database()

    # Verify tables exist
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    assert "api_keys" in tables
    assert "usage_logs" in tables
    assert "quota_alerts" in tables
    assert "customer_subscriptions" in tables

    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
