"""Regression tests for NewsDOM filter CLI input-read failures."""

from pathlib import Path

import pytest

from tools.filter_dom import main


@pytest.mark.parametrize(
    "read_error",
    [
        OSError("simulated read failure"),
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
    ],
)
def test_main_reports_input_read_errors_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    read_error: Exception,
) -> None:
    """Unreadable or undecodable JSON input must fail through the CLI contract."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"
    input_file.write_bytes(b"{}")
    original_read_text = Path.read_text

    def fail_target_read(self: Path, *args: object, **kwargs: object) -> str:
        if self == input_file:
            raise read_error
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_target_read)

    with pytest.raises(SystemExit) as excinfo:
        main([str(input_file), str(output_file)])

    assert excinfo.value.code == 1
    assert "Error reading input file" in capsys.readouterr().err
    assert not output_file.exists()
