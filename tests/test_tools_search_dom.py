from __future__ import annotations

import json
from pathlib import Path
import pytest

from tools.search_dom import main, search_dom


def create_sample_dom(path: Path) -> None:
    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "Breaking News Today",
                        "body_blocks": [
                            "This is a test block.",
                            "We found something amazing.",
                            "The keyword is hidden here.",
                        ],
                    }
                ],
            },
            {
                "page_number": 2,
                "articles": [
                    {
                        "article_id": "art-2",
                        "headline": "Another Keyword headline",
                        "body_blocks": ["Just random text."],
                    }
                ],
            },
        ]
    }
    path.write_text(json.dumps(data), encoding="utf-8")


def test_search_dom_found(tmp_path: Path) -> None:
    json_path = tmp_path / "test.json"
    create_sample_dom(json_path)

    results = search_dom(json_path, "keyword")

    assert len(results) == 2
    assert results[0]["type"] == "body_block"
    assert results[0]["page"] == 1
    assert results[0]["article_id"] == "art-1"

    assert results[1]["type"] == "headline"
    assert results[1]["page"] == 2
    assert results[1]["article_id"] == "art-2"


def test_search_dom_not_found(tmp_path: Path) -> None:
    json_path = tmp_path / "test.json"
    create_sample_dom(json_path)

    results = search_dom(json_path, "missingword")
    assert len(results) == 0


def test_search_dom_file_not_found(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.json"
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        search_dom(non_existent, "query")


def test_search_dom_invalid_extension(tmp_path: Path) -> None:
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("not json", encoding="utf-8")
    with pytest.raises(ValueError, match="File must be a .json file"):
        search_dom(txt_path, "query")


def test_search_dom_invalid_json(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_json.json"
    json_path.write_text("invalid{json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        search_dom(json_path, "query")


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    json_path = tmp_path / "test.json"
    create_sample_dom(json_path)

    main([str(json_path), "keyword"])

    captured = capsys.readouterr()
    assert "Found 2 results for query: 'keyword'" in captured.out
    assert (
        "- Page 1, Article art-1 [Body Block 2]: The keyword is hidden here."
        in captured.out
    )
    assert (
        "- Page 2, Article art-2 [Headline]: Another Keyword headline" in captured.out
    )


def test_main_no_results(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    json_path = tmp_path / "test.json"
    create_sample_dom(json_path)

    main([str(json_path), "nonexistent"])

    captured = capsys.readouterr()
    assert "No results found for query: 'nonexistent'" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    non_existent = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(non_existent), "query"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "File not found" in captured.err


def test_search_dom_unknown_type(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Test the unexpected else branch in main() for line 86
    import json

    json_path = tmp_path / "test.json"
    data = {"pages": []}
    json_path.write_text(json.dumps(data), encoding="utf-8")

    # We mock search_dom to return a result with an unknown type
    import tools.search_dom

    def mock_search_dom(*args, **kwargs):
        return [
            {"type": "unknown_type", "page": 1, "article_id": "art-1", "text": "text"}
        ]

    monkeypatch.setattr(tools.search_dom, "search_dom", mock_search_dom)

    tools.search_dom.main([str(json_path), "query"])

    captured = capsys.readouterr()
    assert "Found 1 results" in captured.out
    assert "Headline" not in captured.out
    assert "Body Block" not in captured.out
