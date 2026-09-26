import pytest
from fastapi.testclient import TestClient
from newsdom_api.main import app

def test_parse_large_form_field_language(monkeypatch):
    client = TestClient(app)

    # Bypass auth for this test
    monkeypatch.setenv("NEWSDOM_AUTH_MODE", "disabled")
    monkeypatch.setenv("NEWSDOM_RUNTIME_PROFILE", "development")
    from newsdom_api.config import load_runtime_settings
    app.state.runtime_settings = load_runtime_settings()

    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
        data={"language": "a" * 51, "mode": "auto"}
    )

    assert response.status_code == 422
    assert "string_too_long" in response.text

def test_parse_large_form_field_mode(monkeypatch):
    client = TestClient(app)

    # Bypass auth for this test
    monkeypatch.setenv("NEWSDOM_AUTH_MODE", "disabled")
    monkeypatch.setenv("NEWSDOM_RUNTIME_PROFILE", "development")
    from newsdom_api.config import load_runtime_settings
    app.state.runtime_settings = load_runtime_settings()

    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
        data={"language": "ch", "mode": "a" * 51}
    )

    assert response.status_code == 422
    assert "string_too_long" in response.text
