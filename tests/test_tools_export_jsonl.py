import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main


def test_export_jsonl_file_not_found(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError):
        export_jsonl(missing_file, tmp_path / "out.jsonl")


def test_export_jsonl_invalid_extension(tmp_path: Path) -> None:
    invalid_ext = tmp_path / "data.txt"
    invalid_ext.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        export_jsonl(invalid_ext, tmp_path / "out.jsonl")


def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    invalid_json = tmp_path / "data.json"
    invalid_json.write_text("{invalid", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(invalid_json, tmp_path / "out.jsonl")


def test_export_jsonl_success(tmp_path: Path) -> None:
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    data = {
        "document_id": "doc_1",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "Head 1",
                        "body_blocks": ["Block 1", "Block 2"],
                    },
                    "invalid_article",
                ],
            },
            "invalid_page",
        ],
    }
    input_json.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_json, output_jsonl)

    assert output_jsonl.exists()
    content = output_jsonl.read_text(encoding="utf-8").strip().split("\n")
    assert len(content) == 1

    record = json.loads(content[0])
    assert record["document_id"] == "doc_1"
    assert record["page_number"] == 1
    assert record["article_id"] == "art_1"
    assert record["headline"] == "Head 1"
    assert record["body_blocks"] == ["Block 1", "Block 2"]


def test_export_jsonl_preserves_published_output_when_encoding_fails(
    tmp_path: Path,
) -> None:
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"

    output_jsonl.write_text("old data", encoding="utf-8")

    data = {
        "document_id": "doc_1",
        "pages": [{"page_number": 1, "articles": [{"article_id": "art_1"}]}],
    }
    input_json.write_text(json.dumps(data), encoding="utf-8")

    with patch("json.dumps", side_effect=Exception("Simulated error")):
        with pytest.raises(Exception, match="Simulated error"):
            export_jsonl(input_json, output_jsonl)

    assert output_jsonl.read_text(encoding="utf-8") == "old data"


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input_json = tmp_path / "input.json"
    output_jsonl = tmp_path / "output.jsonl"
    input_json.write_text('{"pages": []}', encoding="utf-8")

    main([str(input_json), str(output_jsonl)])

    captured = capsys.readouterr()
    assert "successfully written to" in captured.out
    assert output_jsonl.exists()


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    input_json = tmp_path / "missing.json"
    output_jsonl = tmp_path / "output.jsonl"

    with pytest.raises(SystemExit):
        main([str(input_json), str(output_jsonl)])

    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err


def test_sys_path_injection_export() -> None:
    if str(Path(__file__).parent.parent) not in sys.path:  # pragma: no cover
        sys.path.insert(0, str(Path(__file__).parent.parent))  # noqa: E402
    from tools import export_jsonl

    assert export_jsonl is not None
