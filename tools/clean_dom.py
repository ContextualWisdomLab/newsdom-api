from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def clean_dom(json_path: Path, output_path: Path) -> None:
    """Remove ads, headers, and footers from a NewsDOM JSON file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input must be a .json file.")
    if output_path.suffix.lower() != ".json":
        raise ValueError("Output must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))

    pages = data.get("pages", [])
    for page in pages:
        if "ads" in page:
            page["ads"] = []
        if "headers" in page:
            page["headers"] = []
        if "footers" in page:
            page["footers"] = []

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run clean_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Clean ads, headers, and footers from NewsDOM JSON output."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        clean_dom(args.input, args.output)
        print(f"Successfully cleaned DOM and saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
