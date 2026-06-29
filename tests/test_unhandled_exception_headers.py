from fastapi.testclient import TestClient

from newsdom_api.main import app


def test_unhandled_exception_does_not_leak_stack_trace_and_has_headers(monkeypatch):
    def fake_parse_pdf_bytes(*args, **kwargs):
        raise RuntimeError("Intentional unhandled internal error for testing")

    monkeypatch.setattr("newsdom_api.main.parse_pdf_bytes", fake_parse_pdf_bytes)
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
