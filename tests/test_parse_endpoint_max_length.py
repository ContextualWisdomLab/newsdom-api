"""Regression tests for bounded `/parse` form values."""

import pytest
from fastapi.testclient import TestClient

from newsdom_api.config import AuthenticationMode, RuntimeSettings
from newsdom_api.main import _runtime_settings, app


_MINIMAL_PDF = b"%PDF-1.4\n%%EOF"
_MISSING = object()


@pytest.fixture
def no_auth_client():
    """Disable authentication without clearing unrelated dependency overrides."""
    previous = app.dependency_overrides.get(_runtime_settings, _MISSING)
    app.dependency_overrides[_runtime_settings] = lambda: RuntimeSettings(
        authentication_mode=AuthenticationMode.DISABLED
    )
    try:
        with TestClient(app) as client:
            yield client
    finally:
        if previous is _MISSING:
            app.dependency_overrides.pop(_runtime_settings, None)
        else:
            app.dependency_overrides[_runtime_settings] = previous


@pytest.mark.parametrize(
    ("bounded_field", "language", "mode"),
    (("language", "a" * 51, "auto"), ("mode", "ch", "b" * 51)),
)
def test_parse_endpoint_rejects_overlong_form_values(
    no_auth_client: TestClient,
    bounded_field: str,
    language: str,
    mode: str,
) -> None:
    """Reject each overlong field through FastAPI's declared form-value contract."""
    response = no_auth_client.post(
        "/parse",
        files={"file": ("fixture.pdf", _MINIMAL_PDF, "application/pdf")},
        data={"language": language, "mode": mode},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(
        error.get("loc") == ["body", bounded_field]
        and error.get("type") == "string_too_long"
        for error in detail
    )
