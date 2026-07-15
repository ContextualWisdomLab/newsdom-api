from pathlib import Path
import json
import pytest
from tools.filter_dom import filter_dom, main


def test_filter_dom_valid(tmp_path: Path):
    input_json = tmp_path / "test.json"
    data = {
        "pages": [
            {
                "articles": [
                    {"headline": "test keyword", "body_blocks": []},
                    {"headline": "other", "body_blocks": ["no match here"]},
                ]
            }
        ]
    }
    input_json.write_text(json.dumps(data))

    result = filter_dom(input_json, "keyword")
    assert len(result["pages"][0]["articles"]) == 1
    assert result["pages"][0]["articles"][0]["headline"] == "test keyword"


def test_filter_dom_not_found():
    with pytest.raises(FileNotFoundError):
        filter_dom(Path("not_found.json"), "key")


def test_filter_dom_wrong_ext(tmp_path: Path):
    wrong = tmp_path / "test.txt"
    wrong.write_text("{}")
    with pytest.raises(ValueError, match="File must be a .json file."):
        filter_dom(wrong, "key")


def test_main_filter(tmp_path: Path, capsys):
    input_json = tmp_path / "test.json"
    out_json = tmp_path / "out.json"
    data = {"pages": [{"articles": [{"headline": "key", "body_blocks": []}]}]}
    input_json.write_text(json.dumps(data))

    main([str(input_json), "key", "--output", str(out_json)])
    assert out_json.exists()

    main([str(input_json), "key"])
    captured = capsys.readouterr()
    assert "key" in captured.out


def test_main_filter_error(capsys):
    with pytest.raises(SystemExit):
        main(["not_found.json", "key"])
    captured = capsys.readouterr()
    assert "Error:" in captured.err
def test_filter_dom_match_body(tmp_path: Path):
    input_json = tmp_path / "test.json"
    data = {
        "pages": [
            {
                "articles": [
                    {"headline": "test", "body_blocks": ["find this keyword"]},
                    {"headline": "test2", "body_blocks": []}
                ]
            },
            {
                "articles": []
            }
        ]
    }
    input_json.write_text(json.dumps(data))

    result = filter_dom(input_json, "keyword")
    assert len(result["pages"]) == 1
    assert len(result["pages"][0]["articles"]) == 1
    assert result["pages"][0]["articles"][0]["headline"] == "test"
