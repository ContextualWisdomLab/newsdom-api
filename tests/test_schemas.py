from newsdom_api.schemas import (
    ArticleNode,
    BoundingBox,
    CaptionNode,
    HealthResponse,
    ImageNode,
    PageNode,
    ParseQuality,
    ParseResponse,
    ReadinessResponse,
)


def test_parse_response_schema_round_trip():
    article = ArticleNode(article_id="a1", headline="headline", body_blocks=[])
    response = ParseResponse(document_id="doc1", pages=[])
    assert article.article_id == "a1"
    assert response.document_id == "doc1"


def test_health_response_schema_round_trip():
    response = HealthResponse(status="ok")
    assert response.status == "ok"

    # Verify default behavior
    response_default = HealthResponse()
    assert response_default.status == "ok"


def test_page_node_openapi_schema_descriptions():
    schema = PageNode.model_json_schema()
    properties = schema["properties"]

    assert (
        properties["page_number"]["description"]
        == "One-based page number from the parsed PDF."
    )
    assert properties["articles"]["description"] == "Articles extracted from this page."


def _assert_no_deprecated_example_keyword(value):
    if isinstance(value, dict):
        assert "example" not in value
        for child in value.values():
            _assert_no_deprecated_example_keyword(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_deprecated_example_keyword(child)


def test_openapi_schema_examples_use_json_schema_2020_12_contract():
    models = (
        BoundingBox,
        CaptionNode,
        ImageNode,
        ArticleNode,
        PageNode,
        ParseQuality,
        ParseResponse,
        HealthResponse,
        ReadinessResponse,
    )
    for model in models:
        _assert_no_deprecated_example_keyword(model.model_json_schema())

    page_properties = PageNode.model_json_schema()["properties"]
    assert page_properties["width"]["examples"] == [800.0]
    assert page_properties["height"]["examples"] == [1200.0]
    assert page_properties["ads"]["examples"] == [["Buy our new product!"]]
    assert page_properties["headers"]["examples"] == [["Chapter 1: Introduction"]]
    assert page_properties["footers"]["examples"] == [["Confidential Document"]]
    assert page_properties["page_numbers"]["examples"] == [["1", "Page 1"]]

    image_schema = ImageNode.model_json_schema()
    assert image_schema["properties"]["media_type"]["examples"] == ["image"]

    article_schema = ArticleNode.model_json_schema()
    assert "headline" in article_schema["required"]
