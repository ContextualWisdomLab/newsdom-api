from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def minify_dom(json_path: Path, output_path: Path | None = None) -> None:
    """Minify NewsDOM JSON to reduce file size."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_bytes())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    out_path = output_path or json_path

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))


def main(argv: list[str] | None = None) -> None:
    """Run the JSON minify CLI."""
    parser = argparse.ArgumentParser(description="Minify a NewsDOM JSON file.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to write the minified JSON file. Defaults to overwriting the input file.",
    )

    args = parser.parse_args(argv)

    try:
        minify_dom(args.input, args.output)
        print(f"JSON successfully minified to {args.output or args.input}")
    except Exception as exc:
        print(f"Error minifying JSON: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
