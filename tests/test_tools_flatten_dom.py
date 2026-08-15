from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import flatten_dom


@pytest.fixture
def valid_dom_json(tmp_path: Path) -> Path:
    json_path = tmp_path / "valid.json"
    data = {
        "document_id": "doc-123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {
                        "article_id": "art-1",
                        "headline": "Test Headline",
                        "body_blocks": ["Block 1", "  ", "Block 2"],
                        "images": [
                            {
                                "path": "images/test.jpg",
                                "captions": [{"text": "Image Cap"}],
                                "footnotes": [{"text": "Image FN"}]
                            }
                        ],
                        "captions": [{"text": "Caption 1"}],
                        "footnotes": [{"text": "Footnote 1"}]
                    },
                    {
                        "article_id": "art-2",
                        "headline": "  ",
                        "body_blocks": [],
                        "images": [],
                        "captions": [{"text": ""}],
                        "footnotes": [{"text": ""}]
                    }
                ]
            }
        ],
        "quality": {"status": "success", "parser": "mineru", "warnings": []}
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


@pytest.fixture
def invalid_dom_json(tmp_path: Path) -> Path:
    json_path = tmp_path / "invalid.json"
    data = {"wrong_schema": True}
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_sys_path_insertion(monkeypatch):
    """Test the sys.path insertion logic."""
    import sys
    import importlib

    # Use monkeypatch to safely simulate an empty sys.path
    monkeypatch.setattr(sys, "path", [])

    # Import the script - we need to reload it to trigger the module-level code
    import tools.flatten_dom
    importlib.reload(tools.flatten_dom)

    # Verify src was inserted
    src_root = str(Path(tools.flatten_dom.__file__).resolve().parents[1] / "src")
    assert sys.path[0] == src_root


def test_flatten_dom_success(valid_dom_json):
    results = flatten_dom.flatten_dom(valid_dom_json)

    # Filtering out empty chunks: headline(1), body_blocks(2 out of 3), image_cap(1), image_fn(1), caption(1), footnote(1) = 7
    assert len(results) == 7
    assert results[0]["type"] == "headline"
    assert results[0]["text"] == "Test Headline"
    assert results[0]["pointer"] == "#/pages/0/articles/0/headline"

    assert results[1]["type"] == "body_block"
    assert results[1]["text"] == "Block 1"
    assert results[1]["pointer"] == "#/pages/0/articles/0/body_blocks/0"

    assert results[2]["type"] == "body_block"
    assert results[2]["text"] == "Block 2"
    assert results[2]["pointer"] == "#/pages/0/articles/0/body_blocks/2"

    assert results[3]["type"] == "image_caption"
    assert results[3]["text"] == "Image Cap"
    assert results[3]["image_path"] == "images/test.jpg"
    assert results[3]["pointer"] == "#/pages/0/articles/0/images/0/captions/0"

    assert results[4]["type"] == "image_footnote"
    assert results[4]["text"] == "Image FN"
    assert results[4]["pointer"] == "#/pages/0/articles/0/images/0/footnotes/0"

    assert results[5]["type"] == "caption"
    assert results[5]["text"] == "Caption 1"
    assert results[5]["pointer"] == "#/pages/0/articles/0/captions/0"

    assert results[6]["type"] == "footnote"
    assert results[6]["text"] == "Footnote 1"
    assert results[6]["pointer"] == "#/pages/0/articles/0/footnotes/0"

    for res in results:
        assert res["document_id"] == "doc-123"
        assert res["page_number"] == 1
        assert res["article_id"] == "art-1"
        assert res["parser"] == "mineru"


def test_flatten_dom_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="File not found"):
        flatten_dom.flatten_dom(tmp_path / "missing.json")


def test_flatten_dom_wrong_ext(tmp_path):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(ValueError, match=r"must be a \.json file"):
        flatten_dom.flatten_dom(txt)


def test_flatten_dom_invalid_json(tmp_path):
    json_path = tmp_path / "bad.json"
    json_path.write_text("{bad json", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        flatten_dom.flatten_dom(json_path)


def test_flatten_dom_validation_error(invalid_dom_json):
    with pytest.raises(ValueError, match="Schema validation failed"):
        flatten_dom.flatten_dom(invalid_dom_json)


def test_main_stdout(valid_dom_json, capsys):
    flatten_dom.main([str(valid_dom_json)])
    out = capsys.readouterr().out
    assert "doc-123" in out
    assert "Test Headline" in out
    assert "#/pages/0/articles/0/body_blocks/2" in out


def test_main_output_file(valid_dom_json, tmp_path):
    out_file = tmp_path / "out.jsonl"
    flatten_dom.main([str(valid_dom_json), "--output", str(out_file)])
    lines = out_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 7
    assert "Test Headline" in lines[0]


def test_main_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        flatten_dom.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err
