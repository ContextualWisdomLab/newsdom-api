from fastapi.testclient import TestClient

from newsdom_api.main import app


def test_healthcheck():
    client = TestClient(app, base_url="https://testserver")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Verify security headers are injected by middleware
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert (
        response.headers.get("Content-Security-Policy")
        == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )


def test_docs_endpoints_have_relaxed_csp():
    client = TestClient(app)

    for endpoint in ["/docs", "/redoc", "/openapi.json"]:
        response = client.get(endpoint)
        assert response.status_code == 200
        csp = response.headers.get("Content-Security-Policy")
        expected_csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "img-src 'self' data: fastapi.tiangolo.com; "
            "font-src 'self' fonts.gstatic.com; "
            "frame-ancestors 'none'; "
            "base-uri 'none'"
        )
        assert csp == expected_csp


def test_healthcheck_omits_hsts_for_plain_http():
    client = TestClient(app, base_url="http://testserver")
    response = client.get("/health")

    assert response.status_code == 200
    assert "Strict-Transport-Security" not in response.headers


def test_healthcheck_emits_hsts_for_forwarded_https():
    client = TestClient(app, base_url="http://testserver")
    response = client.get("/health", headers={"X-Forwarded-Proto": "https"})

    assert response.status_code == 200
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )


def test_openapi_metadata_includes_contact_and_license():
    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    info = response.json()["info"]
    assert info["contact"] == {
        "name": "Seongho Bae",
        "url": "https://github.com/ContextualWisdomLab/newsdom-api",
    }
    assert info["license"] == {
        "name": "MIT License",
        "identifier": "MIT",
    }
