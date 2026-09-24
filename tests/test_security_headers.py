import pytest
from fastapi.testclient import TestClient
from newsdom_api.main import app

client = TestClient(app)

def test_csp_docs_endpoints():
    for endpoint in ("/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"):
        response = client.get(endpoint)
        csp = response.headers.get("Content-Security-Policy", "")
        expected_csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; "
            "img-src 'self' data: fastapitiangolo.tiangolo.com; "
            "font-src 'self' fonts.gstatic.com; "
            "frame-ancestors 'none'; "
            "base-uri 'none'"
        )
        assert csp == expected_csp

def test_csp_api_endpoints():
    response = client.get("/health")
    csp = response.headers.get("Content-Security-Policy", "")
    assert csp == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
