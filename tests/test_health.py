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
        "url": "https://github.com/ContextualWisdomLab/newsdom-api",
    }
    assert info["license"] == {
        "name": "MIT License",
        "identifier": "MIT",
    }


def test_parse_openapi_form_fields_publish_standard_examples():
    """The multipart request schema must expose current JSON Schema examples."""

    client = TestClient(app)
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    request_schema = document["paths"]["/parse"]["post"]["requestBody"]["content"][
        "multipart/form-data"
    ]["schema"]
    schema_reference = request_schema["$ref"]
    assert schema_reference.startswith("#/components/schemas/")

    schema_name = schema_reference.rsplit("/", 1)[-1]
    properties = document["components"]["schemas"][schema_name]["properties"]

    assert properties["language"]["examples"] == ["ch"]
    assert properties["mode"]["examples"] == ["auto"]
    assert "example" not in properties["language"]
    assert "example" not in properties["mode"]
