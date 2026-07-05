from newsdom_api.schemas import ArticleNode, ParseResponse


def test_parse_response_schema_round_trip():
    article = ArticleNode(article_id="a1", headline="headline", body_blocks=[])
    response = ParseResponse(document_id="doc1", pages=[])
    assert article.article_id == "a1"
    assert response.document_id == "doc1"
