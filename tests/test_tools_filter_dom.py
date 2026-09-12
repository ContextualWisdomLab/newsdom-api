from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import filter_dom

@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    data = {
        "document_id": "test_doc",
        "quality": {"status": "success", "parser": "test"},
        "pages": [
            {
                "page_number": 1,
                "articles": [],
                "ads": ["ad1", "ad2"]
            },
            {
                "page_number": 2,
                "articles": [],
                "ads": ["ad3"]
            }
        ]
    }
    p = tmp_path / "sample.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p

def test_filter_dom_pages(sample_json):
    result = filter_dom.filter_dom(sample_json, pages_to_keep=[1])
    assert len(result["pages"]) == 1
    assert result["pages"][0]["page_number"] == 1
    assert len(result["pages"][0]["ads"]) == 2

def test_filter_dom_remove_ads(sample_json):
    result = filter_dom.filter_dom(sample_json, remove_ads=True)
    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["ads"]) == 0
    assert len(result["pages"][1]["ads"]) == 0

def test_filter_dom_both(sample_json):
    result = filter_dom.filter_dom(sample_json, pages_to_keep=[2], remove_ads=True)
    assert len(result["pages"]) == 1
    assert result["pages"][0]["page_number"] == 2
    assert len(result["pages"][0]["ads"]) == 0

def test_filter_dom_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        filter_dom.filter_dom(tmp_path / "not_found.json")

def test_filter_dom_wrong_ext(tmp_path):
    p = tmp_path / "wrong.txt"
    p.write_text("test")
    with pytest.raises(ValueError, match="must be a .json file"):
        filter_dom.filter_dom(p)

def test_filter_dom_invalid_json(tmp_path):
    p = tmp_path / "invalid.json"
    p.write_text("{invalid")
    with pytest.raises(ValueError, match="Invalid JSON file"):
        filter_dom.filter_dom(p)

def test_filter_dom_invalid_schema(tmp_path):
    p = tmp_path / "schema.json"
    p.write_text(json.dumps({"invalid": "schema"}))
    with pytest.raises(ValueError, match="does not match ParseResponse schema"):
        filter_dom.filter_dom(p)

def test_main_success(sample_json, tmp_path, capsys):
    out_file = tmp_path / "out.json"
    filter_dom.main([str(sample_json), "-o", str(out_file), "-p", "1", "--remove-ads"])

    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert len(data["pages"]) == 1
    assert data["pages"][0]["page_number"] == 1
    assert len(data["pages"][0]["ads"]) == 0

    out = capsys.readouterr().out
    assert f"Filtered DOM written to {out_file}" in out

def test_main_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        filter_dom.main([str(tmp_path / "not_found.json"), "-o", str(tmp_path / "out.json")])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "Error:" in err


def test_sys_path_insertion(tmp_path):
    import sys
    from importlib import reload
    import tools.filter_dom

    # Store original path
    original_path = list(sys.path)

    # Remove _SRC_ROOT from sys.path to force the if statement to execute
    src_root = str(Path(__file__).resolve().parents[1] / "src")
    if src_root in sys.path:
        sys.path.remove(src_root)

    try:
        # Reload the module to execute the if statement
        reload(tools.filter_dom)
        assert src_root in sys.path
    finally:
        # Restore original path
        sys.path = original_path
