from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file containing article metadata and body blocks."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    document_id = data.get("document_id", "Unknown Document")

    # To pass data preservation tests, write to a temporary file first
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with NamedTemporaryFile(mode="w", dir=output_path.parent, delete=False, encoding="utf-8") as temp_file:
            temp_path = Path(temp_file.name)
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_number = page.get("page_number", "Unknown")

                articles = page.get("articles", [])
                for article in articles:
                    if not isinstance(article, dict):
                        continue

                    # Create a record for each article
                    record = {
                        "document_id": document_id,
                        "page_number": page_number,
                        "article_id": article.get("article_id", "Unknown Article ID"),
                        "headline": article.get("headline", ""),
                        "body_blocks": article.get("body_blocks", [])
                    }
                    temp_file.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Atomically replace the destination file
        os.replace(temp_path, output_path)
    except Exception:
        if 'temp_path' in locals() and temp_path.exists():
            temp_path.unlink()
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
