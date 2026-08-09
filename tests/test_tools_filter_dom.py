from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest

from tools.filter_dom import filter_dom, main


@pytest.fixture
def valid_dom_data() -> dict:
    return {
        "document_id": "test-doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "Apple Straße opens",
                        "body_blocks": ["Camera launch details."],
                        "images": [],
                        "captions": [],
                        "footnotes": [],
                    },
                    {
                        "article_id": "art-2",
                        "headline": "Tesla stock drops",
                        "body_blocks": ["Investors review earnings."],
                        "images": [],
                        "captions": [],
                        "footnotes": [],
                    },
                ],
                "ads": [],
                "headers": [],
                "footers": [],
                "page_numbers": [],
            },
            {
                "page_number": 2,
                "articles": [
                    {
                        "article_id": "art-3",
                        "headline": "Headline 3",
                        "body_blocks": ["Second page body."],
                        "images": [],
                        "captions": [],
                        "footnotes": [],
                    }
                ],
                "ads": [],
                "headers": [],
                "footers": [],
                "page_numbers": [],
            },
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []},
    }


def _write_dom(tmp_path: Path, payload: dict) -> Path:
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(payload), encoding="utf-8")
    return input_file


def test_filter_dom_no_filters(tmp_path: Path, valid_dom_data: dict) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    result = filter_dom(input_file)

    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["articles"]) == 2


def test_filter_dom_by_pages(tmp_path: Path, valid_dom_data: dict) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    result = filter_dom(input_file, pages_to_keep=[2])

    assert len(result["pages"]) == 1
    assert result["pages"][0]["page_number"] == 2
    assert len(result["pages"][0]["articles"]) == 1


def test_filter_dom_by_articles(tmp_path: Path, valid_dom_data: dict) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    result = filter_dom(input_file, articles_to_keep=["art-1", "art-3"])

    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["articles"]) == 1
    assert result["pages"][0]["articles"][0]["article_id"] == "art-1"
    assert len(result["pages"][1]["articles"]) == 1
    assert result["pages"][1]["articles"][0]["article_id"] == "art-3"


def test_filter_dom_by_keyword_uses_unicode_casefold(
    tmp_path: Path, valid_dom_data: dict
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    result = filter_dom(input_file, keyword="STRASSE")

    assert [article["article_id"] for article in result["pages"][0]["articles"]] == [
        "art-1"
    ]
    assert result["pages"][1]["articles"] == []


def test_filter_dom_keyword_does_not_match_across_fields(
    tmp_path: Path, valid_dom_data: dict
) -> None:
    valid_dom_data["pages"][0]["articles"][0]["headline"] = "foo"
    valid_dom_data["pages"][0]["articles"][0]["body_blocks"] = ["bar"]
    input_file = _write_dom(tmp_path, valid_dom_data)

    result = filter_dom(input_file, keyword="foobar")

    assert result["pages"][0]["articles"] == []


def test_filter_dom_combines_page_article_and_keyword_filters(
    tmp_path: Path, valid_dom_data: dict
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    result = filter_dom(
        input_file,
        pages_to_keep=[1],
        articles_to_keep=["art-1", "art-2"],
        keyword="camera",
    )

    assert len(result["pages"]) == 1
    assert [article["article_id"] for article in result["pages"][0]["articles"]] == [
        "art-1"
    ]


def test_filter_dom_rejects_blank_keyword(
    tmp_path: Path, valid_dom_data: dict
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    with pytest.raises(ValueError, match="Keyword must not be blank"):
        filter_dom(input_file, keyword="   ")


def test_filter_dom_file_not_found(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_dom(non_existent)


def test_filter_dom_invalid_extension(tmp_path: Path) -> None:
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("not json", encoding="utf-8")

    with pytest.raises(ValueError, match="Input file must be a .json file"):
        filter_dom(txt_path)


def test_filter_dom_invalid_json(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_json.json"
    json_path.write_text("invalid{json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom(json_path)


def test_filter_dom_validation_error(tmp_path: Path) -> None:
    json_path = tmp_path / "invalid_schema.json"
    invalid_data = {"pages": []}
    json_path.write_text(json.dumps(invalid_data), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom(json_path)


def test_main_with_output_file(
    tmp_path: Path, valid_dom_data: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)
    output_file = tmp_path / "output.json"

    main([str(input_file), "-o", str(output_file), "--pages", "1"])

    captured = capsys.readouterr()
    assert "Filtered DOM successfully written to" in captured.out
    out_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(out_data["pages"]) == 1


def test_main_stdout(
    tmp_path: Path, valid_dom_data: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    main([str(input_file), "--articles", "art-2"])

    captured = capsys.readouterr()
    out_data = json.loads(captured.out)
    assert len(out_data["pages"]) == 2
    assert len(out_data["pages"][0]["articles"]) == 1
    assert out_data["pages"][0]["articles"][0]["article_id"] == "art-2"


def test_main_accepts_keyword_filter(
    tmp_path: Path, valid_dom_data: dict, capsys: pytest.CaptureFixture[str]
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    main([str(input_file), "--keyword", "camera"])

    captured = capsys.readouterr()
    out_data = json.loads(captured.out)
    assert [article["article_id"] for article in out_data["pages"][0]["articles"]] == [
        "art-1"
    ]


def test_main_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    non_existent = tmp_path / "missing.json"

    with pytest.raises(SystemExit) as exc_info:
        main([str(non_existent)])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON file:" in captured.err


def test_main_propagates_unexpected_errors(
    tmp_path: Path,
    valid_dom_data: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = _write_dom(tmp_path, valid_dom_data)

    def fail_unexpectedly(*args: object, **kwargs: object) -> dict:
        raise RuntimeError("implementation defect")

    monkeypatch.setattr("tools.filter_dom.filter_dom", fail_unexpectedly)

    with pytest.raises(RuntimeError, match="implementation defect"):
        main([str(input_file)])


def test_sys_path_injection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valid_dom_data: dict
) -> None:
    monkeypatch.setattr(sys, "path", [])
    json_path = _write_dom(tmp_path, valid_dom_data)
    monkeypatch.setattr(sys, "argv", ["filter_dom.py", str(json_path)])

    import warnings

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        runpy.run_module("tools.filter_dom", run_name="__main__")

    expected_src = str(Path(__file__).resolve().parents[1] / "src")
    assert sys.path[0] == expected_src
