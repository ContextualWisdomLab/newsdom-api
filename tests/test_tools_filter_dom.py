from pathlib import Path
import json
import pytest

from tools.filter_dom import filter_dom, main


@pytest.fixture
def mock_dom_data():
    return {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "Matching keyword in title",
                        "body_blocks": ["Some unrelated text."],
                    },
                    {
                        "headline": "No match here",
                        "body_blocks": [
                            "But the keyword is in the body.",
                            "Another block.",
                        ],
                    },
                    {
                        "headline": "Completely unrelated",
                        "body_blocks": ["Nothing to see here."],
                    },
                ]
            }
        ]
    }


def test_filter_dom_success(
    tmp_path: Path, mock_dom_data: dict, capsys: pytest.CaptureFixture
):
    test_json = tmp_path / "test.json"
    test_json.write_text(json.dumps(mock_dom_data), encoding="utf-8")

    result = filter_dom(test_json, "keyword")

    pages = result.get("pages", [])
    assert len(pages) == 1
    articles = pages[0].get("articles", [])
    assert len(articles) == 2
    assert articles[0]["headline"] == "Matching keyword in title"
    assert articles[1]["headline"] == "No match here"


def test_filter_dom_file_not_found():
    with pytest.raises(FileNotFoundError):
        filter_dom(Path("nonexistent.json"), "keyword")


def test_filter_dom_invalid_extension(tmp_path: Path):
    test_txt = tmp_path / "test.txt"
    test_txt.write_text("{}", encoding="utf-8")

    with pytest.raises(ValueError, match="File must be a .json file"):
        filter_dom(test_txt, "keyword")


def test_main_success(
    tmp_path: Path, mock_dom_data: dict, capsys: pytest.CaptureFixture
):
    test_json = tmp_path / "test.json"
    test_json.write_text(json.dumps(mock_dom_data), encoding="utf-8")

    main([str(test_json), "keyword"])
    captured = capsys.readouterr()

    assert "Matching keyword in title" in captured.out
    assert "No match here" in captured.out
    assert "Completely unrelated" not in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture):
    with pytest.raises(SystemExit) as exc_info:
        main(["nonexistent.json", "keyword"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
