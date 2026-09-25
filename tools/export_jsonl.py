from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def export_jsonl(input_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file atomically."""
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {input_path}")
    if input_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=output_path.parent, encoding="utf-8"
    )

    try:
        for page in pages:
            if not isinstance(page, dict):
                continue
            articles = page.get("articles", [])
            for article in articles:
                if not isinstance(article, dict):
                    continue
                temp_file.write(json.dumps(article, ensure_ascii=False) + "\n")
        temp_file.close()
        os.replace(temp_file.name, output_path)
    except Exception:
        temp_file.close()
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the JSONL output file.")

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
