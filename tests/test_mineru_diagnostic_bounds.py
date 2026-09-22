import subprocess

import pytest

from newsdom_api import mineru_runner
from newsdom_api.errors import MineruRuntimeUnavailableError


@pytest.mark.parametrize(
    ("failure", "expected_returncode"),
    [
        (
            subprocess.CalledProcessError(
                23,
                ["mineru"],
                output="o" * 5000,
                stderr=(b"\xff" + b"e" * 5000),
            ),
            23,
        ),
        (
            subprocess.TimeoutExpired(
                ["mineru"],
                300,
                output=(b"\xff" + b"o" * 5000),
                stderr=b"ignored timeout stderr",
            ),
            -1,
        ),
    ],
)
def test_execute_mineru_bounds_failure_diagnostics(monkeypatch, failure, expected_returncode):
    def fail_run(*_args, **_kwargs):
        raise failure

    monkeypatch.setattr(subprocess, "run", fail_run)

    with pytest.raises(MineruRuntimeUnavailableError) as exc_info:
        mineru_runner._execute_mineru(["mineru", "-p", "sample.pdf"])

    error = exc_info.value
    assert error.returncode == expected_returncode
    assert isinstance(error.stdout, str)
    assert len(error.stdout) <= 4096
    assert "\ufffd" in error.stdout

    if expected_returncode == 23:
        assert isinstance(error.stderr, str)
        assert len(error.stderr) <= 4096
        assert "\ufffd" in error.stderr
    else:
        assert error.stderr == "OCR processing timed out after 5 minutes"
