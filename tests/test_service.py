import json
from pathlib import Path

from newsdom_api.schemas import ParseResponse
from newsdom_api.service import parse_pdf_bytes


def test_parse_pdf_bytes_writes_temp_file_and_builds_dom(monkeypatch):
    observed = {}
    model = json.loads(
        Path("tests/fixtures/mineru_multi_page_model.json").read_text(encoding="utf-8")
    )

    def fake_run_mineru(path: Path):
        observed["path_name"] = path.name
        observed["bytes"] = path.read_bytes()
        return {
            "content_list": [
                {
                    "type": "text",
                    "text": "headline",
                    "text_level": 1,
                    "bbox": [0, 0, 1, 1],
                }
            ],
            "model": model,
        }

    def fake_build_dom(content_list, document_id: str, model=None) -> ParseResponse:
        observed["document_id"] = document_id
        observed["content_list"] = content_list
        observed["model"] = model
        return ParseResponse(document_id=document_id, pages=[])

    monkeypatch.setattr("newsdom_api.service.run_mineru", fake_run_mineru)
    monkeypatch.setattr("newsdom_api.service.build_dom", fake_build_dom)

    result = parse_pdf_bytes(b"pdf-bytes", filename="fixture.pdf")
    assert observed["path_name"] == "fixture.pdf"
    assert observed["bytes"] == b"pdf-bytes"
    assert observed["document_id"] == "fixture"
    assert observed["content_list"] == [
        {
            "type": "text",
            "text": "headline",
            "text_level": 1,
            "bbox": [0, 0, 1, 1],
        }
    ]
    assert observed["model"] == model
    assert result.document_id == "fixture"


def test_parse_pdf_bytes_sanitizes_client_filename(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path):
        observed["path_name"] = path.name
        return {
            "content_list": [
                {
                    "type": "text",
                    "text": "headline",
                    "text_level": 1,
                    "bbox": [0, 0, 1, 1],
                }
            ]
        }

    monkeypatch.setattr("newsdom_api.service.run_mineru", fake_run_mineru)
    result = parse_pdf_bytes(b"pdf-bytes", filename="../../nested/unsafe.pdf")
    assert observed["path_name"] == "unsafe.pdf"
    assert result.document_id == "unsafe"
