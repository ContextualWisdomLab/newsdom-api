import json
from pathlib import Path
import pytest
from tools.filter_dom import filter_dom, main

def test_filter_dom_success(tmp_path: Path) -> None:
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"

    data = {
        "pages": [
            {
                "articles": [
                    {"headline": "Match query here", "body_blocks": []},
                    {"headline": "No match", "body_blocks": ["Nothing here either"]},
                    {"headline": "Another one", "body_blocks": ["Body block with query here"]},
                ]
            }
        ]
    }
    in_file.write_text(json.dumps(data), encoding="utf-8")

    filter_dom(in_file, "query", out_file)

    out_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert len(out_data["pages"][0]["articles"]) == 2
    assert out_data["pages"][0]["articles"][0]["headline"] == "Match query here"
    assert out_data["pages"][0]["articles"][1]["headline"] == "Another one"


def test_filter_dom_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_dom(tmp_path / "does_not_exist.json", "query", tmp_path / "out.json")


def test_filter_dom_invalid_extension(tmp_path: Path) -> None:
    in_file = tmp_path / "in.txt"
    in_file.write_text("not json")
    with pytest.raises(ValueError, match=r"File must be a \.json file\."):
        filter_dom(in_file, "query", tmp_path / "out.json")


def test_filter_dom_invalid_json(tmp_path: Path) -> None:
    in_file = tmp_path / "in.json"
    in_file.write_text("{not json}", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file:"):
        filter_dom(in_file, "query", tmp_path / "out.json")


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    in_file = tmp_path / "in.json"
    out_file = tmp_path / "out.json"

    data = {"pages": [{"articles": [{"headline": "Match query here", "body_blocks": []}]}]}
    in_file.write_text(json.dumps(data), encoding="utf-8")

    main([str(in_file), "query", str(out_file)])

    captured = capsys.readouterr()
    assert f"Filtered DOM saved to {out_file}" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    in_file = tmp_path / "in.json"
    # invalid json
    in_file.write_text("{not json}", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        main([str(in_file), "query", str(tmp_path / "out.json")])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Invalid JSON file:" in captured.err
