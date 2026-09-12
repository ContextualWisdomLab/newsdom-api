import json
from pathlib import Path
import pytest

from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_dom_json(tmp_path: Path) -> Path:
    data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art_1",
                        "headline": "match Headline",
                        "body_blocks": ["Irrelevant text"]
                    },
                    {
                        "article_id": "art_2",
                        "headline": "Other News",
                        "body_blocks": ["This text has the match keyword."]
                    },
                    {
                        "article_id": "art_3",
                        "headline": "Irrelevant",
                        "body_blocks": ["Nothing here"]
                    }
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {
                        "article_id": "art_4",
                        "headline": "No keyword",
                        "body_blocks": ["Empty content"]
                    }
                ]
            }
        ]
    }
    file_path = tmp_path / "test.json"
    file_path.write_text(json.dumps(data), encoding="utf-8")
    return file_path


def test_filter_dom_logic(sample_dom_json: Path, tmp_path: Path):
    output_path = tmp_path / "filtered.json"
    filter_dom(sample_dom_json, output_path, "match")

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert "document_id" in result

    pages = result["pages"]
    assert len(pages) == 1
    assert pages[0]["page_number"] == 1

    articles = pages[0]["articles"]
    assert len(articles) == 2
    assert articles[0]["article_id"] == "art_1"
    assert articles[1]["article_id"] == "art_2"


def test_filter_dom_invalid_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        filter_dom(tmp_path / "missing.json", tmp_path / "out.json", "query")

    invalid_ext = tmp_path / "test.txt"
    invalid_ext.write_text("hello")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom(invalid_ext, tmp_path / "out.json", "query")

    invalid_json = tmp_path / "invalid.json"
    invalid_json.write_text("invalid data")
    with pytest.raises(ValueError, match="Invalid JSON"):
        filter_dom(invalid_json, tmp_path / "out.json", "query")


def test_main_cli(sample_dom_json: Path, tmp_path: Path, capsys):
    output_path = tmp_path / "out.json"
    main([str(sample_dom_json), "match", "-o", str(output_path)])

    assert output_path.exists()
    out, _ = capsys.readouterr()
    assert "successfully" in out


def test_main_cli_error(tmp_path: Path, monkeypatch):
    with pytest.raises(SystemExit) as exc_info:
        main([str(tmp_path / "missing.json"), "query", "-o", str(tmp_path / "out.json")])
    assert exc_info.value.code == 1
