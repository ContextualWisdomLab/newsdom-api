from newsdom_api.main import app
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


def test_openapi_response_examples_match_documented_schema_contract():
    schema = app.openapi()
    components = schema["components"]["schemas"]

    page_properties = components["PageNode"]["properties"]
    assert page_properties["width"]["example"] == 595.27
    assert page_properties["height"]["example"] == 841.88
    assert page_properties["ads"]["example"] == ["[광고] 신제품 출시"]
    assert components["ImageNode"]["properties"]["media_type"]["example"] == "image"
