"""Regression tests for the /parse text-form validation boundary."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeSettings
from newsdom_api.main import _runtime_settings, app

_MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [ 3 0 R ] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [ 0 0 612 792 ] >>\nendobj\n"
    b"trailer\n<< /Root 1 0 R >>\n%%EOF"
)


@pytest.fixture
def no_auth_client():
    """Return a development client with route authentication disabled."""
    app.dependency_overrides[_runtime_settings] = lambda: RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED
    )
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "form_data",
    [
        {"language": "a" * 51, "mode": "auto"},
        {"language": "ch", "mode": "b" * 51},
    ],
    ids=["language", "mode"],
)
def test_parse_rejects_text_form_values_longer_than_fifty_characters(
    tmp_path: Path, no_auth_client: TestClient, form_data: dict[str, str]
) -> None:
    """Reject overlong text values with the API's sanitized validation response."""
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(_MINIMAL_PDF)

    with pdf_path.open("rb") as pdf_file:
        response = no_auth_client.post(
            "/parse",
            files={"file": ("test.pdf", pdf_file, "application/pdf")},
            data=form_data,
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid parse parameters"}
