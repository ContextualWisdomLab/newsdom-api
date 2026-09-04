import pytest
from fastapi.testclient import TestClient
from newsdom_api.main import app
from newsdom_api.config import RuntimeSettings, AuthenticationMode, RuntimeProfile
import io

@pytest.fixture
def override_settings(monkeypatch):
    app.dependency_overrides[RuntimeSettings] = lambda: RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED,
        runtime_profile=RuntimeProfile.DEVELOPMENT
    )
    monkeypatch.setattr("newsdom_api.main._parse_access_failure", lambda request: None)
    yield
    app.dependency_overrides.clear()

def test_parse_endpoint_rejects_long_form_fields(override_settings):
    client = TestClient(app)

    file_content = b"%PDF-1.4\n%testpdf"
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {
        "language": "a" * 51,
        "mode": "auto"
    }

    response = client.post("/parse", files=files, data=data)

    assert response.status_code == 422
    assert "detail" in response.json()

    data_mode_too_long = {
        "language": "ch",
        "mode": "a" * 51
    }

    response_mode = client.post("/parse", files=files, data=data_mode_too_long)
    assert response_mode.status_code == 422
    assert "detail" in response_mode.json()
