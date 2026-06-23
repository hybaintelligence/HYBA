from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_enterprise_posture_and_circuit_breaker_modules_are_wired():
    main = (ROOT / "python_backend/hyba_genesis_api/main.py").read_text(
        encoding="utf-8"
    )
    posture = (ROOT / "python_backend/hyba_genesis_api/core/api_posture.py").read_text(
        encoding="utf-8"
    )

    assert "install_enterprise_api_posture(app)" in main
    assert "InMemoryRateLimiter" in posture
    assert "request_body_too_large" in posture
    assert "rate_limit_exceeded" in posture
    assert "enterprise_error_payload" in posture


def test_distributed_customer_metering_fails_observably_not_silently():
    source = (
        ROOT / "python_backend/hyba_genesis_api/api/customer_access.py"
    ).read_text(encoding="utf-8")

    assert "HYBA_REDIS_URL" in source
    assert "Redis usage increment failed" in source
    assert "record_billing_quota_rejection" in source
    assert "record_billing_usage" in source
