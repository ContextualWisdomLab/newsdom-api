from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.filter_dom import filter_dom, main


@pytest.fixture
def mock_json_path(tmp_path: Path) -> Path:
    data = {
        "document_id": "test-1",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "a1",
                        "headline": "Test Headline 1",
                        "body_blocks": ["body 1"],
                    },
                    {
                        "article_id": "a2",
                        "headline": "Another Headline",
                        "body_blocks": ["body 2"],
                    },
                ],
            },
            {
                "page_number": 2,
                "articles": [
                    {
                        "article_id": "a3",
                        "headline": "Test Headline 2",
                        "body_blocks": ["body 3"],
                    },
                ],
            },
        ],
    }
    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_filter_dom_success(mock_json_path: Path, tmp_path: Path):
    output_path = tmp_path / "output.json"
    result = filter_dom(mock_json_path, r"^Test Headline", output_path)

    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["articles"]) == 1
    assert result["pages"][0]["articles"][0]["article_id"] == "a1"
    assert len(result["pages"][1]["articles"]) == 1
    assert result["pages"][1]["articles"][0]["article_id"] == "a3"

    assert output_path.exists()
    saved_data = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(saved_data["pages"]) == 2


def test_filter_dom_file_not_found():
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_dom(Path("nonexistent.json"), "query")


def test_filter_dom_invalid_extension(tmp_path: Path):
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="File must be a .json file"):
        filter_dom(txt_file, "query")


def test_filter_dom_invalid_json(tmp_path: Path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad json}", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(bad_json, "query")


def test_filter_dom_invalid_regex(mock_json_path: Path):
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        filter_dom(mock_json_path, "[invalid")


def test_main_success_stdout(mock_json_path: Path, capsys: pytest.CaptureFixture):
    main([str(mock_json_path), "Another"])
    captured = capsys.readouterr()
    assert "Another Headline" in captured.out
    assert "Test Headline" not in captured.out


def test_main_success_file(
    mock_json_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture
):
    output_path = tmp_path / "out.json"
    main([str(mock_json_path), "Another", "-o", str(output_path)])
    captured = capsys.readouterr()
    assert f"Filtered DOM saved to {output_path}" in captured.out
    assert output_path.exists()


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("invalid", encoding="utf-8")
    with pytest.raises(SystemExit) as exc_info:
        main([str(bad_json), "query"])
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Invalid JSON file" in captured.err
