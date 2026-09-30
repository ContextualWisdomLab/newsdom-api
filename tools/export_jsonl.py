from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")
    try:
        def reject_non_standard(token: str) -> float:
            raise ValueError(f"Non-standard float found: {token}")
        data = json.loads(json_path.read_text(encoding="utf-8"), parse_constant=reject_non_standard)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Invalid JSON format: Top-level object must be a dictionary.")

    document_id = data.get("document_id")

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("Invalid JSON format: 'pages' must be a list.")

    with output_path.open("w", encoding="utf-8") as f:
        for page in pages:
            if not isinstance(page, dict):
                continue

            page_number = page.get("page_number")
            articles = page.get("articles", [])

            if not isinstance(articles, list):
                continue

            for article in articles:
                if not isinstance(article, dict):
                    continue

                # Create a new dict for output to avoid modifying original and preserve ordering
                out_article: dict[str, Any] = {}

                # Check for document_id in article; if not present, take from root
                if "document_id" not in article and document_id is not None:
                    out_article["document_id"] = document_id

                # Check for page_number in article; if not present, take from page
                if "page_number" not in article and page_number is not None:
                    out_article["page_number"] = page_number

                out_article.update(article)

                f.write(json.dumps(out_article, allow_nan=False, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the JSONL output file.")

    args = parser.parse_args(argv)

    try:
        if args.input.resolve() == args.output.resolve() or (args.output.exists() and args.input.samefile(args.output)):
            raise ValueError("Input and output paths cannot refer to the same file.")

        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
