from fastapi.testclient import TestClient
from src.newsdom_api.main import app


def test_auth_non_ascii(monkeypatch):
    monkeypatch.setenv("NEWSDOM_API_TOKEN", "secret")
    client = TestClient(app)
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer 안녕하세요".encode("utf-8")},
        files={"file": ("test.pdf", b"%PDF-test", "application/pdf")},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"
