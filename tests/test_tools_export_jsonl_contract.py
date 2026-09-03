"""Canonical-schema contract tests for the JSONL export boundary."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.export_jsonl import export_jsonl


def _canonical_document() -> dict[str, object]:
    return {
        "document_id": "doc-1",
        "pages": [
            {
                "page_number": 1,
                "width": 800.0,
                "height": 1200.0,
                "articles": [
                    {
                        "article_id": "section-1",
                        "headline": "Quarterly results",
                        "bbox": {"x0": 10.0, "y0": 20.0, "x1": 700.0, "y1": 300.0},
                        "body_blocks": ["Revenue increased."],
                        "images": [
                            {
                                "path": "images/figure-1.png",
                                "media_type": "image",
                                "bbox": {"x0": 30.0, "y0": 80.0, "x1": 400.0, "y1": 260.0},
                                "captions": [{"text": "Figure 1", "bbox": None}],
                                "footnotes": [],
                            }
                        ],
                        "captions": [{"text": "Section caption", "bbox": None}],
                        "footnotes": [{"text": "Source note", "bbox": None}],
                    }
                ],
                "ads": [],
                "headers": [],
                "footers": [],
                "page_numbers": ["1"],
            }
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }


def test_export_preserves_canonical_article_provenance(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text(json.dumps(_canonical_document()), encoding="utf-8")

    export_jsonl(input_file, output_file)

    exported = json.loads(output_file.read_text(encoding="utf-8").strip())
    assert exported["document_id"] == "doc-1"
    assert exported["page_number"] == 1
    assert exported["article_id"] == "section-1"
    assert exported["bbox"] == {"x0": 10.0, "y0": 20.0, "x1": 700.0, "y1": 300.0}
    assert exported["images"][0]["path"] == "images/figure-1.png"
    assert exported["images"][0]["captions"][0]["text"] == "Figure 1"
    assert exported["captions"][0]["text"] == "Section caption"
    assert exported["footnotes"][0]["text"] == "Source note"


def test_export_rejects_noncanonical_page_shape_instead_of_silently_dropping_it(
    tmp_path: Path,
) -> None:
    document = _canonical_document()
    pages = document["pages"]
    assert isinstance(pages, list)
    pages.append("not-a-page")
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.jsonl"
    input_file.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ValueError, match="canonical NewsDOM"):
        export_jsonl(input_file, output_file)

    assert not output_file.exists()


def test_export_rejects_output_that_would_overwrite_input(tmp_path: Path) -> None:
    input_file = tmp_path / "document.json"
    original = json.dumps(_canonical_document(), ensure_ascii=False)
    input_file.write_text(original, encoding="utf-8")

    with pytest.raises(ValueError, match="Output path must differ from input path"):
        export_jsonl(input_file, input_file)

    assert input_file.read_text(encoding="utf-8") == original
