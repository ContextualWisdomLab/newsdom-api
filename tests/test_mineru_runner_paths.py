import json
from pathlib import Path
import subprocess

import pytest

from newsdom_api import mineru_runner


class _FakeTempDir:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.path.mkdir(parents=True, exist_ok=True)
        return str(self.path)

    def __exit__(self, exc_type, exc, tb):
        return False


@pytest.fixture(autouse=True)
def clear_mineru_bin_cache():
    mineru_runner._resolve_mineru_bin.cache_clear()
    yield
    mineru_runner._resolve_mineru_bin.cache_clear()


def _assert_no_private_path_material(value: str) -> None:
    forbidden_fragments = (
        "/Users/",
        "/private/var/folders/",
        "/tmp/",
        "\\Users\\",
        "\\Temp\\",
        "newsdom-mineru-",
    )
    for fragment in forbidden_fragments:
        assert fragment not in value


def test_resolve_mineru_bin_prefers_env(monkeypatch):
    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/opt/mineru")
    assert mineru_runner._resolve_mineru_bin() == "/opt/mineru"


def test_resolve_mineru_bin_raises_when_not_found(monkeypatch):
    monkeypatch.delenv("NEWSDOM_MINERU_BIN", raising=False)
    monkeypatch.setattr(mineru_runner.shutil, "which", lambda name: None)
    with pytest.raises(FileNotFoundError):
        mineru_runner._resolve_mineru_bin()


def test_find_output_dir_raises_when_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        mineru_runner._find_output_dir(tmp_path)


def test_build_mineru_command_preserves_safe_spaces(tmp_path: Path):
    command = mineru_runner.build_mineru_command(
        Path("safe upload.pdf"), tmp_path / "mineru output"
    )

    assert command[2] == "safe upload.pdf"
    assert command[4] == str(tmp_path / "mineru output")


@pytest.mark.parametrize(
    ("input_pdf", "match"),
    [
        (Path("upload.pdf;touch-pwned"), "Unsafe input PDF path"),
        (Path("upload`id`.pdf"), "Unsafe input PDF path"),
        (Path("upload.pdf"), "Unsafe MinerU executable"),
    ],
    ids=["semicolon", "backtick", "executable"],
)
def test_build_mineru_command_rejects_shell_control_chars(
    tmp_path: Path, input_pdf: Path, match: str
):
    mineru_bin = "mineru"
    if match == "Unsafe MinerU executable":
        mineru_bin = "mineru;touch-pwned"

    with pytest.raises(ValueError, match=match):
        mineru_runner.build_mineru_command(
            input_pdf, tmp_path / "mineru-output", mineru_bin=mineru_bin
        )


def test_run_mineru_reads_generated_json(monkeypatch, tmp_path: Path):
    tempdir = tmp_path / "temp"
    ocr_dir = tempdir / "sample" / "ocr"
    ocr_dir.mkdir(parents=True)
    (ocr_dir / "alt_content_list.json").write_text(
        json.dumps([{"type": "text", "text": "ok"}]), encoding="utf-8"
    )
    (ocr_dir / "alt_model.json").write_text(
        json.dumps([{"layout_dets": []}]), encoding="utf-8"
    )

    monkeypatch.setattr(mineru_runner.shutil, "which", lambda name: "/usr/bin/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    called = {}

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        assert timeout is not None
        called["cmd"] = cmd

        class Result:
            stdout = "stdout"
            stderr = "stderr"

        return Result()

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    result = mineru_runner.run_mineru(Path("sample.pdf"))
    assert called["cmd"][0] == "/usr/bin/mineru"
    assert result["content_list"][0]["text"] == "ok"
    assert result["stderr"] == "stderr"


def test_run_mineru_prefers_exact_stem_content_json(monkeypatch, tmp_path: Path):
    tempdir = tmp_path / "temp"
    ocr_dir = tempdir / "sample" / "ocr"
    ocr_dir.mkdir(parents=True)
    (ocr_dir / "sample_content_list.json").write_text(
        json.dumps([{"type": "text", "text": "exact"}]), encoding="utf-8"
    )
    (ocr_dir / "alt_content_list.json").write_text(
        json.dumps([{"type": "text", "text": "fallback"}]), encoding="utf-8"
    )
    (ocr_dir / "alt_model.json").write_text(
        json.dumps([{"layout_dets": []}]), encoding="utf-8"
    )

    monkeypatch.setattr(mineru_runner.shutil, "which", lambda name: "/usr/bin/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        assert timeout is not None

        class Result:
            stdout = "stdout"
            stderr = "stderr"

        return Result()

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    result = mineru_runner.run_mineru(Path("sample.pdf"))
    assert result["content_list"][0]["text"] == "exact"


def test_run_mineru_wraps_called_process_error(monkeypatch, tmp_path: Path):
    tempdir = tmp_path / "temp"
    tempdir.mkdir()

    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/opt/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        raise subprocess.CalledProcessError(
            returncode=23,
            cmd=cmd,
            output="runtime output from /private/var/folders/secret",
            stderr="runtime stderr from /Users/private-user/tmp/mineru.log",
        )

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    with pytest.raises(Exception) as exc_info:
        mineru_runner.run_mineru(Path("sample.pdf"))

    assert exc_info.type.__name__ == "MineruRuntimeUnavailableError"
    assert exc_info.value.returncode == 23
    assert exc_info.value.stdout == "runtime output from /private/var/folders/secret"
    assert (
        exc_info.value.stderr
        == "runtime stderr from /Users/private-user/tmp/mineru.log"
    )
    _assert_no_private_path_material(str(exc_info.value))


def test_run_mineru_wraps_missing_executable_failure(monkeypatch, tmp_path: Path):
    tempdir = tmp_path / "temp"
    tempdir.mkdir()

    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/opt/private/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        raise FileNotFoundError(
            "/opt/private/mineru not found in /Users/private-user/bin"
        )

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    with pytest.raises(Exception) as exc_info:
        mineru_runner.run_mineru(Path("sample.pdf"))

    assert exc_info.type.__name__ == "MineruRuntimeUnavailableError"
    assert getattr(exc_info.value, "returncode", None) is None
    assert getattr(exc_info.value, "stdout", None) in (None, "")
    assert getattr(exc_info.value, "stderr", None) in (None, "")
    _assert_no_private_path_material(str(exc_info.value))


@pytest.mark.parametrize(
    ("fixture_name", "create_outputs"),
    [
        ("missing ocr dir", lambda output_dir: None),
        (
            "missing content list",
            lambda output_dir: (output_dir / "sample" / "ocr").mkdir(parents=True),
        ),
        (
            "missing model",
            lambda output_dir: (
                (output_dir / "sample" / "ocr").mkdir(parents=True),
                (output_dir / "sample" / "ocr" / "alt_content_list.json").write_text(
                    json.dumps([{"type": "text", "text": "ok"}]),
                    encoding="utf-8",
                ),
            ),
        ),
    ],
    ids=["missing-ocr-dir", "missing-content-list", "missing-model"],
)
def test_run_mineru_raises_typed_incomplete_output_error(
    monkeypatch, tmp_path: Path, fixture_name: str, create_outputs
):
    tempdir = tmp_path / "temp"
    create_outputs(tempdir)
    if fixture_name == "missing content list":
        ocr_dir = tempdir / "sample" / "ocr"
        (ocr_dir / "alt_model.json").write_text(
            json.dumps([{"layout_dets": []}]), encoding="utf-8"
        )

    monkeypatch.setenv("NEWSDOM_MINERU_BIN", "/opt/mineru")
    monkeypatch.setattr(mineru_runner.shutil, "which", lambda name: "/usr/bin/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        assert timeout is not None

        class Result:
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    with pytest.raises(Exception) as exc_info:
        mineru_runner.run_mineru(Path("sample.pdf"))

    assert exc_info.type.__name__ == "MineruIncompleteOutputError"
    _assert_no_private_path_material(str(exc_info.value))


@pytest.mark.parametrize(
    ("artifact_name", "file_name"),
    [
        ("content_list", "sample_content_list.json"),
        ("model", "sample_model.json"),
    ],
    ids=["malformed-content-list", "malformed-model"],
)
def test_run_mineru_raises_typed_incomplete_output_error_for_malformed_json(
    monkeypatch, tmp_path: Path, artifact_name: str, file_name: str
):
    tempdir = tmp_path / "temp"
    ocr_dir = tempdir / "sample" / "ocr"
    ocr_dir.mkdir(parents=True)

    content_payload = "{not valid json"
    model_payload = "{not valid json"
    if artifact_name == "content_list":
        model_payload = json.dumps([{"layout_dets": []}])
    else:
        content_payload = json.dumps([{"type": "text", "text": "ok"}])

    (ocr_dir / "sample_content_list.json").write_text(content_payload, encoding="utf-8")
    (ocr_dir / "sample_model.json").write_text(model_payload, encoding="utf-8")

    monkeypatch.setattr(mineru_runner.shutil, "which", lambda name: "/usr/bin/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        assert timeout is not None

        class Result:
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    with pytest.raises(Exception) as exc_info:
        mineru_runner.run_mineru(Path("sample.pdf"))

    assert exc_info.type.__name__ == "MineruIncompleteOutputError"
    _assert_no_private_path_material(str(exc_info.value))


@pytest.mark.parametrize(
    ("file_name", "read_error"),
    [
        (
            "sample_content_list.json",
            FileNotFoundError("/private/var/folders/sample_content_list.json"),
        ),
        (
            "sample_model.json",
            UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte"),
        ),
    ],
    ids=["content-read-missing", "model-read-unicode-error"],
)
def test_run_mineru_wraps_output_read_failures(
    monkeypatch, tmp_path: Path, file_name: str, read_error: Exception
):
    tempdir = tmp_path / "temp"
    ocr_dir = tempdir / "sample" / "ocr"
    ocr_dir.mkdir(parents=True)
    (ocr_dir / "sample_content_list.json").write_text(
        json.dumps([{"type": "text", "text": "ok"}]), encoding="utf-8"
    )
    (ocr_dir / "sample_model.json").write_text(
        json.dumps([{"layout_dets": []}]), encoding="utf-8"
    )

    monkeypatch.setattr(mineru_runner.shutil, "which", lambda name: "/usr/bin/mineru")
    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        assert timeout is not None

        class Result:
            stdout = ""
            stderr = ""

        return Result()

    original_read_text = Path.read_text

    def fake_read_text(self, *args, **kwargs):
        if self.name == file_name:
            raise read_error
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)
    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    with pytest.raises(Exception) as exc_info:
        mineru_runner.run_mineru(Path("sample.pdf"))

    assert exc_info.type.__name__ == "MineruIncompleteOutputError"
    _assert_no_private_path_material(str(exc_info.value))
