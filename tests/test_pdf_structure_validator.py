"""Resource-isolated PDF structural validation for untrusted uploads."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from pypdf.errors import PdfReadError

from newsdom_api.pdf_structure_validator import (
    ValidationOutcome,
    _child_pythonpath,
    apply_resource_limits,
    child_main,
    decode_child_payload,
    resource_limits_supported,
    validate_pdf_structure_in_process,
    validate_pdf_structure_isolated,
)

SYNTHETIC_PDF = Path("tests/fixtures/synthetic_reference.pdf")


class _HangingProcess:
    """Child double that occupies the waiter until cancelled or killed."""

    def __init__(self) -> None:
        self.returncode: int | None = None
        self.killed = False
        self.started = asyncio.Event()

    async def communicate(self) -> tuple[bytes, bytes]:
        """Block until the parent kills or cancels the waiter."""

        self.started.set()
        await asyncio.sleep(30)
        return b"", b""

    def kill(self) -> None:
        """Record termination of a hanging validator child."""

        self.killed = True
        self.returncode = -9

    async def wait(self) -> int:
        """Return the recorded termination status."""

        return int(self.returncode or 0)


def test_linux_runtime_exposes_cpu_and_address_space_limits() -> None:
    """Production Linux must expose the POSIX limits the child applies."""

    assert resource_limits_supported() is True


def test_in_process_validation_accepts_synthetic_reference_pdf() -> None:
    """A real fixture PDF must remain structurally valid for MinerU admission."""

    assert SYNTHETIC_PDF.is_file()
    assert (
        validate_pdf_structure_in_process(SYNTHETIC_PDF) is ValidationOutcome.VALID
    )


def test_in_process_validation_rejects_missing_magic_bytes(tmp_path: Path) -> None:
    """Reject files that do not start with the PDF magic header."""

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"not-a-pdf")
    assert (
        validate_pdf_structure_in_process(path)
        is ValidationOutcome.INVALID_DOCUMENT
    )


@pytest.mark.parametrize(
    "error",
    [
        PdfReadError("invalid xref table"),
        RecursionError("parser recursion"),
        ValueError("PDF has no pages"),
        OverflowError("oversize object"),
        TypeError("unexpected object"),
        MemoryError("expanded object stream"),
    ],
)
def test_in_process_validation_maps_client_parser_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error: BaseException
) -> None:
    """Client-caused parser failures stay typed as invalid documents."""

    def reject_pdf(_stream: Path, *, strict: bool) -> None:
        assert strict is True
        raise error

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.PdfReader", reject_pdf
    )
    assert (
        validate_pdf_structure_in_process(path)
        is ValidationOutcome.INVALID_DOCUMENT
    )


def test_in_process_validation_rejects_pdf_without_pages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A structurally opened PDF with zero pages is not admissible."""

    class EmptyPdfReader:
        pages: list[object] = []

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.PdfReader",
        lambda *_args, **_kwargs: EmptyPdfReader(),
    )
    assert (
        validate_pdf_structure_in_process(path)
        is ValidationOutcome.INVALID_DOCUMENT
    )


def test_in_process_validation_maps_unexpected_errors_to_validator_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Programming failures must not be reported as client invalid documents."""

    def reject_pdf(_stream: Path, *, strict: bool) -> None:
        raise RuntimeError("unexpected validator bug")

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"%PDF-1.4\n%%EOF")
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.PdfReader", reject_pdf
    )
    assert (
        validate_pdf_structure_in_process(path)
        is ValidationOutcome.VALIDATOR_FAILURE
    )


def test_apply_resource_limits_sets_cpu_and_address_space(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The child must apply both CPU and address-space limits before open()."""

    recorded: list[tuple[int, tuple[int, int]]] = []

    def fake_setrlimit(resource_id: int, limits: tuple[int, int]) -> None:
        recorded.append((resource_id, limits))

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource.setrlimit", fake_setrlimit
    )
    apply_resource_limits(cpu_seconds=3, address_space_bytes=1024)
    assert recorded[0][1] == (3, 3)
    assert recorded[1][1] == (1024, 1024)


def test_apply_resource_limits_fails_closed_without_platform_support(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unsupported hosts must not silently skip the sandbox."""

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: False,
    )
    with pytest.raises(RuntimeError, match="unavailable"):
        apply_resource_limits()


def test_decode_child_payload_accepts_only_typed_outcomes() -> None:
    """Child stdout is a one-object JSON contract with no paths or traces."""

    assert decode_child_payload(b'{"outcome":"valid"}') is ValidationOutcome.VALID
    assert (
        decode_child_payload(b'{"outcome":"invalid_document"}')
        is ValidationOutcome.INVALID_DOCUMENT
    )
    assert decode_child_payload(b"not-json") is ValidationOutcome.VALIDATOR_FAILURE
    assert decode_child_payload(b'["valid"]') is ValidationOutcome.VALIDATOR_FAILURE
    assert (
        decode_child_payload(b'{"outcome":"mystery"}')
        is ValidationOutcome.VALIDATOR_FAILURE
    )
    assert decode_child_payload(b"\xff") is ValidationOutcome.VALIDATOR_FAILURE


def test_child_main_reads_sys_argv_when_unspecified(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The child ABI uses process argv when the caller omits an explicit list."""

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"not-a-pdf")
    monkeypatch.setattr(sys, "argv", ["pdf_structure_validator", str(path)])
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.apply_resource_limits", lambda: None
    )
    assert child_main() == 1
    assert json.loads(capsys.readouterr().out) == {"outcome": "invalid_document"}


def test_child_main_emits_sanitized_invalid_outcome(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The child prints only a typed outcome and never the upload path."""

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.apply_resource_limits", lambda: None
    )
    path = tmp_path / "secret-upload.pdf"
    path.write_bytes(b"not-a-pdf")
    assert child_main([str(path)]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"outcome": "invalid_document"}
    assert "secret-upload" not in json.dumps(payload)


def test_child_main_rejects_wrong_argv(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unexpected argv is a validator failure, not a client 415."""

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.apply_resource_limits", lambda: None
    )
    assert child_main([]) == 1
    assert json.loads(capsys.readouterr().out) == {"outcome": "validator_failure"}


def test_child_main_reports_valid_synthetic_pdf(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A valid fixture returns outcome valid and process status 0."""

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.apply_resource_limits", lambda: None
    )
    assert child_main([str(SYNTHETIC_PDF)]) == 0
    assert json.loads(capsys.readouterr().out) == {"outcome": "valid"}


def test_module_entrypoint_uses_child_main(tmp_path: Path) -> None:
    """`python -m newsdom_api.pdf_structure_validator` must stay the child ABI."""

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"not-a-pdf")
    env = os.environ.copy()
    env["PYTHONPATH"] = _child_pythonpath()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "newsdom_api.pdf_structure_validator",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout) == {"outcome": "invalid_document"}


@pytest.mark.asyncio
async def test_isolated_validation_fails_closed_without_limits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Parents must not spawn an unbounded validator on unsupported platforms."""

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: False,
    )
    outcome = await validate_pdf_structure_isolated(Path("unused.pdf"))
    assert outcome is ValidationOutcome.VALIDATOR_FAILURE


@pytest.mark.asyncio
async def test_isolated_validation_times_out_and_kills_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hanging validator is terminated at the wall-clock limit."""

    hanging = _HangingProcess()

    async def factory(*_args: object, **_kwargs: object) -> _HangingProcess:
        return hanging

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    ticks = 0

    async def ticker() -> None:
        nonlocal ticks
        while ticks < 5:
            await asyncio.sleep(0)
            ticks += 1

    validation = asyncio.create_task(
        validate_pdf_structure_isolated(Path("unused.pdf"), timeout_seconds=0.05)
    )
    await hanging.started.wait()
    await ticker()
    outcome = await validation
    assert ticks == 5
    assert hanging.killed is True
    assert outcome is ValidationOutcome.INVALID_DOCUMENT


@pytest.mark.asyncio
async def test_isolated_validation_cancel_reclaims_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Request cancellation must kill the disposable child."""

    hanging = _HangingProcess()

    async def factory(*_args: object, **_kwargs: object) -> _HangingProcess:
        return hanging

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    task = asyncio.create_task(
        validate_pdf_structure_isolated(Path("unused.pdf"), timeout_seconds=5)
    )
    await hanging.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert hanging.killed is True


@pytest.mark.asyncio
async def test_isolated_validation_spawn_failure_is_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Process-launch failures fail closed without leaking OS text."""

    async def factory(*_args: object, **_kwargs: object) -> _HangingProcess:
        raise OSError("/tmp/secret-validator-socket")

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    outcome = await validate_pdf_structure_isolated(Path("unused.pdf"))
    assert outcome is ValidationOutcome.VALIDATOR_FAILURE


@pytest.mark.asyncio
async def test_isolated_validation_reclaim_failure_after_broken_pipe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cleanup errors after a broken child still fail closed."""

    class BrokenProcess:
        returncode = None

        async def communicate(self) -> tuple[bytes, bytes]:
            raise RuntimeError("pipe broke")

        def kill(self) -> None:
            raise OSError("already reaped")

        async def wait(self) -> int:
            raise OSError("wait failed")

    async def factory(*_args: object, **_kwargs: object) -> BrokenProcess:
        return BrokenProcess()

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    outcome = await validate_pdf_structure_isolated(Path("unused.pdf"))
    assert outcome is ValidationOutcome.VALIDATOR_FAILURE


@pytest.mark.asyncio
async def test_isolated_validation_reads_child_stdout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Successful children are decoded through the typed JSON contract."""

    class FinishedProcess:
        returncode = 0

        async def communicate(self) -> tuple[bytes, bytes]:
            return b'{"outcome":"valid"}', b""

        def kill(self) -> None:
            raise AssertionError("successful children must not be killed")

        async def wait(self) -> int:
            return 0

    async def factory(*_args: object, **_kwargs: object) -> FinishedProcess:
        return FinishedProcess()

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    outcome = await validate_pdf_structure_isolated(Path("unused.pdf"))
    assert outcome is ValidationOutcome.VALID


@pytest.mark.asyncio
async def test_isolated_validation_real_child_accepts_synthetic_pdf() -> None:
    """The production child ABI must validate the checked-in fixture PDF."""

    if not resource_limits_supported():
        pytest.skip("resource limits are required for the production child")
    outcome = await validate_pdf_structure_isolated(SYNTHETIC_PDF)
    assert outcome is ValidationOutcome.VALID


def test_child_pythonpath_prepends_src_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The disposable child must import the same `src` package tree."""

    src_dir = str(Path("src").resolve())
    monkeypatch.delenv("PYTHONPATH", raising=False)
    assert _child_pythonpath() == src_dir
    monkeypatch.setenv("PYTHONPATH", "/already-on-path")
    assert _child_pythonpath() == f"{src_dir}{os.pathsep}/already-on-path"


@pytest.mark.asyncio
async def test_isolated_validation_propagates_spawn_cancellation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancellation during process launch must not be converted into 503."""

    async def factory(*_args: object, **_kwargs: object) -> _HangingProcess:
        raise asyncio.CancelledError()

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    with pytest.raises(asyncio.CancelledError):
        await validate_pdf_structure_isolated(Path("unused.pdf"))


@pytest.mark.asyncio
async def test_isolated_validation_empty_stdout_is_validator_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A silent child cannot be treated as a valid document."""

    class SilentProcess:
        returncode = 1

        async def communicate(self) -> tuple[bytes, bytes]:
            return b"", b""

        def kill(self) -> None:
            raise AssertionError("silent children must not be killed")

        async def wait(self) -> int:
            return 1

    async def factory(*_args: object, **_kwargs: object) -> SilentProcess:
        return SilentProcess()

    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.resource_limits_supported",
        lambda: True,
    )
    monkeypatch.setattr(
        "newsdom_api.pdf_structure_validator.asyncio.create_subprocess_exec",
        factory,
    )
    outcome = await validate_pdf_structure_isolated(Path("unused.pdf"))
    assert outcome is ValidationOutcome.VALIDATOR_FAILURE


@pytest.mark.asyncio
async def test_http_mapping_accepts_valid_outcome(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A valid isolated outcome must not raise into the `/parse` contract."""

    from newsdom_api.main import _validate_pdf_structure

    async def valid(_file_path: Path) -> ValidationOutcome:
        return ValidationOutcome.VALID

    monkeypatch.setattr(
        "newsdom_api.main.validate_pdf_structure_isolated", valid
    )
    await _validate_pdf_structure(tmp_path / "upload.pdf")


@pytest.mark.asyncio
async def test_http_mapping_uses_fixed_415_and_503(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Callers see only the fixed media-type or service-unavailable details."""

    from newsdom_api.main import (
        SERVICE_UNAVAILABLE_DETAIL,
        UNSUPPORTED_MEDIA_DETAIL,
        _validate_pdf_structure,
    )

    path = tmp_path / "upload.pdf"
    path.write_bytes(b"%PDF-1.4\n%%EOF")

    async def invalid(_file_path: Path) -> ValidationOutcome:
        return ValidationOutcome.INVALID_DOCUMENT

    monkeypatch.setattr(
        "newsdom_api.main.validate_pdf_structure_isolated", invalid
    )
    with pytest.raises(HTTPException) as invalid_info:
        await _validate_pdf_structure(path)
    assert invalid_info.value.status_code == 415
    assert invalid_info.value.detail == UNSUPPORTED_MEDIA_DETAIL
    assert invalid_info.value.__cause__ is None
    assert "/tmp/" not in str(invalid_info.value.detail)

    async def failed(_file_path: Path) -> ValidationOutcome:
        return ValidationOutcome.VALIDATOR_FAILURE

    monkeypatch.setattr(
        "newsdom_api.main.validate_pdf_structure_isolated", failed
    )
    with pytest.raises(HTTPException) as failed_info:
        await _validate_pdf_structure(path)
    assert failed_info.value.status_code == 503
    assert failed_info.value.detail == SERVICE_UNAVAILABLE_DETAIL
