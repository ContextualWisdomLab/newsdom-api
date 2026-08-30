import pytest
from fastapi.testclient import TestClient
from newsdom_api.main import app, _runtime_settings
from newsdom_api.config import RuntimeSettings, AuthenticationMode

def test_parse_form_field_max_length_rejection():
    """Verify that oversized form fields are rejected with 422 to prevent DoS."""

    def override_settings():
        return RuntimeSettings(authentication_mode=AuthenticationMode.DISABLED)

    app.dependency_overrides[_runtime_settings] = override_settings

    try:
        client = TestClient(app)

        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

        oversized_string = "a" * 51
        response = client.post(
            "/parse",
            files={"file": ("test.pdf", pdf_content, "application/pdf")},
            data={"language": oversized_string, "mode": "auto"},
        )

        assert response.status_code == 422
        assert "detail" in response.json()
    finally:
        app.dependency_overrides.clear()
