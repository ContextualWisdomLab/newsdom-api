from fastapi.testclient import TestClient

from newsdom_api import runtime_readiness
from newsdom_api.main import app


def test_mineru_runtime_ready_accepts_configured_executable(monkeypatch):
    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/opt/mineru/bin/mineru")
    lookups: list[str] = []

    def fake_which(command: str) -> str | None:
        lookups.append(command)
        return command

    monkeypatch.setattr(runtime_readiness.shutil, "which", fake_which)

    assert runtime_readiness.is_mineru_runtime_ready() is True
    assert lookups == ["/opt/mineru/bin/mineru"]


def test_mineru_runtime_ready_rejects_missing_configured_executable(monkeypatch):
    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/missing/mineru")
    monkeypatch.setattr(runtime_readiness.shutil, "which", lambda command: None)

    assert runtime_readiness.is_mineru_runtime_ready() is False


def test_mineru_runtime_ready_uses_default_path_lookup(monkeypatch):
    monkeypatch.delenv("NEWSDOM_MINERU_BIN", raising=False)
    lookups: list[str] = []

    def fake_which(command: str) -> str | None:
        lookups.append(command)
        return "/usr/bin/mineru"

    monkeypatch.setattr(runtime_readiness.shutil, "which", fake_which)

    assert runtime_readiness.is_mineru_runtime_ready() is True
    assert lookups == ["mineru"]


def test_ready_returns_parser_readiness_without_authentication(monkeypatch):
    monkeypatch.setenv("NEWSDOM_API_TOKEN", "configured-secret")
    monkeypatch.setattr(runtime_readiness, "is_mineru_runtime_ready", lambda: True)
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"


def test_ready_returns_sanitized_503_when_mineru_is_unavailable(monkeypatch):
    monkeypatch.setattr(runtime_readiness, "is_mineru_runtime_ready", lambda: False)
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"
