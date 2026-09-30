import json
import os
import pytest
from pathlib import Path
from tools.filter_dom import filter_dom, main


def test_filter_dom_success(tmp_path: Path):
    """Verify test_filter_dom_success."""
    input_data = {
        "document_id": "test_doc",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "headline": "Match this",
                        "body_blocks": ["no match here"]
                    },
                    {
                        "headline": "No match",
                        "body_blocks": ["but Match this body"]
                    },
                    {
                        "headline": "Ignore",
                        "body_blocks": ["ignore this too"]
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "Match")

    assert output_file.exists()
    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))

    assert "pages" in filtered_data
    assert len(filtered_data["pages"]) == 1
    assert len(filtered_data["pages"][0]["articles"]) == 2

    articles = filtered_data["pages"][0]["articles"]
    assert articles[0]["headline"] == "Match this"
    assert articles[0]["document_id"] == "test_doc"
    assert articles[0]["page_number"] == 1

    assert articles[1]["headline"] == "No match"
    assert articles[1]["document_id"] == "test_doc"
    assert articles[1]["page_number"] == 1


def test_filter_dom_same_file_error(tmp_path: Path):
    """Verify test_filter_dom_same_file_error."""
    input_file = tmp_path / "input.json"
    input_file.touch()

    with pytest.raises(ValueError, match="Input and output paths must not be the same file."):
        filter_dom(input_file, input_file, "query")


def test_filter_dom_not_json(tmp_path: Path):
    """Verify test_filter_dom_not_json."""
    input_file = tmp_path / "input.txt"
    input_file.touch()
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match=r"Input file must be a \.json file\."):
        filter_dom(input_file, output_file, "query")


def test_filter_dom_not_found(tmp_path: Path):
    """Verify test_filter_dom_not_found."""
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(FileNotFoundError):
        filter_dom(input_file, output_file, "query")


def test_filter_dom_invalid_json(tmp_path: Path):
    """Verify test_filter_dom_invalid_json."""
    input_file = tmp_path / "input.json"
    input_file.write_text("invalid json", encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Invalid JSON file:"):
        filter_dom(input_file, output_file, "query")


def test_filter_dom_not_dict_root(tmp_path: Path):
    """Verify test_filter_dom_not_dict_root."""
    input_file = tmp_path / "input.json"
    input_file.write_text("[]", encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Root of JSON must be an object."):
        filter_dom(input_file, output_file, "query")


def test_filter_dom_nan_constant_error(tmp_path: Path):
    """Verify test_filter_dom_nan_constant_error."""
    input_file = tmp_path / "input.json"
    input_file.write_text('{"val": NaN}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Strict JSON parsing rejected non-standard constant"):
        filter_dom(input_file, output_file, "query")


def test_main_success(tmp_path: Path, capsys):
    """Verify test_main_success."""
    input_file = tmp_path / "input.json"
    input_file.write_text('{"document_id": "test", "pages": []}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    main([str(input_file), str(output_file), "query"])
    captured = capsys.readouterr()
    assert "Filtered JSON successfully written to" in captured.out


def test_main_error(tmp_path: Path, capsys):
    """Verify test_main_error."""
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), str(output_file), "query"])

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error filtering JSON" in captured.err


def test_filter_dom_empty_and_invalid_types(tmp_path: Path):
    """Verify test_filter_dom_empty_and_invalid_types."""
    # Test handling of invalid types that should be safely ignored
    input_data = {
        "pages": [
            "not a dict",
            {
                "page_number": 2,
                "articles": "not a list"
            },
            {
                "page_number": 3,
                "articles": [
                    "not a dict",
                    {
                        "headline": ["not a string"],
                        "body_blocks": "not a list"
                    },
                    {
                        "headline": "match",
                        "body_blocks": [123] # not a string
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "match")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(filtered_data["pages"]) == 1
    assert len(filtered_data["pages"][0]["articles"]) == 1
    assert filtered_data["pages"][0]["articles"][0]["headline"] == "match"

def test_filter_dom_replace_error(tmp_path: Path, monkeypatch):
    """Verify test_filter_dom_replace_error."""
    input_file = tmp_path / "input.json"
    input_file.write_text('{"pages": []}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    def mock_replace(*args, **kwargs):
        raise OSError("Mock replace error")

    monkeypatch.setattr(os, "replace", mock_replace)

    with pytest.raises(OSError, match="Mock replace error"):
        filter_dom(input_file, output_file, "query")

def test_filter_dom_coverage_edges(tmp_path: Path):
    """Verify test_filter_dom_coverage_edges."""
    input_data = {
        "pages": [
            {
                "articles": [
                    {
                        # Not a string headline
                        "headline": 123,
                        # No body blocks list
                        "body_blocks": None
                    },
                    {
                        "headline": "match string",
                        # document_id and page_number already present
                        "document_id": "existing_doc",
                        "page_number": 42
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "match")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    articles = filtered_data["pages"][0]["articles"]
    assert articles[0]["document_id"] == "existing_doc"
    assert articles[0]["page_number"] == 42


def test_filter_dom_not_list_pages(tmp_path: Path):
    """Verify test_filter_dom_not_list_pages."""
    input_data = {"pages": "not a list"}
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "query")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert filtered_data["pages"] == []

def test_filter_dom_not_list_articles(tmp_path: Path):
    """Verify test_filter_dom_not_list_articles."""
    input_data = {"pages": [{"articles": "not a list"}]}
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "query")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert filtered_data["pages"] == []

def test_filter_dom_break_body_blocks(tmp_path: Path):
    """Verify test_filter_dom_break_body_blocks."""
    input_data = {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "No match",
                        "body_blocks": ["match 1", "match 2"]
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "match")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(filtered_data["pages"]) == 1

def test_filter_dom_unlink_error(tmp_path: Path, monkeypatch):
    """Verify test_filter_dom_unlink_error."""
    input_file = tmp_path / "input.json"
    input_file.write_text('{"pages": []}', encoding="utf-8")
    output_file = tmp_path / "output.json"

    def mock_replace(*args, **kwargs):
        raise OSError("Mock replace error")

    def mock_unlink(*args, **kwargs):
        raise OSError("Mock unlink error")

    monkeypatch.setattr(os, "replace", mock_replace)
    monkeypatch.setattr(os, "unlink", mock_unlink)

    with pytest.raises(OSError, match="Mock replace error"):
        filter_dom(input_file, output_file, "query")

def test_filter_dom_no_articles(tmp_path: Path):
    """Verify test_filter_dom_no_articles."""
    input_data = {
        "pages": [
            {
                "articles": []
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "match")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(filtered_data["pages"]) == 0

def test_filter_dom_no_body_blocks_and_no_headline_but_with_string_match(tmp_path: Path):
    """Verify test_filter_dom_no_body_blocks_and_no_headline_but_with_string_match."""
    input_data = {
        "pages": [
            {
                "articles": [
                    {
                        "foo": "bar",
                        "headline": "match"
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "match")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(filtered_data["pages"]) == 1

def test_filter_dom_match_body_block_break(tmp_path: Path):
    """Verify test_filter_dom_match_body_block_break."""
    input_data = {
        "pages": [
            {
                "articles": [
                    {
                        "headline": "No",
                        "body_blocks": ["match here", "match also here"]
                    }
                ]
            }
        ]
    }
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(input_data), encoding="utf-8")
    output_file = tmp_path / "output.json"

    filter_dom(input_file, output_file, "match")

    filtered_data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(filtered_data["pages"]) == 1
