from newsdom_api.schemas import (
    ArticleNode,
    HealthResponse,
    ImageNode,
    PageNode,
    ParseResponse,
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


def test_openapi_schema_examples_are_exact_and_required_contract_is_preserved():
    page_schema = PageNode.model_json_schema()
    page_properties = page_schema["properties"]
    assert page_properties["width"]["example"] == 800.0
    assert page_properties["height"]["example"] == 1200.0
    assert page_properties["ads"]["example"] == ["Buy our new product!"]
    assert page_properties["headers"]["example"] == ["Chapter 1: Introduction"]
    assert page_properties["footers"]["example"] == ["Confidential Document"]
    assert page_properties["page_numbers"]["example"] == ["1", "Page 1"]

    image_schema = ImageNode.model_json_schema()
    assert image_schema["properties"]["media_type"]["example"] == "image"

    article_schema = ArticleNode.model_json_schema()
    assert "headline" in article_schema["required"]
