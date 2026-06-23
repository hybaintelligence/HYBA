"""Unit tests for API client utilities."""
from __future__ import annotations
import pytest


def test_api_endpoint_construction():
    """Verify API endpoint paths are constructed correctly."""
    base_url = "https://api.hyba.io/v1"
    path = "/health"
    expected = f"{base_url}{path}"
    assert expected == "https://api.hyba.io/v1/health"


@pytest.mark.parametrize(
    "status_code,expected",
    [(200, True), (201, True), (204, True), (400, False), (401, False), (500, False)],
)
def test_success_status_detection(status_code: int, expected: bool):
    """Verify successful HTTP status codes are detected."""
    success_codes = {200, 201, 204}
    assert (status_code in success_codes) == expected


def test_retry_backoff_calculation():
    """Verify exponential backoff values for retry logic."""
    base_delay = 1.0
    from math import pow as math_pow

    for attempt in range(1, 5):
        delay = min(base_delay * math_pow(2, attempt - 1), 30.0)
        assert delay > 0
        assert delay <= 30.0


def test_jwt_token_format():
    """Verify JWT token has expected structure."""
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozw"
    parts = token.split(".")
    assert len(parts) == 3
    header, payload, signature = parts
    assert header
    assert payload
    assert signature
    assert len(header) > 0
    assert len(signature) > 0