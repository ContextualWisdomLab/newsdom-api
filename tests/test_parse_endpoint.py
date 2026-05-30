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


def test_parse_endpoint_rejects_non_pdf_content_type():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.txt", b"%PDF-1.4\nsome text", "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported media type" in response.json()["detail"]


def test_parse_endpoint_rejects_invalid_magic_bytes():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"Not a PDF\n", "application/pdf")},
    )
    assert response.status_code == 415
    assert "Invalid file content" in response.json()["detail"]


def test_parse_endpoint_rejects_oversized_file(monkeypatch):
    client = TestClient(app)

    # We fake the size calculation for the test
    # Starlette UploadFile calculates size via the spooled file
    # We can inject a file with a large reported size
    class FakeUploadFile:
        def __init__(self, size):
            self.size = size
            self.content_type = "application/pdf"
            self.filename = "large.pdf"

        async def read(self):
            return b"%PDF-1.4\n..."

    # Alternatively, directly patch the app or post large content
    # A cleaner way is posting a large request body, but for speed we can
    # monkeypatch size or just post a large string using a generator
    large_content = b"%PDF" + b"0" * (50 * 1024 * 1024 + 1)

    response = client.post(
        "/parse",
        files={"file": ("large.pdf", large_content, "application/pdf")},
    )

    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]


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
