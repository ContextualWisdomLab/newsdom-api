from newsdom_api.metering import CanonicalParseUsageSink
from newsdom_api.schemas import (
    ArticleNode,
    CaptionNode,
    ImageNode,
    PageNode,
    ParseResponse,
)


def test_parse_export_counts_real_response_shape_without_document_text():
    queued = []
    response = ParseResponse(
        document_id="doc-1",
        pages=[
            PageNode(
                page_number=1,
                headers=["header"],
                articles=[
                    ArticleNode(
                        article_id="article-1",
                        headline="headline",
                        body_blocks=["body-1", "body-2"],
                        captions=[CaptionNode(text="caption")],
                        images=[
                            ImageNode(
                                path="image.png", footnotes=[CaptionNode(text="note")]
                            )
                        ],
                    )
                ],
            )
        ],
    )
    sink = CanonicalParseUsageSink(
        event_builder=lambda **payload: payload,
        enqueue=queued.append,
        identity={
            "tenant_reference": "urn:cwl:tenant:test",
            "billing_account_reference": "urn:cwl:account:test",
            "billing_principal_reference": "urn:cwl:principal:test",
        },
    )

    sink.emit_parse(
        response,
        document_job_reference="urn:cwl:job:1",
        pdf_bytes=b"%PDF",
        ocr_page_count=1,
        occurred_at="2026-08-28T00:00:00Z",
        shard_reference="urn:cwl:shard:1",
        credential_reference="urn:cwl:credential:1",
    )

    event = queued[0]
    assert event["pdf_bytes"] == 4
    assert event["page_count"] == 1
    assert event["ocr_page_count"] == 1
    assert event["extracted_block_count"] == 6
    assert event["credential_reference"] == "urn:cwl:credential:1"
    assert "headline" not in event
    assert "body-1" not in event


def test_failed_parse_is_not_exported():
    queued = []
    response = ParseResponse(
        document_id="doc-1",
        quality={"status": "failed"},
    )
    sink = CanonicalParseUsageSink(
        event_builder=lambda **payload: payload,
        enqueue=queued.append,
        identity={},
    )

    sink.emit_parse(
        response,
        document_job_reference="job-1",
        pdf_bytes=b"pdf",
        ocr_page_count=0,
        occurred_at="2026-08-28T00:00:00Z",
    )

    assert queued == []

    partial = ParseResponse(
        document_id="doc-1",
        quality={"status": "partial"},
    )
    sink.emit_parse(
        partial,
        document_job_reference="job-1",
        pdf_bytes=b"pdf",
        ocr_page_count=0,
        occurred_at="2026-08-28T00:00:00Z",
    )
    assert len(queued) == 1


def test_identity_cannot_override_parse_fields():
    """Reserved parse fields remain under the sink's explicit authority."""
    try:
        CanonicalParseUsageSink(
            event_builder=lambda **payload: payload,
            enqueue=lambda _: None,
            identity={"document_id": "must-not-override"},
        )
    except ValueError as error:
        assert "document_id" in str(error)
    else:
        raise AssertionError("reserved identity field was accepted")


def test_identity_cannot_inject_document_content():
    """Private document text is rejected before reaching the builder."""
    try:
        CanonicalParseUsageSink(
            event_builder=lambda **payload: payload,
            enqueue=lambda _: None,
            identity={"document_text": "must-not-reach-builder"},
        )
    except ValueError as error:
        assert "document_text" in str(error)
    else:
        raise AssertionError("private document content was accepted as identity")
