"""Invoke MinerU as an external parser and collect its structured outputs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError


def build_mineru_command(
    input_pdf: Path, output_dir: Path, mineru_bin: str = "mineru"
) -> list[str]:
    """Build the MinerU CLI command for OCR pipeline execution."""

    return [
        mineru_bin,
        "-p",
        str(input_pdf),
        "-o",
        str(output_dir),
        "-b",
        "pipeline",
        "-m",
        "ocr",
        "-l",
        "japan",
    ]


def _resolve_mineru_bin() -> str:
    """Resolve the MinerU executable path from env override or PATH."""

    configured = os.environ.get("NEWSDOM_MINERU_BIN")
    if configured:
        return configured
    found = shutil.which("mineru")
    if not found:
        raise FileNotFoundError(
            "Could not find 'mineru' executable. "
            "Ensure it is installed and on the PATH, or set NEWSDOM_MINERU_BIN."
        )
    return found


def _find_output_dir(base_output_dir: Path) -> Path:
    """Locate the OCR output directory created by MinerU."""

    candidates = list(base_output_dir.glob("*/ocr"))
    if not candidates:
        raise FileNotFoundError("MinerU OCR output directory was not produced")
    return candidates[0]


def run_mineru(input_pdf: Path) -> dict[str, Any]:
    """Run MinerU on a PDF and return parsed JSON artifacts plus raw process output."""

    mineru_bin = _resolve_mineru_bin()
    with tempfile.TemporaryDirectory(prefix="newsdom-mineru-") as tempdir:
        output_dir = Path(tempdir)
        cmd = build_mineru_command(input_pdf, output_dir, mineru_bin=mineru_bin)
        try:
            completed = subprocess.run(
                cmd, check=True, capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired as exc:
            raise MineruRuntimeUnavailableError(
                returncode=-1,
                stdout=exc.stdout if exc.stdout else "",
                stderr="OCR processing timed out after 5 minutes",
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise MineruRuntimeUnavailableError(
                returncode=exc.returncode,
                stdout=exc.output,
                stderr=exc.stderr,
            ) from exc
        except FileNotFoundError as exc:
            raise MineruRuntimeUnavailableError() from exc
        try:
            ocr_dir = _find_output_dir(output_dir)
            content_path = ocr_dir / f"{input_pdf.stem}_content_list.json"
            if not content_path.exists():
                json_candidates = sorted(ocr_dir.glob("*_content_list.json"))
                if not json_candidates:
                    raise FileNotFoundError("MinerU content list JSON was not produced")
                content_path = json_candidates[0]
            model_candidates = sorted(ocr_dir.glob("*_model.json"))
            if not model_candidates:
                raise FileNotFoundError("MinerU model JSON was not produced")
        except FileNotFoundError as exc:
            raise MineruIncompleteOutputError() from exc
        try:
            content_list = json.loads(content_path.read_text(encoding="utf-8"))
            model = json.loads(model_candidates[0].read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise MineruIncompleteOutputError() from exc
        return {
            "content_list": content_list,
            "model": model,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
