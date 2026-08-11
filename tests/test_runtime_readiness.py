"""Readiness tests for MinerU executable discovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from newsdom_api import mineru_runner
from newsdom_api.errors import MineruRuntimeUnavailableError


def test_mineru_runtime_available_is_false_when_resolution_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing runtime resolution must make readiness fail closed."""

    def fail_resolution() -> str:
        raise MineruRuntimeUnavailableError()

    monkeypatch.setattr(mineru_runner, "_resolve_mineru_bin", fail_resolution)

    assert mineru_runner.mineru_runtime_available() is False


@pytest.mark.parametrize("relative", [False, True])
def test_mineru_runtime_available_accepts_executable_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, relative: bool
) -> None:
    """Absolute and relative executable paths should be checked on the filesystem."""

    executable = tmp_path / "relative" / "mineru" if relative else tmp_path / "mineru"
    executable.parent.mkdir(parents=True, exist_ok=True)
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o700)
    selected = str(executable.relative_to(tmp_path)) if relative else str(executable)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(mineru_runner, "_resolve_mineru_bin", lambda: selected)

    assert mineru_runner.mineru_runtime_available() is True


def test_mineru_runtime_available_rejects_missing_or_nonexecutable_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A configured path must identify an existing executable file."""

    missing = tmp_path / "missing-mineru"
    monkeypatch.setattr(mineru_runner, "_resolve_mineru_bin", lambda: str(missing))
    assert mineru_runner.mineru_runtime_available() is False

    nonexecutable = tmp_path / "mineru"
    nonexecutable.write_text("not executable", encoding="utf-8")
    nonexecutable.chmod(0o600)
    monkeypatch.setattr(
        mineru_runner, "_resolve_mineru_bin", lambda: str(nonexecutable)
    )
    assert mineru_runner.mineru_runtime_available() is False


def test_mineru_runtime_available_checks_path_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A command name should use the cached PATH lookup for readiness."""

    monkeypatch.setattr(mineru_runner, "_resolve_mineru_bin", lambda: "mineru")
    monkeypatch.setattr(
        mineru_runner, "_cached_which", lambda command: f"/bin/{command}"
    )
    assert mineru_runner.mineru_runtime_available() is True

    monkeypatch.setattr(mineru_runner, "_cached_which", lambda _command: None)
    assert mineru_runner.mineru_runtime_available() is False
