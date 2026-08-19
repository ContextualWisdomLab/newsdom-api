from __future__ import annotations

import json
from pathlib import Path
import sys
import subprocess
from unittest.mock import patch
import os

import pytest
from tools.filter_dom import filter_dom, main


def test_filter_dom_success(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"headline": "Breaking News: Apple announces new iPhone"},
                    {"headline": "Banana prices drop"},
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {"headline": "Apple pie recipe"},
                    {"headline": None},
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data))

    filter_dom(input_file, output_file, "apple")

    result = json.loads(output_file.read_text())

    assert len(result["pages"]) == 2
    assert len(result["pages"][0]["articles"]) == 1
    assert result["pages"][0]["articles"][0]["headline"] == "Breaking News: Apple announces new iPhone"

    assert len(result["pages"][1]["articles"]) == 1
    assert result["pages"][1]["articles"][0]["headline"] == "Apple pie recipe"


def test_filter_dom_no_matches(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    data = {
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"headline": "Breaking News: Apple announces new iPhone"},
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data))

    filter_dom(input_file, output_file, "banana")

    result = json.loads(output_file.read_text())

    assert len(result["pages"]) == 0


def test_filter_dom_file_not_found(tmp_path: Path) -> None:
    input_file = tmp_path / "nonexistent.json"
    output_file = tmp_path / "output.json"

    with pytest.raises(FileNotFoundError, match="File not found or is not a file"):
        filter_dom(input_file, output_file, "apple")


def test_filter_dom_invalid_extension(tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("dummy text")
    output_file = tmp_path / "output.json"

    with pytest.raises(ValueError, match="Input file must be a .json file."):
        filter_dom(input_file, output_file, "apple")


@patch("tools.filter_dom.filter_dom")
def test_main_success(mock_filter_dom, tmp_path: Path, capsys) -> None:
    input_file = tmp_path / "in.json"
    output_file = tmp_path / "out.json"

    main([str(input_file), str(output_file), "--keyword", "apple"])

    mock_filter_dom.assert_called_once_with(input_file, output_file, "apple")
    assert "Filtering complete. Filtered DOM saved to" in capsys.readouterr().out


@patch("tools.filter_dom.filter_dom")
def test_main_error(mock_filter_dom, tmp_path: Path, capsys) -> None:
    input_file = tmp_path / "in.json"
    output_file = tmp_path / "out.json"

    mock_filter_dom.side_effect = Exception("Mocked error")

    with pytest.raises(SystemExit) as exc_info:
        main([str(input_file), str(output_file), "--keyword", "apple"])

    assert exc_info.value.code == 1
    assert "Error: Mocked error" in capsys.readouterr().err


def test_filter_dom_module_help() -> None:
    env = {
        **os.environ,
        "PYTHONPATH": str(Path.cwd() / "src"),
    }
    result = subprocess.run(
        [sys.executable, "-m", "tools.filter_dom", "--help"],
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.returncode == 0
    assert "--keyword" in result.stdout
