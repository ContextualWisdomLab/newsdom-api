from fastapi.testclient import TestClient
from newsdom_api.main import app


def test_parse_endpoint_openapi_schema():
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200

    schema = response.json()
    parse_body_schema = schema["components"]["schemas"].get("Body_parse_parse_post")
    assert parse_body_schema is not None, "Body schema for parse endpoint not found"

    properties = parse_body_schema.get("properties", {})

    assert "file" in properties
    assert properties["file"].get("example") == "document.pdf", (
        "File example missing or incorrect"
    )

    assert "language" in properties
    assert properties["language"].get("example") == "ch", (
        "Language example missing or incorrect"
    )

    assert "mode" in properties
    assert properties["mode"].get("example") == "auto", (
        "Mode example missing or incorrect"
    )
