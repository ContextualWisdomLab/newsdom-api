import json
from pathlib import Path
from unittest.mock import patch

import pytest
from tools.export_jsonl import export_jsonl, main

@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Test Headline",
                        "body_blocks": ["Block 1", "Block 2"]
                    },
                    "invalid_article"
                ]
            },
            "invalid_page"
        ]
    }
    json_path = tmp_path / "test.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path

def test_export_jsonl_success(sample_json: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "output.jsonl"
    export_jsonl(sample_json, output_path)
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(content) == 1
    record = json.loads(content[0])
    assert record["document_id"] == "test_doc"
    assert record["page_number"] == 1
    assert record["article_id"] == "art_1"
    assert record["headline"] == "Test Headline"
    assert record["body_blocks"] == ["Block 1", "Block 2"]

def test_export_jsonl_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="File not found"):
        export_jsonl(tmp_path / "missing.json", tmp_path / "out.jsonl")

def test_export_jsonl_invalid_extension(tmp_path: Path) -> None:
    invalid_file = tmp_path / "test.txt"
    invalid_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input file must be a .json file."):
        export_jsonl(invalid_file, tmp_path / "out.jsonl")

def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file:"):
        export_jsonl(bad_json, tmp_path / "out.jsonl")

def test_main_success(sample_json: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    output_path = tmp_path / "out_main.jsonl"
    main([str(sample_json), str(output_path)])
    assert output_path.exists()
    captured = capsys.readouterr()
    assert "JSONL successfully written to" in captured.out

def test_main_failure(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    missing_file = tmp_path / "missing.json"
    output_path = tmp_path / "out_main.jsonl"
    with pytest.raises(SystemExit) as excinfo:
        main([str(missing_file), str(output_path)])
    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL:" in captured.err
