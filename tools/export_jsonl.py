"""Export NewsDOM JSON to a JSONL file where each line is an article."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _reject_non_finite(token: str) -> float:
    """Reject non-standard float tokens during JSON parsing."""
    raise ValueError(f"Non-standard float token: {token}")


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file with article provenance."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")

    if json_path.resolve() == output_path.resolve() or (output_path.exists() and os.path.samefile(json_path, output_path)):
        raise ValueError("Input and output paths must not be the same file.")

    try:
        json_text = json_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Invalid encoding: {exc}") from exc

    try:
        data = json.loads(json_text, parse_constant=_reject_non_finite)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid JSON data: {exc}") from exc

    document_id = data.get("document_id", "Unknown Document")
    pages = data.get("pages", [])

    with output_path.open("w", encoding="utf-8") as jsonl_file:
        for page in pages:
            if not isinstance(page, dict):
                continue

            page_number = page.get("page_number", "Unknown")
            articles = page.get("articles", [])

            for article in articles:
                if not isinstance(article, dict):
                    continue

                # Copy provenance metadata
                article_data = dict(article)
                article_data["document_id"] = document_id
                article_data["page_number"] = page_number

                jsonl_line = json.dumps(article_data, ensure_ascii=False, allow_nan=False)
                jsonl_file.write(jsonl_line + "\n")


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
