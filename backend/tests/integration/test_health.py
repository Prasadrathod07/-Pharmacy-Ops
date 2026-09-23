from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok_with_database_connected():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "connected"


def test_health_endpoint_includes_request_id_header():
    response = client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers
