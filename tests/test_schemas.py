from newsdom_api.schemas import ArticleNode, HealthResponse, PageNode, ParseResponse


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


def test_openapi_collection_examples_are_concrete_and_stable():
    """Keep Swagger collection examples populated with domain-valid values."""

    article_properties = ArticleNode.model_json_schema()["properties"]
    page_properties = PageNode.model_json_schema()["properties"]

    assert article_properties["body_blocks"]["example"] == [
        "This is a paragraph of text in the article body."
    ]
    assert page_properties["ads"]["example"] == ["Summer Sale! 50% Off"]
    assert page_properties["headers"]["example"] == ["1. Introduction"]
    assert page_properties["footers"]["example"] == ["Copyright 2023"]
    assert page_properties["page_numbers"]["example"] == ["1", "2"]
