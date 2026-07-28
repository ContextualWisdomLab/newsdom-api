"""Invoke MinerU as an external parser and collect its structured outputs."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from .errors import MineruIncompleteOutputError, MineruRuntimeUnavailableError

# ⚡ Bolt: Use a pre-compiled regex to push pattern matching to C,
# avoiding the Python-level overhead of `any()` and generator comprehensions
_UNSAFE_CHARS_PATTERN = re.compile(r"[\0&;|`$<>\n\r]")

# MinerU 3.4.4's public CLI defaults to ``ch``. That model covers Chinese,
# English, Japanese, Traditional Chinese, and Latin; callers can select another
# supported script family through the request parameter.
DEFAULT_LANGUAGE = "ch"
DEFAULT_MODE = "auto"

# Parsing modes understood by MinerU's ``-m`` flag. ``auto`` picks txt vs. ocr
# per document, ``ocr`` forces optical recognition, ``txt`` extracts the
# embedded text layer only.
VALID_MODES = frozenset({"auto", "ocr", "txt"})

# Public language keys accepted by MinerU 3.4.4's CLI. Keeping this contract
# locally lets the API return a client-visible 422 instead of a downstream 503.
VALID_LANGUAGES = frozenset(
    {
        "ch",
        "ch_server",
        "korean",
        "ta",
        "te",
        "ka",
        "th",
        "el",
        "arabic",
        "east_slavic",
        "cyrillic",
        "devanagari",
    }
)

# Compatibility aliases published by MinerU. Aliases are canonicalized before
# subprocess execution so behavior does not depend on a particular CLI wrapper.
_LANGUAGE_ALIASES = {
    "en": "ch",
    "japan": "ch",
    "chinese_cht": "ch",
    "latin": "ch",
    "ar": "arabic",
    "fa": "arabic",
    "ug": "arabic",
    "ur": "arabic",
    "ps": "arabic",
    "ku": "arabic",
    "sd": "arabic",
    "bal": "arabic",
    "ru": "east_slavic",
    "be": "east_slavic",
    "uk": "east_slavic",
    "hi": "devanagari",
    "mr": "devanagari",
    "ne": "devanagari",
    "bh": "devanagari",
    "mai": "devanagari",
    "ang": "devanagari",
    "bho": "devanagari",
    "mah": "devanagari",
    "sck": "devanagari",
    "new": "devanagari",
    "gom": "devanagari",
    "sa": "devanagari",
    "bgc": "devanagari",
    "rs_cyrillic": "cyrillic",
    "bg": "cyrillic",
    "mn": "cyrillic",
    "abq": "cyrillic",
    "ady": "cyrillic",
    "kbd": "cyrillic",
    "ava": "cyrillic",
    "dar": "cyrillic",
    "inh": "cyrillic",
    "che": "cyrillic",
    "lbe": "cyrillic",
    "lez": "cyrillic",
    "tab": "cyrillic",
    "kk": "cyrillic",
    "ky": "cyrillic",
    "tg": "cyrillic",
    "mk": "cyrillic",
    "tt": "cyrillic",
    "cv": "cyrillic",
    "ba": "cyrillic",
    "mhr": "cyrillic",
    "mo": "cyrillic",
    "udm": "cyrillic",
    "kv": "cyrillic",
    "os": "cyrillic",
    "bua": "cyrillic",
    "xal": "cyrillic",
    "tyv": "cyrillic",
    "sah": "cyrillic",
    "kaa": "cyrillic",
}

# Method subdirectories MinerU may create beneath the output directory.
_KNOWN_METHOD_DIRS = ("auto", "ocr", "txt")


def normalize_mode(mode: str) -> str:
    """Validate and normalize a MinerU parsing mode.

    Returns the lower-cased mode when it is one of ``auto``/``ocr``/``txt`` and
    raises :class:`ValueError` otherwise so callers can surface a client error.
    """

    normalized = str(mode).strip().lower()
    if normalized not in VALID_MODES:
        raise ValueError(f"Unsupported MinerU mode: {mode!r}")
    return normalized


def normalize_language(language: str) -> str:
    """Validate and normalize a MinerU language code.

    Returns the canonical MinerU 3.4.4 public language key and raises
    :class:`ValueError` otherwise so callers receive a client error instead of
    a downstream runtime failure.
    """

    normalized = str(language).strip().lower()
    canonical = _LANGUAGE_ALIASES.get(normalized, normalized)
    if canonical not in VALID_LANGUAGES:
        raise ValueError(f"Unsupported MinerU language: {language!r}")
    return canonical


def _mineru_command_arg(value: str | Path, *, label: str) -> str:
    """Validate a path or executable string before passing it to MinerU argv."""

    value_str = str(value)
    if _UNSAFE_CHARS_PATTERN.search(value_str):
        raise ValueError(f"Unsafe {label} for MinerU command")
    if value_str.startswith("-"):
        raise ValueError(f"Unsafe {label} for MinerU command")
    return value_str


def build_mineru_command(
    input_pdf: Path,
    output_dir: Path,
    mineru_bin: str = "mineru",
    *,
    language: str = DEFAULT_LANGUAGE,
    mode: str = DEFAULT_MODE,
) -> list[str]:
    """Build the MinerU CLI command for pipeline execution.

    ``language`` maps to MinerU's ``-l`` flag and ``mode`` to ``-m``. Both are
    validated so callers cannot inject arbitrary argv values; the defaults are
    aligned with MinerU 3.4.4 (``ch``/``auto``).
    """

    validated_mode = normalize_mode(mode)
    validated_language = normalize_language(language)

    return [
        _mineru_command_arg(mineru_bin, label="MinerU executable"),
        "-p",
        _mineru_command_arg(input_pdf, label="input PDF path"),
        "-o",
        _mineru_command_arg(output_dir, label="output directory path"),
        "-b",
        "pipeline",
        "-m",
        validated_mode,
        "-l",
        validated_language,
    ]


@lru_cache
def _cached_which(cmd: str) -> str | None:
    """Cache shutil.which to avoid redundant filesystem lookups."""
    return shutil.which(cmd)


def _resolve_mineru_bin() -> str:
    """Resolve the MinerU executable path for this process.

    The shutil.which result is cached, but NEWSDOM_MINERU_BIN is evaluated
    on every call to allow runtime overrides.
    """

    configured = os.environ.get("NEWSDOM_MINERU_BIN")
    if configured:
        return configured
    found = _cached_which("mineru")
    if not found:
        raise MineruRuntimeUnavailableError(
            stderr=(
                "Could not find 'mineru' executable. "
                "Ensure it is installed and on the PATH, or set NEWSDOM_MINERU_BIN."
            )
        )
    return found


def _find_output_dir(base_output_dir: Path, method: str = DEFAULT_MODE) -> Path:
    """Locate the parse-method output directory created by MinerU.

    MinerU writes results under ``<base>/<document>/<method>/`` where the method
    subdirectory reflects the parsing mode. The requested ``method`` is tried
    first, then the other known method directories, so ``auto`` runs that
    resolve to a concrete txt/ocr layout are still discovered.
    """

    search_order = [method, *(m for m in _KNOWN_METHOD_DIRS if m != method)]
    for candidate_method in search_order:
        try:
            return next(base_output_dir.glob(f"*/{candidate_method}"))
        except StopIteration:
            continue
    raise FileNotFoundError("MinerU output directory was not produced")


def _execute_mineru(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    """Execute the MinerU command and handle runtime errors."""
    try:
        return subprocess.run(
            cmd, check=True, capture_output=True, text=True, timeout=300, shell=False
        )
    except subprocess.TimeoutExpired as exc:
        stdout_str = (
            exc.stdout.decode("utf-8", "replace")
            if isinstance(exc.stdout, bytes)
            else exc.stdout
        )
        raise MineruRuntimeUnavailableError(
            returncode=-1,
            stdout=stdout_str or "",
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


def _read_mineru_json(path: Path, *, artifact: str) -> Any:
    """Read a MinerU JSON artifact with safe, differentiated failure messages."""
    try:
        # ⚡ Bolt: Passing read_bytes() directly to json.loads() avoids intermediate string allocation
        return json.loads(path.read_bytes())
    except json.JSONDecodeError as exc:
        raise MineruIncompleteOutputError(f"{artifact} JSON was malformed") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise MineruIncompleteOutputError(f"{artifact} JSON could not be read") from exc


def _parse_mineru_output(
    output_dir: Path, input_pdf: Path, method: str = DEFAULT_MODE
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse the JSON outputs generated by MinerU."""
    try:
        ocr_dir = _find_output_dir(output_dir, method)
        content_path = ocr_dir / f"{input_pdf.stem}_content_list.json"
        if not content_path.exists():
            try:
                content_path = next(ocr_dir.glob("*_content_list.json"))
            except StopIteration:
                raise FileNotFoundError("MinerU content list JSON was not produced")
        try:
            model_path = next(ocr_dir.glob("*_model.json"))
        except StopIteration:
            raise FileNotFoundError("MinerU model JSON was not produced")
    except FileNotFoundError as exc:
        raise MineruIncompleteOutputError() from exc
    content_list = _read_mineru_json(content_path, artifact="content list")
    model = _read_mineru_json(model_path, artifact="model")

    return content_list, model


def run_mineru(
    input_pdf: Path,
    *,
    language: str = DEFAULT_LANGUAGE,
    mode: str = DEFAULT_MODE,
) -> dict[str, Any]:
    """Run MinerU on a PDF and return parsed JSON artifacts plus raw process output.

    ``language`` and ``mode`` are forwarded to the MinerU CLI (validated by
    :func:`build_mineru_command`). PATH lookups for the default MinerU
    executable are cached, while NEWSDOM_MINERU_BIN is evaluated on each call to
    allow runtime overrides.
    """

    resolved_mode = normalize_mode(mode)
    mineru_bin = _resolve_mineru_bin()
    with tempfile.TemporaryDirectory(prefix="newsdom-mineru-") as tempdir:
        output_dir = Path(tempdir)
        cmd = build_mineru_command(
            input_pdf,
            output_dir,
            mineru_bin=mineru_bin,
            language=language,
            mode=resolved_mode,
        )

        completed = _execute_mineru(cmd)
        content_list, model = _parse_mineru_output(output_dir, input_pdf, resolved_mode)

        return {
            "content_list": content_list,
            "model": model,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
