from fastapi.testclient import TestClient
import subprocess
from pathlib import Path

from newsdom_api.main import app
from newsdom_api import mineru_runner


class _FakeTempDir:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.path.mkdir(parents=True, exist_ok=True)
        return str(self.path)

    def __exit__(self, exc_type, exc, tb):
        return False


def _assert_no_private_path_material(value: str) -> None:
    forbidden_fragments = (
        "/Users/",
        "/private/var/folders/",
        "/tmp/",
        "\\Users\\",
        "\\Temp\\",
        "newsdom-upload-",
        "newsdom-mineru-",
    )
    for fragment in forbidden_fragments:
        assert fragment not in value


def test_parse_endpoint_requires_pdf_file():
    client = TestClient(app)
    response = client.post("/parse")
    assert response.status_code == 422


def test_parse_endpoint_returns_503_for_mineru_runtime_failure(monkeypatch):
    def fake_run(cmd, check, capture_output, text, timeout=None):
        assert check is True
        assert capture_output is True
        assert text is True
        raise subprocess.CalledProcessError(
            returncode=17,
            cmd=cmd,
            output="stdout from /private/var/folders/runtime-output",
            stderr="stderr from /Users/private-user/tmp/mineru.stderr",
        )

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "MinerU runtime unavailable"
    _assert_no_private_path_material(response.json()["detail"])


def test_parse_endpoint_returns_502_for_incomplete_mineru_output(
    monkeypatch, tmp_path: Path
):
    tempdir = tmp_path / "mineru-output"
    ocr_dir = tempdir / "fixture" / "ocr"
    ocr_dir.mkdir(parents=True)
    (ocr_dir / "alt_content_list.json").write_text(
        '[{"type": "text", "text": "ok"}]', encoding="utf-8"
    )

    monkeypatch.setattr(
        mineru_runner.tempfile,
        "TemporaryDirectory",
        lambda prefix: _FakeTempDir(tempdir),
    )

    def fake_run(cmd, check, capture_output, text, timeout=None):
        assert check is True
        assert capture_output is True
        assert text is True

        class Result:
            stdout = "stdout from /private/var/folders/runtime-output"
            stderr = "stderr from /Users/private-user/tmp/mineru.stderr"

        return Result()

    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "MinerU output was incomplete"
    _assert_no_private_path_material(response.json()["detail"])
