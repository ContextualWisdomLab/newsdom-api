"""Fuzz and smoke-test the DOM normalization boundary."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Fix relative import when running from root via pyinstaller
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from newsdom_api.dom_builder import build_dom


def _coerce_content_list(candidate: Any) -> list[dict[str, Any]]:
    """Return a MinerU-like content list or an empty list."""

    if not isinstance(candidate, list):
        return []
    return [item for item in candidate if isinstance(item, dict)]


def exercise_dom_builder(raw_bytes: bytes) -> None:
    """Exercise build_dom with bytes that may or may not decode into JSON blocks."""

    try:
        decoded = raw_bytes.decode("utf-8", errors="ignore")
        candidate = json.loads(decoded)
    except json.JSONDecodeError:
        return
    build_dom(_coerce_content_list(candidate), document_id="fuzz")


def _run_smoke(seed_path: Path) -> None:
    """Run one deterministic normalization pass from a known corpus seed."""

    sample = json.loads(seed_path.read_text(encoding="utf-8"))
    build_dom(_coerce_content_list(sample), document_id="smoke")


def main(argv: list[str] | None = None) -> int:
    """Run either deterministic smoke mode or Atheris fuzz mode."""

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--smoke", type=Path)
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    args, forwarded = parser.parse_known_args(raw_argv)

    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]

    if args.smoke is not None:
        if forwarded:
            parser.error(f"unrecognized arguments: {' '.join(forwarded)}")
        _run_smoke(args.smoke)
        return 0

    import atheris

    def test_one_input(data: bytes) -> None:
        exercise_dom_builder(data)

    atheris.Setup([sys.argv[0], *forwarded], test_one_input)
    atheris.Fuzz()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
