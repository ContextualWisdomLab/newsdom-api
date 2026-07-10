from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

# To ensure the path manipulation in the tool doesn't cause issues during testing
# or leave global side-effects, we mock sys.argv and import explicitly.
import tools.validate_dom as validate_dom


@pytest.fixture
def valid_json_path(tmp_path: Path) -> Path:
    p = tmp_path / "valid.json"
    p.write_text(
        """
        {
            "document_id": "test_doc",
            "pages": [],
            "quality": {"status": "success", "parser": "mineru", "warnings": []}
        }
        """,
        encoding="utf-8",
    )
    return p


@pytest.fixture
def invalid_json_path(tmp_path: Path) -> Path:
    p = tmp_path / "invalid.json"
    p.write_text(
        """
        {
            "document_id": 1234,
            "pages": "not_a_list"
        }
        """,
        encoding="utf-8",
    )
    return p


@pytest.fixture
def malformed_json_path(tmp_path: Path) -> Path:
    p = tmp_path / "malformed.json"
    p.write_text("{ this is not valid json", encoding="utf-8")
    return p


def test_validate_json_file_valid(valid_json_path: Path) -> None:
    assert validate_dom.validate_json_file(valid_json_path) is True


def test_validate_json_file_invalid(
    invalid_json_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert validate_dom.validate_json_file(invalid_json_path) is False
    captured = capsys.readouterr()
    assert "Validation failed" in captured.err


def test_validate_json_file_malformed(
    malformed_json_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert validate_dom.validate_json_file(malformed_json_path) is False
    captured = capsys.readouterr()
    assert "Validation failed" in captured.err


def test_validate_directory(tmp_path: Path) -> None:
    # Setup dir
    (tmp_path / "valid1.json").write_text('{"document_id": "doc1"}', encoding="utf-8")
    (tmp_path / "valid2.json").write_text('{"document_id": "doc2"}', encoding="utf-8")
    (tmp_path / "invalid.json").write_text('{"document_id": 123}', encoding="utf-8")
    (tmp_path / "not_json.txt").write_text("ignore me", encoding="utf-8")

    total, passed = validate_dom.validate_directory(tmp_path)
    assert total == 3
    assert passed == 2


def test_main_file_valid(
    valid_json_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("sys.argv", ["validate_dom.py", str(valid_json_path)]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Valid." in captured.out


def test_main_file_invalid(
    invalid_json_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("sys.argv", ["validate_dom.py", str(invalid_json_path)]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 1


def test_main_dir_without_recursive(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with patch("sys.argv", ["validate_dom.py", str(tmp_path)]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Use -r/--recursive" in captured.err


def test_main_dir_recursive_all_valid(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "valid.json").write_text('{"document_id": "doc1"}', encoding="utf-8")
    with patch("sys.argv", ["validate_dom.py", str(tmp_path), "-r"]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "All files are valid" in captured.out


def test_main_dir_recursive_some_invalid(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "valid.json").write_text('{"document_id": "doc1"}', encoding="utf-8")
    (tmp_path / "invalid.json").write_text('{"document_id": 123}', encoding="utf-8")
    with patch("sys.argv", ["validate_dom.py", str(tmp_path), "-r"]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Total files: 2" in captured.out
    assert "Passed: 1" in captured.out


def test_main_path_not_exist(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    not_exist = tmp_path / "does_not_exist.json"
    with patch("sys.argv", ["validate_dom.py", str(not_exist)]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Input path does not exist" in captured.err


def test_main_file_not_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    txt_file = tmp_path / "test.txt"
    txt_file.touch()
    with patch("sys.argv", ["validate_dom.py", str(txt_file)]):
        with pytest.raises(SystemExit) as exc:
            validate_dom.main()
        assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Input must be a .json file" in captured.err


def test_main_invalid_input_path(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A path that is neither file nor dir, e.g. a socket or block device
    # We simulate this by mocking is_file and is_dir to return False
    valid_file = tmp_path / "valid.json"
    valid_file.touch()
    with patch("sys.argv", ["validate_dom.py", str(valid_file)]):
        with patch("pathlib.Path.is_file", return_value=False):
            with patch("pathlib.Path.is_dir", return_value=False):
                with pytest.raises(SystemExit) as exc:
                    validate_dom.main()
                assert exc.value.code == 1
    captured = capsys.readouterr()
    assert "Invalid input path" in captured.err
