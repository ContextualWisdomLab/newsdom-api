import json
import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from tools.export_jsonl import export_jsonl, main

def test_export_jsonl_success(tmp_path: Path):
    """Export every article with its document and page identifiers."""

    input_file = tmp_path / "test.json"
    output_file = tmp_path / "test.jsonl"

    data = {
        "document_id": "doc123",
        "pages": [
            {
                "page_number": 1,
                "articles": [
                    {"article_id": "a1", "headline": "H1"},
                    {"article_id": "a2", "headline": "H2"}
                ]
            },
            {
                "page_number": 2,
                "articles": [
                    {"article_id": "a3", "headline": "H3"}
                ]
            }
        ]
    }
    input_file.write_text(json.dumps(data), encoding="utf-8")

    export_jsonl(input_file, output_file)

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3

    parsed_lines = [json.loads(line) for line in lines]
    assert parsed_lines[0] == {"article_id": "a1", "headline": "H1", "document_id": "doc123", "page_number": 1}
    assert parsed_lines[1] == {"article_id": "a2", "headline": "H2", "document_id": "doc123", "page_number": 1}
    assert parsed_lines[2] == {"article_id": "a3", "headline": "H3", "document_id": "doc123", "page_number": 2}

def test_export_jsonl_file_not_found(tmp_path: Path):
    """Reject an input path that does not exist."""

    input_file = tmp_path / "missing.json"
    output_file = tmp_path / "out.jsonl"
    with pytest.raises(FileNotFoundError):
        export_jsonl(input_file, output_file)

def test_export_jsonl_invalid_extension(tmp_path: Path):
    """Reject an input file without the JSON extension."""

    input_file = tmp_path / "test.txt"
    input_file.write_text("{}")
    output_file = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Input file must be a .json file."):
        export_jsonl(input_file, output_file)

def test_export_jsonl_same_file(tmp_path: Path):
    """Reject aliases that would overwrite the input file."""

    input_file = tmp_path / "test.json"
    input_file.write_text("{}")
    with pytest.raises(ValueError, match="must not refer to the same file"):
        export_jsonl(input_file, input_file)

def test_export_jsonl_invalid_json(tmp_path: Path):
    """Reject malformed JSON input."""

    input_file = tmp_path / "test.json"
    input_file.write_text("{invalid")
    output_file = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_non_finite_float(tmp_path: Path):
    """Reject non-standard non-finite JSON numbers."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"val": NaN}')
    output_file = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Invalid JSON file"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_top_level_not_dict(tmp_path: Path):
    """Reject a top-level JSON value that is not an object."""

    input_file = tmp_path / "test.json"
    input_file.write_text("[]")
    output_file = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="Top-level parsed object must be a dictionary"):
        export_jsonl(input_file, output_file)

def test_export_jsonl_pages_not_list(tmp_path: Path):
    """Reject a pages field that is not a list."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"pages": {}}')
    output_file = tmp_path / "out.jsonl"
    with pytest.raises(ValueError, match="'pages' field must be a list."):
        export_jsonl(input_file, output_file)

@pytest.mark.parametrize(
    ("pages", "message"),
    [
        (["not a dict"], "pages[0] must be an object"),
        ([{"page_number": 1, "articles": "not a list"}], "articles must be a list"),
        (
            [{"page_number": 1, "articles": ["not a dict"]}],
            "articles[0] must be an object",
        ),
    ],
)
def test_export_jsonl_rejects_invalid_nested_types(
    tmp_path: Path,
    pages: list,
    message: str,
):
    """Malformed nested records must fail instead of disappearing from output."""

    input_file = tmp_path / "test.json"
    output_file = tmp_path / "out.jsonl"
    input_file.write_text(
        json.dumps({"document_id": "doc123", "pages": pages}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=re.escape(message)):
        export_jsonl(input_file, output_file)

    assert not output_file.exists()


def test_export_jsonl_does_not_touch_predictable_temp_sibling(tmp_path: Path):
    """A pre-existing legacy .tmp sibling must never be opened or removed."""

    input_file = tmp_path / "test.json"
    output_file = tmp_path / "out.jsonl"
    legacy_temp_file = tmp_path / "out.jsonl.tmp"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    legacy_temp_file.write_text("owner data", encoding="utf-8")

    export_jsonl(input_file, output_file)

    assert legacy_temp_file.read_text(encoding="utf-8") == "owner data"


def test_export_jsonl_new_file_is_private(tmp_path: Path):
    """A newly exported file must never pass through a group-readable mode."""

    input_file = tmp_path / "test.json"
    output_file = tmp_path / "out.jsonl"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    real_replace = os.replace

    def assert_private_then_replace(source, destination):
        """Assert private staging permissions immediately before publication."""

        assert (Path(source).stat().st_mode & 0o777) == 0o600
        real_replace(source, destination)

    with patch("os.replace", side_effect=assert_private_then_replace):
        export_jsonl(input_file, output_file)

    assert (output_file.stat().st_mode & 0o777) == 0o600


def test_export_jsonl_permissions_existing_file(tmp_path: Path):
    """Preserve the permissions of an existing destination."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    output_file = tmp_path / "out.jsonl"
    output_file.write_text("")
    os.chmod(output_file, 0o600)

    export_jsonl(input_file, output_file)

    assert (output_file.stat().st_mode & 0o777) == 0o600

def test_export_jsonl_cleanup_on_error(tmp_path: Path):
    """Remove the invocation-owned temporary file after publication fails."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    output_file = tmp_path / "out.jsonl"

    with patch("os.replace", side_effect=OSError("Disk full")):
        with pytest.raises(OSError):
            export_jsonl(input_file, output_file)

    temp_path = output_file.with_suffix(output_file.suffix + ".tmp")
    assert not temp_path.exists()

def test_main_success(tmp_path: Path, capsys):
    """Report CLI success after exporting a valid document."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    output_file = tmp_path / "out.jsonl"

    with patch("sys.argv", ["export_jsonl.py", str(input_file), str(output_file)]):
        main()

    captured = capsys.readouterr()
    assert f"JSONL successfully written to {output_file}" in captured.out

def test_main_error(tmp_path: Path, capsys):
    """Report a CLI error and exit nonzero for an invalid input path."""

    input_file = tmp_path / "test.json"
    output_file = tmp_path / "out.jsonl"

    with patch("sys.argv", ["export_jsonl.py", str(input_file), str(output_file)]):
        with pytest.raises(SystemExit) as excinfo:
            main()

    assert excinfo.value.code == 1
    captured = capsys.readouterr()
    assert "Error exporting JSONL" in captured.err
def test_export_jsonl_cleanup_error_ignored(tmp_path: Path):
    """Preserve the primary publication error if cleanup also fails."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    output_file = tmp_path / "out.jsonl"

    with patch("os.replace", side_effect=OSError("Disk full")):
        with patch("os.unlink", side_effect=OSError("Cannot unlink")):
            with pytest.raises(OSError):
                export_jsonl(input_file, output_file)
def test_export_jsonl_cleanup_temp_missing(tmp_path: Path):
    """Cleanup tolerates replacement code that already removed its unique temp."""

    input_file = tmp_path / "test.json"
    input_file.write_text('{"document_id": "doc", "pages": []}')
    output_file = tmp_path / "out.jsonl"

    def mock_replace(source, _destination):
        """Remove the staging file before simulating publication failure."""

        os.unlink(source)
        raise OSError("Disk full")

    with patch("os.replace", side_effect=mock_replace):
        with pytest.raises(OSError):
            export_jsonl(input_file, output_file)
