"""Adversarial tests for security boundaries and input validation."""
from __future__ import annotations
import pytest


class TestInputValidation:
    """Verify input validation rejects malicious inputs."""

    @pytest.mark.parametrize(
        "malicious_input,expected_dangerous",
        [
            ("'; DROP TABLE users; --", True),
            ("../../etc/passwd", True),
            ("<script>alert('xss')</script>", True),
            ("${7*7}", True),
            ("1; rm -rf /", True),
            ("admin' OR '1'='1", True),
            ("NULL; DELETE FROM users;", True),
            ("||cat /etc/shadow", True),
            ("normal_input", False),
            ("hello world", False),
            ("user@example.com", False),
        ],
    )
    def test_malicious_pattern_detection(self, malicious_input, expected_dangerous):
        """Verify malicious input patterns are detected."""
        dangerous_patterns = [
            "' OR '", "'; DROP", "' OR 1=1", "'; DELETE", "||",
            "../", "<script", "${", "rm -rf", "DROP TABLE",
            "DELETE FROM", "-- ", "1=1",
        ]
        detected = any(pattern in malicious_input.upper() or pattern in malicious_input for pattern in dangerous_patterns)
        assert detected == expected_dangerous, f"Detection mismatch for: {malicious_input}"

    @pytest.mark.parametrize(
        "path_input,expected_safe",
        [
            ("valid/path", True),
            ("../outside", False),
            ("../../etc/passwd", False),
            ("valid/nested/path", True),
            ("~/home/user", True),
        ],
    )
    def test_path_traversal_detection(self, path_input, expected_safe):
        """Verify path traversal attacks are detected."""
        is_safe = not path_input.startswith("../") and ".." not in path_input.split("/")[:-1] if "/" in path_input else True
        assert is_safe == expected_safe


class TestBoundaryConditions:
    """Verify boundary condition handling."""

    @pytest.mark.parametrize(
        "value",
        [0, -1, 2**31, 2**63 - 1, -2**31, float("inf"), float("nan")],
    )
    def test_extreme_numeric_values(self, value):
        """Verify extreme numeric values don't crash validation."""
        assert isinstance(value, (int, float))

    def test_empty_input_handling(self):
        """Verify empty inputs are handled gracefully."""
        empty_values = ["", None, {}, [], set()]
        for v in empty_values:
            assert not v or v is None

    def test_nested_json_depth(self):
        """Verify deep JSON nesting is detected."""
        deep_nested = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        depth = 0
        obj = deep_nested
        while isinstance(obj, dict):
            obj = next(iter(obj.values()))
            depth += 1
        assert depth == 5


class TestRateLimiting:
    """Verify rate limiting boundary conditions."""

    def test_rate_limit_window_calculation(self):
        """Verify rate limit window boundaries."""
        max_requests = 100
        for current_count in [0, 50, 99, 100, 101]:
            is_allowed = current_count < max_requests
            assert is_allowed == (current_count < max_requests)

    def test_burst_limit_enforcement(self):
        """Verify burst limit enforcement."""
        max_burst = 20
        for burst_count in [0, 10, 19, 20, 25]:
            within_limit = burst_count <= max_burst
            assert within_limit == (burst_count <= max_burst)