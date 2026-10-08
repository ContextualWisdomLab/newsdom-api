from fastapi.testclient import TestClient
from newsdom_api.main import app

def test_language_form_field_length_limit():
    client = TestClient(app)
    # create dummy PDF content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF\n"
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer dev_token"},
        data={"language": "a" * 51, "mode": "auto"},
        files={"file": ("dummy.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 422
    assert "string_too_long" in response.text

def test_mode_form_field_length_limit():
    client = TestClient(app)
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF\n"
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer dev_token"},
        data={"language": "en", "mode": "a" * 51},
        files={"file": ("dummy.pdf", pdf_content, "application/pdf")}
    )
    assert response.status_code == 422
    assert "string_too_long" in response.text
