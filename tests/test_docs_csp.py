"""Executable security contracts for the API documentation surface."""

from __future__ import annotations

import re

from fastapi.testclient import TestClient

from newsdom_api.main import STRICT_CSP, app


def _script_nonce(response_text: str, csp: str) -> str:
    match = re.search(r"(?:^|;\s*)script-src 'nonce-([^']+)'(?:\s|;)", csp)
    assert match is not None, csp
    nonce = match.group(1)
    script_tags = re.findall(r"<script(?:\s+[^>]*)?>", response_text)
    assert script_tags
    assert all(f'nonce="{nonce}"' in tag for tag in script_tags)
    return nonce


def test_swagger_scripts_require_response_nonce() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    first = client.get("/docs")
    second = client.get("/docs")

    assert first.status_code == 200
    assert second.status_code == 200
    first_csp = first.headers["Content-Security-Policy"]
    second_csp = second.headers["Content-Security-Policy"]
    first_nonce = _script_nonce(first.text, first_csp)
    second_nonce = _script_nonce(second.text, second_csp)
    assert first_nonce != second_nonce
    script_directive = next(
        part.strip() for part in first_csp.split(";") if part.strip().startswith("script-src")
    )
    assert "'unsafe-inline'" not in script_directive


def test_redoc_scripts_require_nonce_without_google_fonts() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/redoc")

    assert response.status_code == 200
    csp = response.headers["Content-Security-Policy"]
    _script_nonce(response.text, csp)
    script_directive = next(
        part.strip() for part in csp.split(";") if part.strip().startswith("script-src")
    )
    assert "'unsafe-inline'" not in script_directive
    assert "fonts.googleapis.com" not in response.text
    assert "fonts.gstatic.com" not in csp


def test_non_html_documentation_endpoints_keep_strict_csp() -> None:
    client = TestClient(app, raise_server_exceptions=False)

    openapi = client.get("/openapi.json")
    oauth_redirect = client.get("/docs/oauth2-redirect")

    assert openapi.status_code == 200
    assert openapi.headers["Content-Security-Policy"] == STRICT_CSP
    assert oauth_redirect.status_code == 404
    assert oauth_redirect.headers["Content-Security-Policy"] == STRICT_CSP
