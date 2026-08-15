"""Acceptance tests for provenance-preserving NewsDOM JSONL flattening."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

from tools import flatten_dom


@pytest.fixture
def valid_dom_json(tmp_path: Path) -> Path:
    """Write a realistic parsed page with text and image-linked evidence."""

    json_path = tmp_path / "valid.json"
    data = {
        "document_id": "doc-123",
        "pages": [
            {
                "page_number": 1,
                "width": 612,
                "height": 792,
                "headers": ["Daily Header"],
                "page_numbers": ["1"],
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "Test Headline",
                        "bbox": {"x0": 10, "y0": 20, "x1": 500, "y1": 700},
                        "body_blocks": ["Block 1", ""],
                        "images": [
                            {
                                "path": "images/art-1-chart.png",
                                "media_type": "image/png",
                                "bbox": {
                                    "x0": 100,
                                    "y0": 200,
                                    "x1": 400,
                                    "y1": 500,
                                },
                                "captions": [
                                    {
                                        "text": "Image Caption",
                                        "bbox": {
                                            "x0": 100,
                                            "y0": 501,
                                            "x1": 400,
                                            "y1": 530,
                                        },
                                    }
                                ],
                                "footnotes": [{"text": "Image Footnote"}],
                            }
                        ],
                        "captions": [{"text": "Article Caption"}],
                        "footnotes": [
                            {
                                "text": "Article Footnote",
                                "bbox": {
                                    "x0": 10,
                                    "y0": 701,
                                    "x1": 500,
                                    "y1": 730,
                                },
                            }
                        ],
                    },
                    {
                        "article_id": "art-2",
                        "headline": "",
                        "body_blocks": [],
                        "images": [],
                        "captions": [{"text": ""}],
                        "footnotes": [],
                    },
                ],
                "ads": ["Buy now"],
                "footers": ["Daily Footer"],
            }
        ],
        "quality": {
            "status": "success",
            "parser": "mineru",
            "warnings": ["minor layout warning"],
        },
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def invalid_dom_json(tmp_path: Path) -> Path:
    """Write JSON that cannot satisfy the canonical ParseResponse schema."""

    json_path = tmp_path / "invalid.json"
    json_path.write_text(json.dumps({"wrong_schema": True}), encoding="utf-8")
    return json_path


def test_json_pointer_escapes_reference_tokens() -> None:
    """Source pointers should follow RFC 6901 escaping rules."""

    assert flatten_dom._json_pointer("a/b", "m~n", 0) == "/a~1b/m~0n/0"


def test_sys_path_insertion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Importing the CLI should expose the repository's source package."""

    monkeypatch.setattr(sys, "path", [])
    module = importlib.reload(flatten_dom)

    expected_src = str(Path(module.__file__).resolve().parents[1] / "src")
    assert sys.path[0] == expected_src


def test_flatten_dom_preserves_semantic_units_and_provenance(
    valid_dom_json: Path,
) -> None:
    """Every searchable unit should retain exact document and image origins."""

    records = flatten_dom.flatten_dom(valid_dom_json)

    assert [record["type"] for record in records] == [
        "page_header",
        "page_number",
        "headline",
        "body_block",
        "image_caption",
        "image_footnote",
        "caption",
        "footnote",
        "advertisement",
        "page_footer",
    ]
    assert [record["record_index"] for record in records] == list(range(10))
    assert [record["source_pointer"] for record in records] == [
        "/pages/0/headers/0",
        "/pages/0/page_numbers/0",
        "/pages/0/articles/0/headline",
        "/pages/0/articles/0/body_blocks/0",
        "/pages/0/articles/0/images/0/captions/0/text",
        "/pages/0/articles/0/images/0/footnotes/0/text",
        "/pages/0/articles/0/captions/0/text",
        "/pages/0/articles/0/footnotes/0/text",
        "/pages/0/ads/0",
        "/pages/0/footers/0",
    ]
    assert [record["text"] for record in records] == [
        "Daily Header",
        "1",
        "Test Headline",
        "Block 1",
        "Image Caption",
        "Image Footnote",
        "Article Caption",
        "Article Footnote",
        "Buy now",
        "Daily Footer",
    ]

    for record in records:
        assert record["document_id"] == "doc-123"
        assert record["page_number"] == 1
        assert record["page_width"] == 612.0
        assert record["page_height"] == 792.0
        assert record["parser"] == "mineru"
        assert record["parse_status"] == "success"

    assert records[0]["article_id"] is None
    assert records[2]["article_id"] == "art-1"
    assert records[2]["article_bbox"] == {
        "x0": 10.0,
        "y0": 20.0,
        "x1": 500.0,
        "y1": 700.0,
    }
    assert records[4]["source_kind"] == "image_text"
    assert records[4]["image_path"] == "images/art-1-chart.png"
    assert records[4]["image_media_type"] == "image/png"
    assert records[4]["bbox"] == {
        "x0": 100.0,
        "y0": 501.0,
        "x1": 400.0,
        "y1": 530.0,
    }
    assert records[4]["image_bbox"] == {
        "x0": 100.0,
        "y0": 200.0,
        "x1": 400.0,
        "y1": 500.0,
    }
    assert records[5]["bbox"] is None
    assert records[6]["image_path"] is None
    assert records[7]["bbox"] == {
        "x0": 10.0,
        "y0": 701.0,
        "x1": 500.0,
        "y1": 730.0,
    }


def test_flatten_dom_empty_document(tmp_path: Path) -> None:
    """A valid document without pages should produce no artificial chunks."""

    json_path = tmp_path / "empty.json"
    json_path.write_text(
        json.dumps(
            {
                "document_id": "doc-empty",
                "pages": [],
                "quality": {
                    "status": "success",
                    "parser": "mineru",
                    "warnings": [],
                },
            }
        ),
        encoding="utf-8",
    )

    assert flatten_dom.flatten_dom(json_path) == []


def test_flatten_dom_not_found(tmp_path: Path) -> None:
    """Missing input should identify the path customers need to fix."""

    missing_path = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        flatten_dom.flatten_dom(missing_path)


def test_flatten_dom_wrong_extension(tmp_path: Path) -> None:
    """The CLI should reject non-JSON inputs before parsing them."""

    text_path = tmp_path / "wrong.txt"
    text_path.write_text("test", encoding="utf-8")

    with pytest.raises(ValueError, match=r"must be a \.json file"):
        flatten_dom.flatten_dom(text_path)


def test_flatten_dom_invalid_json(tmp_path: Path) -> None:
    """Malformed JSON should retain an actionable parse reason."""

    json_path = tmp_path / "bad.json"
    json_path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON file"):
        flatten_dom.flatten_dom(json_path)


def test_flatten_dom_validation_error(invalid_dom_json: Path) -> None:
    """Structurally invalid JSON should name the canonical schema contract."""

    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        flatten_dom.flatten_dom(invalid_dom_json)


def test_main_stdout(
    valid_dom_json: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without an output path, each semantic unit should be one JSONL line."""

    flatten_dom.main([str(valid_dom_json)])

    lines = capsys.readouterr().out.splitlines()
    records = [json.loads(line) for line in lines]
    assert len(records) == 10
    assert records[2]["text"] == "Test Headline"
    assert records[4]["image_path"] == "images/art-1-chart.png"


def test_main_atomically_replaces_output_and_creates_parent(
    valid_dom_json: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Successful writes should replace an old file only after full serialization."""

    output_path = tmp_path / "nested" / "out.jsonl"
    output_path.parent.mkdir()
    output_path.write_text('{"old": true}\n', encoding="utf-8")

    flatten_dom.main([str(valid_dom_json), "--output", str(output_path)])

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 10
    assert json.loads(lines[0])["text"] == "Daily Header"
    assert "Flattened DOM saved to" in capsys.readouterr().out
    assert list(output_path.parent.glob(f".{output_path.name}.*.tmp")) == []


def test_main_creates_missing_output_parent(
    valid_dom_json: Path, tmp_path: Path
) -> None:
    """A requested nested output path should not require manual directory setup."""

    output_path = tmp_path / "new" / "nested" / "out.jsonl"

    flatten_dom.main([str(valid_dom_json), "--output", str(output_path)])

    assert output_path.is_file()


def test_main_preserves_existing_output_when_replace_fails(
    valid_dom_json: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A failed atomic replace should leave the previous complete JSONL intact."""

    output_path = tmp_path / "out.jsonl"
    original = '{"complete": true}\n'
    output_path.write_text(original, encoding="utf-8")

    def fail_replace(source: object, destination: object) -> None:
        raise OSError(f"cannot replace {source} with {destination}")

    monkeypatch.setattr(flatten_dom.os, "replace", fail_replace)

    with pytest.raises(SystemExit) as exit_info:
        flatten_dom.main([str(valid_dom_json), "--output", str(output_path)])

    assert exit_info.value.code == 1
    assert output_path.read_text(encoding="utf-8") == original
    assert list(tmp_path.glob(f".{output_path.name}.*.tmp")) == []
    assert "cannot replace" in capsys.readouterr().err


def test_main_expected_input_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Expected customer errors should exit with one actionable message."""

    missing_path = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exit_info:
        flatten_dom.main([str(missing_path)])

    assert exit_info.value.code == 1
    assert str(missing_path) in capsys.readouterr().err


def test_main_propagates_unexpected_errors(
    valid_dom_json: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Implementation defects should preserve their traceback for operators."""

    def fail_unexpectedly(path: Path) -> list[dict[str, object]]:
        raise RuntimeError(f"unexpected defect for {path}")

    monkeypatch.setattr(flatten_dom, "flatten_dom", fail_unexpectedly)

    with pytest.raises(RuntimeError, match="unexpected defect"):
        flatten_dom.main([str(valid_dom_json)])
