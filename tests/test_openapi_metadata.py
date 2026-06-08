"""Tests for OpenAPI metadata introduced in the PR.

Covers: FastAPI app-level metadata (title, description, version),
/health endpoint summary/description, /parse endpoint summary/description,
documented error responses, and the file parameter description.
"""

from fastapi.testclient import TestClient

from newsdom_api.main import app

_client = TestClient(app)


def _openapi() -> dict:
    response = _client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


# ---------------------------------------------------------------------------
# App-level metadata
# ---------------------------------------------------------------------------


def test_openapi_title():
    schema = _openapi()
    assert schema["info"]["title"] == "NewsDOM API"


def test_openapi_description():
    schema = _openapi()
    description = schema["info"]["description"]
    assert "Japanese newspaper" in description
    assert "MinerU" in description
    assert "DOM" in description


def test_openapi_version():
    schema = _openapi()
    assert schema["info"]["version"] == "0.2.0"


# ---------------------------------------------------------------------------
# /health endpoint metadata
# ---------------------------------------------------------------------------


def test_health_summary():
    schema = _openapi()
    health_op = schema["paths"]["/health"]["get"]
    assert health_op["summary"] == "Liveness check"


def test_health_description():
    schema = _openapi()
    health_op = schema["paths"]["/health"]["get"]
    assert "load balancer" in health_op["description"].lower() or "health check" in health_op["description"].lower()


# ---------------------------------------------------------------------------
# /parse endpoint metadata
# ---------------------------------------------------------------------------


def test_parse_summary():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    assert parse_op["summary"] == "Parse PDF document"


def test_parse_description():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    assert "Japanese newspaper" in parse_op["description"]
    assert "DOM" in parse_op["description"]


def test_parse_502_response_documented():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    assert "502" in parse_op["responses"]
    description_502 = parse_op["responses"]["502"]["description"]
    assert "incomplete" in description_502.lower() or "MinerU" in description_502


def test_parse_503_response_documented():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    assert "503" in parse_op["responses"]
    description_503 = parse_op["responses"]["503"]["description"]
    assert "unavailable" in description_503.lower() or "MinerU" in description_503


def test_parse_200_response_has_example():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    response_200 = parse_op["responses"]["200"]
    assert "content" in response_200
    example = response_200["content"]["application/json"]["example"]
    assert example["document_id"] == "upload"
    assert "pages" in example
    assert "quality" in example


def test_parse_200_response_description():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    assert "Successfully parsed" in parse_op["responses"]["200"]["description"]


# ---------------------------------------------------------------------------
# File parameter description
# ---------------------------------------------------------------------------


def test_parse_file_parameter_has_description():
    schema = _openapi()
    parse_op = schema["paths"]["/parse"]["post"]
    # The file description is surfaced in the request body schema
    request_body = parse_op["requestBody"]
    content_schema = request_body["content"]["multipart/form-data"]["schema"]
    # Resolve the $ref if present
    if "$ref" in content_schema:
        ref_path = content_schema["$ref"].lstrip("#/").split("/")
        node = schema
        for part in ref_path:
            node = node[part]
        content_schema = node
    file_prop = content_schema["properties"]["file"]
    # FastAPI may inline or reference; handle both
    if "$ref" in file_prop:
        ref_path = file_prop["$ref"].lstrip("#/").split("/")
        node = schema
        for part in ref_path:
            node = node[part]
        file_prop = node
    assert file_prop.get("description") == "The PDF file to parse"


# ---------------------------------------------------------------------------
# Regression: functional endpoints still work after metadata changes
# ---------------------------------------------------------------------------


def test_health_endpoint_still_returns_ok():
    response = _client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parse_endpoint_still_rejects_missing_file():
    """Ensure metadata-only changes did not break request validation."""
    response = _client.post("/parse")
    assert response.status_code == 422
