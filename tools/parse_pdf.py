from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from newsdom_api.service import parse_pdf_bytes


def main(argv: list[str] | None = None) -> None:
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

    if not args.input.is_file():
        print(
            f"Error: The input file {args.input} does not exist or is not a file.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        pdf_bytes = args.input.read_bytes()
        response = parse_pdf_bytes(pdf_bytes, filename=args.input.name)

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
