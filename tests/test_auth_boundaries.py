from fastapi.testclient import TestClient

from hyba_genesis_api.main import app


def test_customer_surfaces_require_api_key():
    client = TestClient(app)
    endpoints = [
        ("GET", "/api/v1/fault-tolerant-computers"),
        ("GET", "/api/v1/computational-intelligence-services"),
        ("GET", "/api/qiaas/health"),
        ("GET", "/api/quantum-finance/capability-map"),
    ]
    for method, path in endpoints:
        response = client.request(method, path)
        assert response.status_code in (401, 422)


def test_admin_endpoint_rejects_missing_jwt():
    response = TestClient(app).get("/api/admin/users")
    assert response.status_code == 401


def test_customer_key_cannot_reach_admin_endpoint():
    response = TestClient(app).get(
        "/api/admin/users", headers={"X-API-Key": "hyba_live_not_admin"}
    )
    assert response.status_code in (401, 403)
