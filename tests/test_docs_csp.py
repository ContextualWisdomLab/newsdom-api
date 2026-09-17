from fastapi.testclient import TestClient
from newsdom_api.main import app

def test_docs_endpoints_relax_csp():
    client = TestClient(app)

    docs_endpoints = ["/docs", "/redoc", "/openapi.json"]
    for endpoint in docs_endpoints:
        response = client.get(endpoint)
        csp = response.headers.get("Content-Security-Policy")
        expected_csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "frame-ancestors 'none'; "
            "base-uri 'none'"
        )
        assert csp == expected_csp

def test_other_endpoints_strict_csp():
    client = TestClient(app)

    response = client.get("/health")
    csp = response.headers.get("Content-Security-Policy")
    assert csp == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
