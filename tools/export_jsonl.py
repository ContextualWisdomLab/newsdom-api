from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file containing one article per line."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")
    if json_path.resolve() == output_path.resolve():
        raise ValueError("Input and output files must not be the same.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    document_id = data.get("document_id", "Unknown Document")

    # Use atomic write strategy: write to a temporary file then replace
    import os

    tmp_path = output_path.with_name(f".{output_path.name}.tmp")

    try:
        with tmp_path.open("w", encoding="utf-8") as jsonlfile:
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_number = page.get("page_number", "Unknown")

                articles = page.get("articles", [])
                for article in articles:
                    if not isinstance(article, dict):
                        continue

                    # Ensure provenance metadata is present
                    article_copy = dict(article)
                    if "document_id" not in article_copy:
                        article_copy["document_id"] = document_id
                    if "page_number" not in article_copy:
                        article_copy["page_number"] = page_number

                    json_str = json.dumps(article_copy, ensure_ascii=False, allow_nan=False)
                    jsonlfile.write(json_str + "\n")

        os.replace(tmp_path, output_path)
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        raise exc


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
