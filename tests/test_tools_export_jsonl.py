from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.export_jsonl import export_jsonl, main

def create_sample_dom(path: Path) -> None:
    data = {
        "document_id": "doc-123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "Test Headline",
                        "body_blocks": ["Block 1", "Block 2"]
                    },
                    "invalid_article_type"
                ]
            },
            "invalid_page_type"
        ]
    }
    path.write_text(json.dumps(data), encoding="utf-8")

def test_export_jsonl_success(tmp_path: Path) -> None:
    json_path = tmp_path / "test.json"
    create_sample_dom(json_path)
    out_path = tmp_path / "out.jsonl"

    export_jsonl(json_path, out_path)

    lines = out_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1

    data = json.loads(lines[0])
    assert data["document_id"] == "doc-123"
    assert data["page_number"] == 1
    assert data["article_id"] == "art-1"
    assert data["headline"] == "Test Headline"
    assert data["body_blocks"] == ["Block 1", "Block 2"]

def test_export_jsonl_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    out_path = tmp_path / "out.jsonl"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        export_jsonl(missing, out_path)

def test_export_jsonl_invalid_extension(tmp_path: Path) -> None:
    txt = tmp_path / "test.txt"
    txt.write_text("{}", encoding="utf-8")
    out_path = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        export_jsonl(txt, out_path)

def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    json_path = tmp_path / "test.json"
    json_path.write_text("invalid json", encoding="utf-8")
    out_path = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(json_path, out_path)

def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    json_path = tmp_path / "test.json"
    create_sample_dom(json_path)
    out_path = tmp_path / "out.jsonl"

    main([str(json_path), str(out_path)])
    captured = capsys.readouterr()
    assert f"JSONL successfully written to {out_path}" in captured.out

def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "missing.json"
    out_path = tmp_path / "out.jsonl"

    with pytest.raises(SystemExit) as exc_info:
        main([str(missing), str(out_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err
