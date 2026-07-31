from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import pretty_print_dom


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "empty_dict": {},
        "empty_list": [],
        "string": "this is a long string that should be truncated because it is more than fifty characters long",
        "nested": {"list": [1, 2]},
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_pretty_print_dom_success(mock_json_file, capsys):
    pretty_print_dom.main([str(mock_json_file)])
    out = capsys.readouterr().out
    assert "NewsDOM Root" in out
    assert "empty_dict: {}" in out
    assert "empty_list: []" in out
    assert "this is a long string that should be truncated ..." in out
    assert "nested:" in out
    assert "[0]: 1" in out


def test_print_tree_primitives():
    # Helper direct test
    pretty_print_dom._print_tree({"a": 1, "b": [2]})
    pretty_print_dom._print_tree([1, {"a": 2}])
    # Edge cases
    pretty_print_dom._print_tree({})
    pretty_print_dom._print_tree([])


def test_pretty_print_dom_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        pretty_print_dom.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "not found" in capsys.readouterr().err


def test_pretty_print_dom_invalid_json(tmp_path, capsys):
    txt = tmp_path / "invalid.json"
    txt.write_text("invalid json", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        pretty_print_dom.main([str(txt)])
    assert e.value.code == 1
    assert "Error decoding JSON" in capsys.readouterr().err
