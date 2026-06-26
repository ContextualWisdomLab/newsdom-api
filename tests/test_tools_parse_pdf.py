from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tools import parse_pdf


@pytest.fixture
def mock_pdf_file(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"dummy pdf content")
    return pdf_path


@patch("tools.parse_pdf.parse_pdf_bytes")
def test_parse_pdf_success_stdout(mock_parse, mock_pdf_file, capsys):
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"status": "ok", "pages": []}
    mock_parse.return_value = mock_response

    parse_pdf.main([str(mock_pdf_file)])

    out = capsys.readouterr().out
    res = json.loads(out)
    assert res["status"] == "ok"
    mock_parse.assert_called_once_with(b"dummy pdf content", filename="sample.pdf")


@patch("tools.parse_pdf.parse_pdf_bytes")
def test_parse_pdf_success_file_output(mock_parse, mock_pdf_file, tmp_path, capsys):
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {"status": "ok", "pages": []}
    mock_parse.return_value = mock_response

    out_path = tmp_path / "out.json"

    parse_pdf.main([str(mock_pdf_file), "-o", str(out_path)])

    out = capsys.readouterr().out
    assert "Output written to" in out

    res = json.loads(out_path.read_text())
    assert res["status"] == "ok"


def test_parse_pdf_file_not_found(tmp_path, capsys):
    missing_file = tmp_path / "missing.pdf"

    with pytest.raises(SystemExit) as e:
        parse_pdf.main([str(missing_file)])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "does not exist or is not a file" in err


def test_parse_pdf_rejects_parent_directory_segments(tmp_path, capsys):
    traversal_path = tmp_path / "nested" / ".." / "sample.pdf"

    with pytest.raises(SystemExit) as e:
        parse_pdf.main([str(traversal_path)])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "must not contain parent directory segments" in err


def test_parse_pdf_rejects_non_pdf_extension(tmp_path, capsys):
    txt_path = tmp_path / "sample.txt"
    txt_path.write_text("not a pdf")

    with pytest.raises(SystemExit) as e:
        parse_pdf.main([str(txt_path)])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "must use a .pdf extension" in err


@patch("tools.parse_pdf.parse_pdf_bytes")
def test_parse_pdf_exception(mock_parse, mock_pdf_file, capsys):
    mock_parse.side_effect = Exception("Mock parsing error")

    with pytest.raises(SystemExit) as e:
        parse_pdf.main([str(mock_pdf_file)])

    assert e.value.code == 1
    err = capsys.readouterr().err
    assert "Mock parsing error" in err


def test_parse_pdf_main_block(monkeypatch, capsys):
    script_path = Path(__file__).resolve().parents[1] / "tools" / "parse_pdf.py"
    monkeypatch.setattr(sys, "argv", [str(script_path), "--help"])

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(script_path), run_name="__main__")

    assert exc_info.value.code == 0
    assert "Parse a Japanese newspaper PDF" in capsys.readouterr().out


def test_sys_path_insertion():
    import sys
    from pathlib import Path
    import importlib

    # Store original sys.path
    original_sys_path = sys.path[:]

    # Remove the src path if it's there
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    if str(_SRC_ROOT) in sys.path:
        sys.path.remove(str(_SRC_ROOT))

    try:
        importlib.reload(parse_pdf)
    finally:
        sys.path = original_sys_path
        importlib.reload(parse_pdf)


def test_sys_path_insertion_not_in_path():
    import sys
    from pathlib import Path
    import importlib

    # Store original sys.path
    original_sys_path = sys.path[:]

    # Remove the src path if it's there
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    # Ensure it's not in sys.path
    while str(_SRC_ROOT) in sys.path:
        sys.path.remove(str(_SRC_ROOT))

    try:
        importlib.reload(parse_pdf)
    finally:
        sys.path = original_sys_path
        importlib.reload(parse_pdf)


def test_sys_path_insertion_already_in_path():
    import sys
    from pathlib import Path
    import importlib

    # Store original sys.path
    original_sys_path = sys.path[:]

    # Remove the src path if it's there
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    # Ensure it is in sys.path
    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))

    try:
        importlib.reload(parse_pdf)
    finally:
        sys.path = original_sys_path
        importlib.reload(parse_pdf)


def test_sys_path_insertion_already_in_path_force_not():
    import sys
    from pathlib import Path
    import importlib

    # Store original sys.path
    original_sys_path = sys.path[:]

    # Remove the src path if it's there
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    # Ensure it is NOT in sys.path so we trigger the other branch too
    while str(_SRC_ROOT) in sys.path:
        sys.path.remove(str(_SRC_ROOT))

    try:
        importlib.reload(parse_pdf)
    finally:
        sys.path = original_sys_path
        importlib.reload(parse_pdf)


def test_sys_path_insertion_already_in_path_force_not2():
    import sys
    from pathlib import Path
    import importlib
    import tools.parse_pdf as parse_pdf

    # Store original sys.path
    original_sys_path = sys.path[:]

    # Remove the src path if it's there
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    # Ensure it is in sys.path
    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))

    try:
        importlib.reload(parse_pdf)
    finally:
        sys.path = original_sys_path
        importlib.reload(parse_pdf)


def test_sys_path_insertion_already_in_path_force_not3():
    import sys
    from pathlib import Path
    import importlib
    import tools.parse_pdf as parse_pdf

    # Store original sys.path
    original_sys_path = sys.path[:]

    # Remove the src path if it's there
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"

    # Ensure it is NOT in sys.path
    while str(_SRC_ROOT) in sys.path:
        sys.path.remove(str(_SRC_ROOT))

    try:
        importlib.reload(parse_pdf)
    finally:
        sys.path = original_sys_path
        importlib.reload(parse_pdf)
