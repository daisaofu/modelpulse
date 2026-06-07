from fastapi.testclient import TestClient

from modelpulse.main import app


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "modelpulse"}


def test_error_explanations_endpoint():
    client = TestClient(app)

    response = client.get("/api/error-explanations")

    assert response.status_code == 200
    assert response.json()["504"] == "网关等上游超时"
