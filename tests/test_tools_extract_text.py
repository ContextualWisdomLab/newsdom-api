from __future__ import annotations

import json
from pathlib import Path

import pytest
from tools import extract_text


@pytest.fixture
def mock_json_file(tmp_path: Path) -> Path:
    json_path = tmp_path / "sample.json"
    data = {
        "pages": [
            {
                "headers": ["Header Text"],
                "articles": [
                    {
                        "headline": "Headline Text",
                        "body_blocks": ["Body 1", "Body 2"],
                        "captions": [{"text": "Caption Text"}],
                        "footnotes": [{"text": "Footnote Text"}],
                        "images": [
                            {
                                "captions": [{"text": "Img Caption"}],
                                "footnotes": [{"text": "Img Footnote"}],
                            }
                        ],
                    },
                    {
                        "headline": "",
                        "body_blocks": [],
                        "captions": ["Not a dict", {"other_key": "val"}],
                        "footnotes": ["Not a dict", {"other_key": "val"}],
                        "images": [
                            {
                                "captions": ["Not a dict", {"other_key": "val"}],
                                "footnotes": ["Not a dict", {"other_key": "val"}],
                            }
                        ],
                    },
                ],
                "ads": ["Ad Text"],
                "footers": ["Footer Text"],
            }
        ]
    }
    json_path.write_text(json.dumps(data), encoding="utf-8")
    return json_path


def test_extract_text_success_stdout(mock_json_file, capsys):
    extract_text.main([str(mock_json_file)])
    out = capsys.readouterr().out
    assert "Header Text" in out
    assert "Headline Text" in out
    assert "Body 1" in out
    assert "Body 2" in out
    assert "Caption Text" in out
    assert "Footnote Text" in out
    assert "Img Caption" in out
    assert "Img Footnote" in out
    assert "Ad Text" in out
    assert "Footer Text" in out


def test_extract_text_success_file(mock_json_file, tmp_path):
    out_file = tmp_path / "out.txt"
    extract_text.main([str(mock_json_file), "-o", str(out_file)])
    out = out_file.read_text(encoding="utf-8")
    assert "Header Text" in out
    assert "Headline Text" in out
    assert "Body 1" in out
    assert "Body 2" in out
    assert "Caption Text" in out
    assert "Footnote Text" in out
    assert "Img Caption" in out
    assert "Img Footnote" in out
    assert "Ad Text" in out
    assert "Footer Text" in out


def test_extract_text_not_found(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        extract_text.main([str(tmp_path / "missing.json")])
    assert e.value.code == 1
    assert "File not found" in capsys.readouterr().err


def test_extract_text_wrong_ext(tmp_path, capsys):
    txt = tmp_path / "wrong.txt"
    txt.write_text("test", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        extract_text.main([str(txt)])
    assert e.value.code == 1
    assert "must be a .json file" in capsys.readouterr().err


def test_module_main() -> None:
    import runpy
    import sys
    from unittest.mock import patch

    sys.modules.pop("tools.extract_text", None)
    with patch("sys.argv", ["tools/extract_text.py", "-h"]):
        try:
            runpy.run_module("tools.extract_text", run_name="__main__")
        except SystemExit as excinfo:
            assert excinfo.code == 0
