"""Upload-ingestion evidence must not silently select a new chunk size."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from newsdom_api.main import PARSE_UPLOAD_CHUNK_BYTES
from tools.benchmark_upload_ingestion import (
    CHUNK_ALIASES,
    main,
    run_cases,
    _read_calls_for_chunk,
    _sample_vmrss_kib,
)


def test_smoke_benchmark_keeps_rollback_chunk(tmp_path: Path) -> None:
    """A smoke run records 8 KiB evidence and refuses to select production."""

    output = tmp_path / "upload-ingestion-result.json"
    assert main(["--smoke", "--output", str(output)]) == 0
    document = json.loads(output.read_text(encoding="utf-8"))
    assert document["selects_production_chunk"] is False
    assert document["rollback_chunk_bytes"] == PARSE_UPLOAD_CHUNK_BYTES == 8192
    assert document["cases"][0]["chunk_bytes"] == 8192
    assert document["cases"][0]["concurrency"] == 1
    assert len(document["cases"][0]["fixture_sha256"]) == 64


def test_read_call_count_matches_payload_size() -> None:
    """A 20 KiB body at 8 KiB must take three reads, not a guessed 1 MiB."""

    assert _read_calls_for_chunk(b"x" * 20480, 8192) == 3
    try:
        _read_calls_for_chunk(b"x", 0)
    except ValueError as exc:
        assert "at least 1" in str(exc)
    else:
        raise AssertionError("expected a zero chunk size to fail")


def test_unknown_chunk_alias_fails_closed(tmp_path: Path) -> None:
    """Operators must not invent an undocumented chunk alias."""

    try:
        main(["--chunks", "2mib", "--output", str(tmp_path / "out.json")])
    except SystemExit as exc:
        assert exc.code == "unknown chunk alias: 2mib"
    else:
        raise AssertionError("expected an unknown chunk alias to fail")


def test_full_alias_matrix_records_each_candidate() -> None:
    """The documented aliases stay available for a later reviewed selection."""

    document = run_cases(
        Path("tests/fixtures/synthetic_reference.pdf"),
        list(CHUNK_ALIASES),
        [1],
    )
    assert [case["chunk_bytes"] for case in document["cases"]] == [
        8192,
        65536,
        262144,
        1048576,
    ]
    assert _sample_vmrss_kib() >= 0


def test_matrix_command_writes_requested_concurrency(tmp_path: Path) -> None:
    """A non-smoke run must honor the caller-selected concurrency list."""

    output = tmp_path / "nested" / "result.json"
    assert (
        main(
            [
                "--chunks",
                "8kib",
                "--concurrency",
                "1,8",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    document = json.loads(output.read_text(encoding="utf-8"))
    assert [case["concurrency"] for case in document["cases"]] == [1, 8]


def test_vmrss_sampler_handles_missing_and_incomplete_status(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Memory evidence must not invent a peak when Linux status is unavailable."""

    class MissingStatus:
        def is_file(self) -> bool:
            return False

        def read_text(self, encoding: str = "utf-8") -> str:
            raise AssertionError("missing status files must not be read")

    class IncompleteStatus:
        def is_file(self) -> bool:
            return True

        def read_text(self, encoding: str = "utf-8") -> str:
            return "VmSize:\t1024 kB\n"

    def fake_path(value: str) -> object:
        if value == "/proc/self/status":
            return MissingStatus()
        return Path(value)

    monkeypatch.setattr("tools.benchmark_upload_ingestion.Path", fake_path)
    assert _sample_vmrss_kib() == 0

    def incomplete_path(value: str) -> object:
        if value == "/proc/self/status":
            return IncompleteStatus()
        return Path(value)

    monkeypatch.setattr("tools.benchmark_upload_ingestion.Path", incomplete_path)
    assert _sample_vmrss_kib() == 0
