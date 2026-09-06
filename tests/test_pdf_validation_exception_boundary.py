"""Tests for the untrusted PDF parser exception boundary."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from newsdom_api.main import _validate_pdf_structure


class UnexpectedParserError(Exception):
    """Represent one ordinary third-party parser exception outside known subclasses."""


def test_unexpected_parser_exception_maps_to_fixed_unsupported_media(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Ordinary parser failures must not escape the upload-validation boundary."""

    def fail_reader(*_args, **_kwargs):
        raise UnexpectedParserError("parser internals must not escape")

    monkeypatch.setattr("newsdom_api.main.PdfReader", fail_reader)
    candidate = tmp_path / "candidate.pdf"
    candidate.write_bytes(b"%PDF-1.7\n")

    with pytest.raises(HTTPException) as captured:
        _validate_pdf_structure(candidate)

    assert captured.value.status_code == 415
    assert captured.value.detail == "Unsupported Media Type"
    assert "parser internals" not in str(captured.value.detail)


def test_process_control_base_exception_is_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The parser boundary must not catch BaseException process-control signals."""

    def interrupt_reader(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("newsdom_api.main.PdfReader", interrupt_reader)
    candidate = tmp_path / "candidate.pdf"
    candidate.write_bytes(b"%PDF-1.7\n")

    with pytest.raises(KeyboardInterrupt):
        _validate_pdf_structure(candidate)
