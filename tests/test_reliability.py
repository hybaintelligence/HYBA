from fastapi import FastAPI
from fastapi.testclient import TestClient

from hyba_genesis_api.core.reliability import (
    BackendDependencyError,
    execute_with_circuit_breaker,
)


def test_circuit_breaker_dependency_failure_returns_503_with_retry_after():
    app = FastAPI()

    @app.get("/dependency")
    async def dependency_route():
        async def failing_operation():
            raise BackendDependencyError("redis unavailable")

        return await execute_with_circuit_breaker(
            "redis",
            failing_operation,
            retry_after_seconds=15,
        )

    response = TestClient(app).get("/dependency")

    assert response.status_code == 503
    assert response.headers["retry-after"] == "15"
    assert response.json()["detail"]["status"] == "degraded"
