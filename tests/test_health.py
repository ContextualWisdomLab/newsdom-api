from fastapi.testclient import TestClient

from newsdom_api.main import app


def test_healthcheck():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Verify security headers are injected by middleware
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )
