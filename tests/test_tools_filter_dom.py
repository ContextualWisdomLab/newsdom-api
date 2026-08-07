from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools.filter_dom import filter_dom, main


@pytest.fixture
def sample_json_data() -> dict:
    return {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "Apple releases new iPhone",
                        "body_blocks": ["The new phone features a great camera."]
                    },
                    {
                        "headline": "Tesla stock drops",
                        "body_blocks": ["Investors are worried about the recent earnings report."]
                    }
                ]
            }
        ]
    }


def test_filter_dom(tmp_path: Path, sample_json_data: dict) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

    filter_dom(input_file, "apple", output_file)

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    articles = output_data["pages"][0]["articles"]
    assert len(articles) == 1
    assert "Apple" in articles[0]["headline"]


def test_filter_dom_no_match(tmp_path: Path, sample_json_data: dict) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

    filter_dom(input_file, "microsoft", output_file)

    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    articles = output_data["pages"][0]["articles"]
    assert len(articles) == 0


def test_filter_dom_file_not_found(tmp_path: Path) -> None:
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"
    with pytest.raises(FileNotFoundError):
        filter_dom(input_file, "apple", output_file)


def test_filter_dom_not_json(tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("not json", encoding="utf-8")
    output_file = tmp_path / "output.json"
    with pytest.raises(ValueError):
        filter_dom(input_file, "apple", output_file)


def test_main(tmp_path: Path, sample_json_data: dict, capsys: pytest.CaptureFixture[str]) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")

    main([str(input_file), "-o", str(output_file), "-k", "tesla"])

    captured = capsys.readouterr()
    assert f"Filtered JSON successfully written to {output_file}" in captured.out


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), "-o", str(output_file), "-k", "apple"])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err

def test_filter_dom_blank_keyword(tmp_path: Path, sample_json_data: dict) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_text(json.dumps(sample_json_data), encoding="utf-8")
    with pytest.raises(ValueError, match="Keyword must not be blank"):
        filter_dom(input_file, "   ", output_file)

def test_filter_dom_casefold(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    data = {
        "pages": [{"articles": [{"headline": "Straße eröffnet", "body_blocks": ["Heute."]}]}]
    }
    input_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    filter_dom(input_file, "STRASSE", output_file)
    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(output_data["pages"][0]["articles"]) == 1

def test_filter_dom_no_cross_field_match(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    data = {
        "pages": [{"articles": [{"headline": "foo", "body_blocks": ["bar"]}]}]
    }
    input_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    filter_dom(input_file, "foobar", output_file)
    output_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(output_data["pages"][0]["articles"]) == 0
