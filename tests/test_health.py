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
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert response.headers.get("Cache-Control") == "no-store, no-cache, max-age=0"
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )


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
        "url": "https://github.com/Seongho-Bae/newsdom-api",
    }
    assert info["license"] == {
        "name": "MIT License",
        "identifier": "MIT",
    }


def test_openapi_schema_contains_dx_examples():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["paths"]["/parse"]["post"]["requestBody"]["required"] is True
    assert schema["components"]["schemas"]["CaptionNode"]["properties"]["text"]["example"] == "Figure 1: Architectural diagram."
    assert schema["components"]["schemas"]["PageNode"]["properties"]["ads"]["example"] == ["Promotional content block"]
    assert schema["components"]["schemas"]["PageNode"]["properties"]["headers"]["example"] == ["Annual Report - 2023"]
