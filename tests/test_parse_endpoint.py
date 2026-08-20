import subprocess
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pypdf.errors import PdfReadError

from newsdom_api import mineru_runner
from newsdom_api.main import (
    MAX_PARSE_UPLOAD_BYTES,
    app,
    parse,
    _validate_pdf_structure,
)


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
    assert response.json()["detail"] == "Unsupported Media Type"


def test_parse_endpoint_rejects_invalid_pdf_magic_bytes():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"not a pdf", "application/pdf")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


def test_validate_pdf_structure_rejects_invalid_magic_bytes(tmp_path):
    with pytest.raises(HTTPException) as exc_info:
        (tmp_path / "test.pdf").write_bytes(b"not a pdf")
        _validate_pdf_structure(tmp_path / "test.pdf")

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type"
    assert exc_info.value.__cause__ is None


def test_validate_pdf_structure_rejects_pypdf_read_errors(monkeypatch, tmp_path):
    def reject_pdf(_stream, *, strict):
        assert strict is True
        raise PdfReadError("invalid xref table")

    monkeypatch.setattr("newsdom_api.main.PdfReader", reject_pdf)

    with pytest.raises(HTTPException) as exc_info:
        (tmp_path / "test.pdf").write_bytes(b"%PDF-1.4\n%%EOF")
        _validate_pdf_structure(tmp_path / "test.pdf")

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type"


def test_parse_endpoint_rejects_prefixed_non_pdf_payload():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={
            "file": (
                "fixture.pdf",
                b"%PDF-not actually a parseable document",
                "application/pdf",
            )
        },
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


def test_parse_endpoint_rejects_pdf_without_pages(monkeypatch):
    class EmptyPdfReader:
        pages = []

    monkeypatch.setattr(
        "newsdom_api.main.PdfReader", lambda *_args, **_kwargs: EmptyPdfReader()
    )

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


def test_parse_endpoint_accepts_structurally_valid_pdf(monkeypatch):
    class OnePagePdfReader:
        pages = [object()]

    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        assert file_path.read_bytes() == b"%PDF-1.4\n%%EOF"
        assert filename == "fixture.pdf"
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr(
        "newsdom_api.main.PdfReader", lambda *_args, **_kwargs: OnePagePdfReader()
    )
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
    )
    assert response.status_code == 200


def test_parse_endpoint_accepts_pdf_content_type_parameters(monkeypatch):
    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        assert file_path.read_bytes() == b"%PDF-1.4\n%synthetic\n"
        assert filename == "fixture.pdf"
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)

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


def test_parse_endpoint_logs_tempfile_cleanup_failure(monkeypatch, caplog):
    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        return {"document_id": "fixture", "pages": []}

    def failing_unlink(self, missing_ok=False):
        raise OSError("locked temp file")

    caplog.set_level("ERROR", logger="newsdom_api")
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    monkeypatch.setattr(Path, "unlink", failing_unlink)

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == "fixture"
    assert response.json()["pages"] == []
    assert "Failed to remove temporary upload file" in caplog.text


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
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Service Unavailable"
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
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr(mineru_runner.subprocess, "run", fake_run)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Bad Gateway"
    _assert_no_private_path_material(response.json()["detail"])


def test_parse_endpoint_catches_incomplete_output_error(monkeypatch):
    from newsdom_api.errors import MineruIncompleteOutputError

    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        raise MineruIncompleteOutputError()

    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Bad Gateway"


def test_parse_endpoint_catches_runtime_unavailable_error(monkeypatch):
    from newsdom_api.errors import MineruRuntimeUnavailableError

    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        raise MineruRuntimeUnavailableError()

    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Service Unavailable"
    _assert_no_private_path_material(response.json()["detail"])


@pytest.mark.asyncio
async def test_parse_endpoint_suppresses_service_exception_chain(monkeypatch):
    from newsdom_api.errors import MineruRuntimeUnavailableError

    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        raise MineruRuntimeUnavailableError()

    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)

    with pytest.raises(HTTPException) as exc_info:
        await parse(_ReadTrackingUpload(b"%PDF-1.4\n%synthetic\n"))

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Service Unavailable"
    assert exc_info.value.__cause__ is None


def test_parse_endpoint_rejects_large_files(monkeypatch):
    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    synthetic_limit = 64
    monkeypatch.setattr("newsdom_api.main.MAX_PARSE_UPLOAD_BYTES", synthetic_limit)

    client = TestClient(app)

    large_payload = b"%PDF-" + (b"x" * (synthetic_limit - 5 + 1))
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", large_payload, "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Payload Too Large"


@pytest.mark.asyncio
async def test_parse_endpoint_rejects_large_file_without_size_metadata(monkeypatch):
    synthetic_limit = 64
    monkeypatch.setattr("newsdom_api.main.MAX_PARSE_UPLOAD_BYTES", synthetic_limit)
    upload = _ReadTrackingUpload(b"%PDF-" + (b"x" * synthetic_limit))
    upload.size = None

    with pytest.raises(HTTPException) as exc_info:
        await parse(upload)

    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Payload Too Large"
    assert sum(upload.read_sizes) > synthetic_limit


def test_parse_endpoint_budget_is_larger_than_the_previous_20_mib_limit():
    assert MAX_PARSE_UPLOAD_BYTES == 64 * 1024 * 1024


def test_parse_endpoint_rejects_missing_magic_bytes():
    client = TestClient(app)
    response = client.post(
        "/parse",
        files={
            "file": ("fixture.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf")
        },
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"


@pytest.mark.asyncio
async def test_parse_endpoint_rejects_magic_bytes_before_full_read():
    upload = _ReadTrackingUpload(b"MZ\x90\x00\x03" + (b"x" * 1024 * 1024))

    with pytest.raises(HTTPException) as exc_info:
        await parse(upload)

    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Unsupported Media Type"
    assert upload.read_sizes == [5]


def test_unhandled_exception_includes_security_headers(monkeypatch):
    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        raise RuntimeError("unexpected internal explosion")

    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Internal Server Error"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert (
        response.headers.get("Content-Security-Policy")
        == "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
    )
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert response.headers.get("Cache-Control") == "no-store, no-cache, max-age=0"
    assert "Strict-Transport-Security" not in response.headers


def test_unhandled_exception_includes_hsts_for_forwarded_https(monkeypatch):
    def fake_parse_pdf_bytes(file_path, filename, **kwargs):
        raise RuntimeError("unexpected internal explosion")

    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf_bytes)
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/parse",
        headers={"X-Forwarded-Proto": "https"},
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 500
    assert (
        response.headers.get("Strict-Transport-Security")
        == "max-age=31536000; includeSubDomains"
    )


def test_parse_endpoint_uses_supported_language_and_auto_mode_defaults(monkeypatch):
    captured = {}

    def fake_parse_pdf(file_path, filename, **kwargs):
        captured.update(kwargs)
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
    )

    assert response.status_code == 200
    assert captured == {"language": "ch", "mode": "auto"}


def test_parse_endpoint_forwards_language_and_mode_to_parser(monkeypatch):
    captured = {}

    def fake_parse_pdf(file_path, filename, **kwargs):
        captured.update(kwargs)
        return {"document_id": "fixture", "pages": []}

    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr("newsdom_api.main.parse_pdf", fake_parse_pdf)

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
        data={"language": "Japan", "mode": "OCR"},
    )

    assert response.status_code == 200
    # Values are normalized (lower-cased) before reaching the parser.
    assert captured == {"language": "ch", "mode": "ocr"}


def test_parse_endpoint_rejects_invalid_mode_with_422(monkeypatch):
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr(
        "newsdom_api.main.parse_pdf",
        lambda *a, **k: {"document_id": "x", "pages": []},
    )

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
        data={"mode": "not-a-mode"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid parse parameters"


def test_parse_endpoint_rejects_invalid_language_with_422(monkeypatch):
    monkeypatch.setattr("newsdom_api.main._validate_pdf_structure", lambda _: None)
    monkeypatch.setattr(
        "newsdom_api.main.parse_pdf",
        lambda *a, **k: {"document_id": "x", "pages": []},
    )

    client = TestClient(app)
    response = client.post(
        "/parse",
        files={"file": ("fixture.pdf", b"%PDF-1.4\n%synthetic\n", "application/pdf")},
        data={"language": "en; rm -rf"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid parse parameters"


@pytest.mark.asyncio
async def test_parse_endpoint_cleans_up_tempfile_on_read_exception(monkeypatch):
    class ClientDisconnectError(Exception):
        pass

    class FailingUploadFile(_ReadTrackingUpload):
        async def read(self, size: int = -1):
            if not hasattr(self, "_failed"):
                # Return valid magic bytes first to bypass structure check
                self._failed = True
                return b"%PDF-"
            raise ClientDisconnectError("Client disconnected during streaming")

    upload = FailingUploadFile(b"%PDF-1.4\n%synthetic\n")
    upload.size = 1000

    # We need to spy on Path.unlink to verify it's called
    # But since it fails *during* the file read loop, the file is created on disk
    # Let's mock Path.unlink and track if it gets called on a temporary file

    unlinked_paths = []
    original_unlink = Path.unlink

    def spy_unlink(self, missing_ok=False):
        unlinked_paths.append(str(self))
        return original_unlink(self, missing_ok)

    monkeypatch.setattr(Path, "unlink", spy_unlink)

    with pytest.raises(ClientDisconnectError):
        await parse(upload)

    # We should have unlinked exactly one file, which should be in the temp directory
    assert len(unlinked_paths) == 1
    assert "tmp" in unlinked_paths[0].lower() or "temp" in unlinked_paths[0].lower()
