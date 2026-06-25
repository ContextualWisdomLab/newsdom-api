import subprocess
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from newsdom_api import mineru_runner
from newsdom_api.main import app, parse


class _FakeTempDir:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.path.mkdir(parents=True, exist_ok=True)
        return str(self.path)

    def __exit__(self, exc_type, exc, tb):
        return False


class _ReadTrackingUpload:
    content_type = "application/pdf"
    filename = "fixture.pdf"
    size = 10 * 1024 * 1024

    def __init__(self, payload: bytes):
        self._payload = payload
        self._offset = 0
        self.read_sizes: list[int] = []

    async def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        if size < 0:
            size = len(self._payload) - self._offset
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


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
        files={"file": ("fixture.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 415
    assert (
        response.json()["detail"] == "Unsupported Media Type: expected application/pdf"
    )


def test_parse_endpoint_accepts_pdf_content_type_parameters(monkeypatch):
    def fake_parse_pdf_bytes(pdf_bytes, filename):
        assert pdf_bytes == b"%PDF-1.4\n%synthetic\n"
        assert filename == "fixture.pdf"
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main.parse_pdf_bytes", fake_parse_pdf_bytes)

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={
            "file": (
                "fixture.pdf",
                b"%PDF-1.4\n%synthetic\n",
                "Application/PDF; charset=binary",
            )
        },
    )

    assert response.status_code == 200


def test_parse_endpoint_returns_503_for_mineru_runtime_failure(monkeypatch):
    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True
        raise subprocess.CalledProcessError(
            returncode=17,
            cmd=cmd,
            output="stdout from /private/var/folders/runtime-output",
            stderr="stderr from /Users/private-user/tmp/mineru.stderr",
        )

    monkeypatch.setattr(mineru_runner, "_resolve_mineru_bin", lambda: "mineru")
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

    def fake_run(cmd, check, capture_output, text, timeout=None, shell=False):
        assert check is True
        assert capture_output is True
        assert text is True

        class Result:
            stdout = "stdout from /private/var/folders/runtime-output"
            stderr = "stderr from /Users/private-user/tmp/mineru.stderr"

        return Result()

    monkeypatch.setattr(mineru_runner, "_resolve_mineru_bin", lambda: "mineru")
    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "MinerU output was incomplete"
    _assert_no_private_path_material(response.json()["detail"])


def test_parse_endpoint_catches_incomplete_output_error(monkeypatch):
    from newsdom_api.errors import MineruIncompleteOutputError

    def fake_parse_pdf_bytes(pdf_bytes, filename):
        raise MineruIncompleteOutputError()

    monkeypatch.setattr("newsdom_api.main.parse_pdf_bytes", fake_parse_pdf_bytes)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "MinerU output was incomplete"


def test_parse_endpoint_catches_runtime_unavailable_error(monkeypatch):
    from newsdom_api.errors import MineruRuntimeUnavailableError

    def fake_parse_pdf_bytes(pdf_bytes, filename):
        raise MineruRuntimeUnavailableError()

    monkeypatch.setattr("newsdom_api.main.parse_pdf_bytes", fake_parse_pdf_bytes)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "MinerU runtime unavailable"
    _assert_no_private_path_material(response.json()["detail"])


def test_parse_endpoint_rejects_large_files(monkeypatch):
    def fake_parse_pdf_bytes(pdf_bytes, filename):
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main.parse_pdf_bytes", fake_parse_pdf_bytes)

    client = TestClient(app)

    large_payload = b"%PDF-1.4\n" + (b"x" * 21 * 1024 * 1024)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", large_payload, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Payload Too Large: file exceeds 20MB limit"


@pytest.mark.asyncio
async def test_parse_endpoint_rejects_large_file_without_size_metadata():
    upload = _ReadTrackingUpload(b"%PDF-" + (b"x" * (20 * 1024 * 1024)))
    upload.size = None

    with pytest.raises(HTTPException) as exc_info:
        await parse(upload)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Payload Too Large: file exceeds 20MB limit"
    assert upload.read_sizes == [5, 20 * 1024 * 1024 - 5 + 1]


def test_parse_endpoint_rejects_missing_magic_bytes():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={
            "file": ("fixture.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf")
        },
    )
    assert response.status_code == 415
    assert (
        response.json()["detail"] == "Unsupported Media Type: missing PDF magic bytes"
    )


@pytest.mark.asyncio
async def test_parse_endpoint_rejects_magic_bytes_before_full_read():
    upload = _ReadTrackingUpload(b"MZ\x90\x00\x03" + (b"x" * 1024 * 1024))

    with pytest.raises(HTTPException) as exc_info:
        await parse(upload)

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type: missing PDF magic bytes"
    assert upload.read_sizes == [5]
