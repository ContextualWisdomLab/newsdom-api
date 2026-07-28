import pytest
from newsdom_api.schemas import ParseQuality

def test_parse_quality_openapi_examples():
    """Verify that ParseQuality schema contains the correct DX/UX OpenAPI examples."""
    schema = ParseQuality.model_json_schema()

    assert schema["properties"]["status"]["example"] == "success"
    assert schema["properties"]["parser"]["example"] == "mineru"
    assert schema["properties"]["warnings"]["example"] == ["Low OCR confidence on page 2"]
