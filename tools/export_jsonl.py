from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON pages and articles to a JSONL file.

    This preserves output files in case of encoding or writing failures by using atomic replacement.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])

    # Write to a temporary file in the same directory to avoid cross-device link errors
    temp_file = NamedTemporaryFile(
        delete=False, dir=output_path.parent, mode="w", encoding="utf-8"
    )
    try:
        for page in pages:
            if not isinstance(page, dict):
                continue

            articles = page.get("articles", [])
            for article in articles:
                if not isinstance(article, dict):
                    continue

                # We could attach document_id and page_number if we want context
                # but following typical JSONL dump patterns
                temp_file.write(json.dumps(article, ensure_ascii=False) + "\n")

        temp_file.flush()
        os.fsync(temp_file.fileno())
        temp_file.close()

        # Atomic replacement
        os.replace(temp_file.name, output_path)
    except Exception:
        # Clean up temp file on failure, preserving original if it existed
        temp_file.close()
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        raise


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI.

    Provides command line interface for JSONL exportation.
    """
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "output", type=Path, help="Path to write the JSONL output file."
    )

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
