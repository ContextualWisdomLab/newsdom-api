from fastapi.testclient import TestClient
from newsdom_api.main import app
from newsdom_api.config import RuntimeSettings, AuthenticationMode
from pathlib import Path
import pytest

from newsdom_api.main import _runtime_settings

@pytest.fixture
def no_auth_client():
    app.dependency_overrides[_runtime_settings] = lambda: RuntimeSettings(authentication_mode=AuthenticationMode.DISABLED)
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_parse_endpoint_max_length_language(tmp_path: Path, no_auth_client):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [ 3 0 R ] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [ 0 0 612 792 ] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
    with open(pdf_path, "rb") as f:
        response = no_auth_client.post(
            "/parse",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"language": "a" * 51, "mode": "auto"}
        )
    assert response.status_code == 422
    assert "Invalid parse parameters" in response.json()["detail"] or "String should have at most 50 characters" in str(response.json())

def test_parse_endpoint_max_length_mode(tmp_path: Path, no_auth_client):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [ 3 0 R ] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [ 0 0 612 792 ] >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF")
    with open(pdf_path, "rb") as f:
        response = no_auth_client.post(
            "/parse",
            files={"file": ("test.pdf", f, "application/pdf")},
            data={"language": "ch", "mode": "b" * 51}
        )
    assert response.status_code == 422
    assert "Invalid parse parameters" in response.json()["detail"] or "String should have at most 50 characters" in str(response.json())
