from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import minify_dom


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {"pages": [{"articles": [{"body_blocks": ["text1", "text2"]}]}]}
    # Write with indentation to test minification
    json_path.write_text(json.dumps(data, indent=4), encoding="utf-8")
    return json_path


def test_minify_dom_overwrite_success(mock_json_file, capsys):
    original_size = mock_json_file.stat().st_size
    minify_dom.main([str(mock_json_file)])
    out = capsys.readouterr().out

    assert "successfully minified to" in out

    minified_size = mock_json_file.stat().st_size
    assert minified_size < original_size

    # Ensure it's still valid JSON
    data = json.loads(mock_json_file.read_bytes())
    assert data["pages"][0]["articles"][0]["body_blocks"][0] == "text1"


def test_minify_dom_output_param_success(mock_json_file, tmp_path, capsys):
    out_path = tmp_path / "minified.json"
    minify_dom.main([str(mock_json_file), "-o", str(out_path)])

    out = capsys.readouterr().out
    assert f"successfully minified to {out_path}" in out

    assert out_path.exists()
    assert out_path.stat().st_size < mock_json_file.stat().st_size


def test_minify_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        minify_dom.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_minify_dom_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        minify_dom.main([str(txt)])
    assert e.value.code == 1
    assert "must be a .json file" in capsys.readouterr().err


def test_minify_dom_invalid_json(tmp_path, capsys):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{bad json", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        minify_dom.main([str(bad_json)])
    assert e.value.code == 1
    assert "Invalid JSON file" in capsys.readouterr().err
