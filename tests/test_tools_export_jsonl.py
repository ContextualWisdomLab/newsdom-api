from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.export_jsonl import export_jsonl, main


@pytest.fixture
def sample_json_path(tmp_path: Path) -> Path:
    data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art1",
                        "headline": "Head 1",
                        "body_blocks": ["Block 1", "Block 2"],
                    },
                    {
                        "article_id": "art2",
                        "headline": "Head 2",
                        "body_blocks": [],
                    },
                ],
            },
            "invalid_page_type",
            {
                "page_number": 2,
                "articles": ["invalid_article_type"],
            },
        ],
    }
    file_path = tmp_path / "input.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_export_jsonl_success(sample_json_path: Path, tmp_path: Path) -> None:
    output_path = tmp_path / "output.jsonl"
    export_jsonl(sample_json_path, output_path)

    assert output_path.exists()

    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    record1 = json.loads(lines[0])
    assert record1["document_id"] == "doc123"
    assert record1["page_number"] == 1
    assert record1["article_id"] == "art1"
    assert record1["headline"] == "Head 1"
    assert record1["body_block_index"] == 0
    assert record1["body_block_text"] == "Block 1"

    record2 = json.loads(lines[1])
    assert record2["body_block_index"] == 1
    assert record2["body_block_text"] == "Block 2"

    record3 = json.loads(lines[2])
    assert record3["article_id"] == "art2"
    assert record3["body_block_index"] is None
    assert record3["body_block_text"] is None


def test_export_jsonl_file_not_found(tmp_path: Path) -> None:
    input_path = tmp_path / "not_found.json"
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        export_jsonl(input_path, output_path)


def test_export_jsonl_invalid_extension(tmp_path: Path) -> None:
    input_path = tmp_path / "input.txt"
    input_path.touch()
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Input file must be a .json file"):
        export_jsonl(input_path, output_path)


def test_export_jsonl_invalid_json(tmp_path: Path) -> None:
    input_path = tmp_path / "input.json"
    input_path.write_text("invalid json", encoding="utf-8")
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_path, output_path)


def test_export_jsonl_preserves_published_output_when_encoding_fails(
    sample_json_path: Path, tmp_path: Path, monkeypatch
) -> None:
    output_path = tmp_path / "output.jsonl"
    output_path.write_text("original content", encoding="utf-8")

    def mock_dumps(*args, **kwargs):
        raise TypeError("Simulated encoding error")

    monkeypatch.setattr(json, "dumps", mock_dumps)

    with pytest.raises(TypeError, match="Simulated encoding error"):
        export_jsonl(sample_json_path, output_path)

    assert output_path.read_text(encoding="utf-8") == "original content"

    temp_files = list(tmp_path.glob("tmp*"))
    assert len(temp_files) == 0


def test_main_success(sample_json_path: Path, tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "output.jsonl"
    main([str(sample_json_path), str(output_path)])

    assert output_path.exists()
    captured = capsys.readouterr()
    assert f"JSONL successfully written to {output_path}" in captured.out


def test_main_error(tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "not_found.json"
    output_path = tmp_path / "output.jsonl"
    with pytest.raises(SystemExit) as exc_info:
        main([str(input_path), str(output_path)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err

def test_export_jsonl_cleans_up_on_exception_without_temp_file(
    sample_json_path: Path, tmp_path: Path, monkeypatch
) -> None:
    output_path = tmp_path / "output.jsonl"

    def mock_dumps(*args, **kwargs):
        raise TypeError("Simulated error")

    monkeypatch.setattr(json, "dumps", mock_dumps)

    # We'll monkeypatch unlink to ensure it's not called if the file doesn't exist
    from pathlib import Path
    original_exists = Path.exists
    original_unlink = Path.unlink

    unlink_called = False

    def mock_exists(self):
        if str(self).startswith(str(tmp_path / "tmp")):
            return False
        return original_exists(self)

    def mock_unlink(self):
        nonlocal unlink_called
        if str(self).startswith(str(tmp_path / "tmp")):
            unlink_called = True
        else:
            original_unlink(self)

    monkeypatch.setattr(Path, "exists", mock_exists)
    monkeypatch.setattr(Path, "unlink", mock_unlink)

    with pytest.raises(TypeError, match="Simulated error"):
        export_jsonl(sample_json_path, output_path)

    assert not unlink_called
