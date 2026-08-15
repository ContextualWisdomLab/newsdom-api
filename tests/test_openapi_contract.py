"""Acceptance tests for the customer-visible OpenAPI request contract."""

from __future__ import annotations

from typing import Any

from newsdom_api.config import RuntimeSettings
from newsdom_api.main import create_app


def _resolve_local_reference(document: dict[str, Any], reference: str) -> dict[str, Any]:
    """Resolve one JSON Pointer reference rooted in the supplied OpenAPI document."""

    assert reference.startswith("#/"), "OpenAPI request schema must use a local ref"
    current: Any = document
    for raw_token in reference[2:].split("/"):
        token = raw_token.replace("~1", "/").replace("~0", "~")
        current = current[token]
    assert isinstance(current, dict)
    return current


def test_parse_multipart_schema_guides_callers_to_a_valid_request() -> None:
    """Swagger consumers should see the required PDF and usable form examples."""

    application = create_app(
        RuntimeSettings(api_token="openapi-contract-token"),
        runtime_readiness_probe=lambda: True,
    )

    document = application.openapi()
    request_body = document["paths"]["/parse"]["post"]["requestBody"]
    multipart_schema = request_body["content"]["multipart/form-data"]["schema"]
    body_schema = _resolve_local_reference(document, multipart_schema["$ref"])
    properties = body_schema["properties"]

    assert request_body["required"] is True
    assert set(body_schema["required"]) == {"file"}
    assert properties["file"]["type"] == "string"
    assert properties["file"].get("format", "binary") == "binary" # FastAPI > 0.100 might use contentMediaType instead
    assert properties["language"]["default"] == "ch"
    assert properties["language"]["example"] == "ch"
    assert properties["mode"]["default"] == "auto"
    assert properties["mode"]["example"] == "auto"
