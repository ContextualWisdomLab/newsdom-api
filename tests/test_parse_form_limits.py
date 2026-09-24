"""Executable contracts for bounded `/parse` form values."""

import pytest
from fastapi.testclient import TestClient

from newsdom_api.main import app


@pytest.mark.parametrize(
    ("field", "limit"),
    (("language", 50), ("mode", 20)),
)
def test_parse_accepts_form_value_at_declared_limit(field: str, limit: int) -> None:
    """A value at the declared boundary reaches endpoint PDF validation."""
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"not a pdf", "application/pdf")},
        data={field: "a" * limit},
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


@pytest.mark.parametrize(
    ("field", "limit"),
    (("language", 50), ("mode", 20)),
)
def test_parse_rejects_form_value_above_declared_limit(field: str, limit: int) -> None:
    """A value one character above the boundary is rejected before the handler."""
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"not a pdf", "application/pdf")},
        data={field: "a" * (limit + 1)},
    )

    assert response.status_code == 422
    assert any(
        error.get("loc") == ["body", field]
        and error.get("type") == "string_too_long"
        for error in response.json()["detail"]
    )
