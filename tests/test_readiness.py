from fastapi.testclient import TestClient

from newsdom_api import mineru_runner
from newsdom_api.main import app


def test_mineru_runtime_ready_accepts_configured_executable(monkeypatch):
    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/opt/mineru/bin/mineru")
    lookups: list[str] = []

    def fake_which(command: str) -> str | None:
        lookups.append(command)
        return command

    monkeypatch.setattr(mineru_runner.shutil, "which", fake_which)

    assert mineru_runner.is_mineru_runtime_ready() is True
    assert lookups == ["/opt/mineru/bin/mineru"]


def test_mineru_runtime_ready_rejects_missing_configured_executable(monkeypatch):
    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/missing/mineru")
    monkeypatch.setattr(mineru_runner.shutil, "which", lambda command: None)

    assert mineru_runner.is_mineru_runtime_ready() is False


def test_mineru_runtime_ready_caches_default_path_lookup(monkeypatch):
    monkeypatch.delenv("NEWSDOM_MINERU_BIN", raising=False)
    mineru_runner._cached_which.cache_clear()
    lookups: list[str] = []

    def fake_which(command: str) -> str | None:
        lookups.append(command)
        return "/usr/bin/mineru"

    monkeypatch.setattr(mineru_runner.shutil, "which", fake_which)

    try:
        assert mineru_runner.is_mineru_runtime_ready() is True
        assert mineru_runner.is_mineru_runtime_ready() is True
        assert lookups == ["mineru"]
    finally:
        mineru_runner._cached_which.cache_clear()


def test_mineru_runtime_ready_reports_missing_default_executable(monkeypatch):
    monkeypatch.delenv("NEWSDOM_MINERU_BIN", raising=False)
    mineru_runner._cached_which.cache_clear()
    monkeypatch.setattr(mineru_runner.shutil, "which", lambda command: None)

    try:
        assert mineru_runner.is_mineru_runtime_ready() is False
    finally:
        mineru_runner._cached_which.cache_clear()


def test_ready_returns_parser_readiness_without_authentication(monkeypatch):
    monkeypatch.setenv("NEWSDOM_API_TOKEN", "configured-secret")
    monkeypatch.setattr("newsdom_api.main.is_mineru_runtime_ready", lambda: True)
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "parser": "mineru"}
    assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"


def test_ready_returns_sanitized_503_when_mineru_is_unavailable(monkeypatch):
    monkeypatch.setattr("newsdom_api.main.is_mineru_runtime_ready", lambda: False)
    client = TestClient(app, base_url="https://testserver")

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Service Unavailable"}
    assert response.headers["Cache-Control"] == "no-store, no-cache, max-age=0"
