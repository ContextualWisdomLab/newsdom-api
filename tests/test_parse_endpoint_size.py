import pytest
from fastapi.testclient import TestClient
from newsdom_api.main import app

def test_parse_endpoint_rejects_large_payloads():
    client = TestClient(app)

    # 20 MB payload
    large_pdf = b"%PDF-" + b"A" * (20 * 1024 * 1024)
    response = client.post(
        "/parse",
        files={"file": ("large.pdf", large_pdf, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Payload Too Large: exceeds 15MB limit"
