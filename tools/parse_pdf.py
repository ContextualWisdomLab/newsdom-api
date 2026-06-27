"""
CLI tool for parse_pdf.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
sys.path.insert(0, str(_SRC_ROOT))

from newsdom_api.service import parse_pdf_bytes  # noqa: E402


def _resolve_pdf_input(input_path: Path) -> Path:
    """Resolve a local PDF input while rejecting traversal-style paths."""

    if ".." in input_path.parts:
        raise ValueError("The input path must not contain parent directory segments.")
    if input_path.suffix.lower() != ".pdf":
        raise ValueError("The input file must use a .pdf extension.")
    if not input_path.is_file():
        raise ValueError(
            f"The input file {input_path} does not exist or is not a file."
        )
    return input_path.resolve(strict=True)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Parse a Japanese newspaper PDF and output the resulting DOM as JSON."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input PDF file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write the JSON output. If not provided, output will be printed to stdout.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation level for JSON output (default: 2).",
    )

    args = parser.parse_args(argv)

    try:
        input_path = _resolve_pdf_input(args.input)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        pdf_bytes = input_path.read_bytes()
        response = parse_pdf_bytes(pdf_bytes, filename=input_path.name)

        # Serialize to dictionary for JSON output
        output_dict = response.model_dump(mode="json")
        json_output = json.dumps(output_dict, ensure_ascii=False, indent=args.indent)

        if args.output:
            args.output.write_text(json_output, encoding="utf-8")
            print(f"Output written to {args.output}")
        else:
            print(json_output)

    except Exception as e:
        print(f"An error occurred while parsing the PDF: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
