from typing import Any
import json
from pathlib import Path

from newsdom_api.schemas import ParseResponse
from newsdom_api.service import _safe_upload_filename, parse_pdf_bytes


def test_parse_pdf_bytes_writes_temp_file_and_builds_dom(monkeypatch):
    observed = {}
    model = json.loads(
        Path("tests/fixtures/mineru_multi_page_model.json").read_text(encoding="utf-8")
    )

    def fake_run_mineru(path: Path, **kwargs):
        observed["path_name"] = path.name
        observed["bytes"] = path.read_bytes()
        observed["language"] = kwargs.get("language")
        observed["mode"] = kwargs.get("mode")
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
    assert observed["language"] == "ch"
    assert observed["mode"] == "auto"


def test_parse_pdf_bytes_sanitizes_client_filename(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
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


def test_parse_pdf_bytes_sanitizes_null_bytes(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
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
    result = parse_pdf_bytes(b"pdf-bytes", filename="null\0byte.pdf")
    assert observed["path_name"] == "nullbyte.pdf"
    assert result.document_id == "nullbyte"


def test_parse_pdf_bytes_sanitizes_shell_chars(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
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
    result = parse_pdf_bytes(b"pdf-bytes", filename="file!@#$%^&()_+-=.pdf")
    assert observed["path_name"] == "file___________-_.pdf"
    assert result.document_id == "file___________-_"


def test_parse_pdf_bytes_truncates_long_sanitized_filename(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
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
    result = parse_pdf_bytes(b"pdf-bytes", filename=f"{'a' * 300}.pdf")
    assert observed["path_name"] == f"{'a' * 236}.pdf"
    assert len(observed["path_name"]) == 240
    assert result.document_id == "a" * 236


def test_safe_upload_filename_truncates_long_name_without_extension():
    assert _safe_upload_filename("b" * 300) == "b" * 240


def test_safe_upload_filename_protects_against_dos():
    assert _safe_upload_filename("c" * 1000) == "c" * 240


def test_parse_pdf_bytes_sanitizes_windows_client_filename(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
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
    result = parse_pdf_bytes(b"pdf-bytes", filename=r"..\nested\unsafe.pdf")
    assert observed["path_name"] == "unsafe.pdf"
    assert result.document_id == "unsafe"


def test_parse_pdf_bytes_uses_default_for_parent_only_filename(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
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
    result = parse_pdf_bytes(b"pdf-bytes", filename="../..")
    assert observed["path_name"] == "upload.pdf"
    assert result.document_id == "upload"


def test_parse_pdf_bytes_forwards_language_and_mode(monkeypatch):
    observed = {}

    def fake_run_mineru(path: Path, **kwargs):
        observed["language"] = kwargs.get("language")
        observed["mode"] = kwargs.get("mode")
        return {
            "content_list": [
                {
                    "type": "text",
                    "text": "heading",
                    "text_level": 1,
                    "bbox": [0, 0, 1, 1],
                }
            ]
        }

    monkeypatch.setattr("newsdom_api.service.run_mineru", fake_run_mineru)
    result = parse_pdf_bytes(
        b"pdf-bytes", filename="fixture.pdf", language="japan", mode="ocr"
    )
    assert observed["language"] == "japan"
    assert observed["mode"] == "ocr"
    assert result.document_id == "fixture"

def test_parse_pdf_isolates_caller_file_from_parser_mutation(
    tmp_path: Path, monkeypatch: Any
) -> None:
    import newsdom_api.service as service

    original = b"%PDF-1.4 caller-owned"
    pdf_file = tmp_path / "caller.pdf"
    pdf_file.write_bytes(original)

    def mutating_run_mineru(path: Path, **kwargs):
        path.write_bytes(b"%PDF-1.4 parser-mutated")
        return {"content_list": [], "model": []}

    monkeypatch.setattr(service, "run_mineru", mutating_run_mineru)
    monkeypatch.setattr(
        service,
        "build_dom",
        lambda *args, **kwargs: ParseResponse(document_id="caller", pages=[]),
    )

    service.parse_pdf(pdf_file, filename="caller.pdf")

    assert pdf_file.read_bytes() == original
