from fastapi import HTTPException
from fastapi.testclient import TestClient

from newsdom_api.main import app, create_app


SECURITY_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


def _assert_error_security_headers(response, *, expect_hsts: bool) -> None:
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Content-Security-Policy"] == SECURITY_CSP
    if expect_hsts:
        assert (
            response.headers["Strict-Transport-Security"]
            == "max-age=31536000; includeSubDomains"
        )
    else:
        assert "Strict-Transport-Security" not in response.headers


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


def test_routing_http_exceptions_preserve_security_headers() -> None:
    for scheme, expect_hsts in (("http", False), ("https", True)):
        client = TestClient(app, base_url=f"{scheme}://testserver")

        not_found = client.get("/missing")
        assert not_found.status_code == 404
        assert not_found.json() == {"detail": "Not Found"}
        _assert_error_security_headers(not_found, expect_hsts=expect_hsts)

        method_not_allowed = client.post("/health")
        assert method_not_allowed.status_code == 405
        assert method_not_allowed.json() == {"detail": "Method Not Allowed"}
        assert method_not_allowed.headers["allow"] == "GET"
        _assert_error_security_headers(method_not_allowed, expect_hsts=expect_hsts)


def test_application_http_exception_preserves_headers() -> None:
    application = create_app()

    def raise_teapot() -> None:
        raise HTTPException(
            status_code=418,
            detail="No tea available",
            headers={"X-Application-Error": "teapot"},
        )

    application.add_api_route("/application-error", raise_teapot, methods=["GET"])

    for scheme, expect_hsts in (("http", False), ("https", True)):
        client = TestClient(application, base_url=f"{scheme}://testserver")
        response = client.get("/application-error")

        assert response.status_code == 418
        assert response.json() == {"detail": "No tea available"}
        assert response.headers["X-Application-Error"] == "teapot"
        _assert_error_security_headers(response, expect_hsts=expect_hsts)


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
