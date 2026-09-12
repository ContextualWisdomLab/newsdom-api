from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def export_csv(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a CSV file containing article metadata and body blocks."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "document_id",
            "page_number",
            "article_id",
            "headline",
            "body_block_index",
            "body_block_text",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        document_id = data.get("document_id", "Unknown Document")

        for page in pages:
            if not isinstance(page, dict):
                continue
            page_number = page.get("page_number", "Unknown")

            articles = page.get("articles", [])
            for article in articles:
                if not isinstance(article, dict):
                    continue
                article_id = article.get("article_id", "Unknown Article ID")
                headline = article.get("headline", "")

                body_blocks = article.get("body_blocks", [])

                if not body_blocks:
                    writer.writerow(
                        {
                            "document_id": document_id,
                            "page_number": page_number,
                            "article_id": article_id,
                            "headline": headline,
                            "body_block_index": "",
                            "body_block_text": "",
                        }
                    )

                for idx, block in enumerate(body_blocks):
                    writer.writerow(
                        {
                            "document_id": document_id,
                            "page_number": page_number,
                            "article_id": article_id,
                            "headline": headline,
                            "body_block_index": idx,
                            "body_block_text": block,
                        }
                    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-CSV export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to CSV.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the CSV output file.")

    args = parser.parse_args(argv)

    try:
        export_csv(args.input, args.output)
        print(f"CSV successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting CSV: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
