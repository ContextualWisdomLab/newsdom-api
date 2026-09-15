from fastapi.testclient import TestClient
from newsdom_api.main import app

def test_docs_endpoints_relax_csp():
    client = TestClient(app)

    docs_endpoints = ["/docs", "/redoc", "/openapi.json"]
    for endpoint in docs_endpoints:
        response = client.get(endpoint)
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "https://cdn.jsdelivr.net" in csp

def test_other_endpoints_strict_csp():
    client = TestClient(app)

    response = client.get("/health")
    csp = response.headers.get("Content-Security-Policy")
    assert csp == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
