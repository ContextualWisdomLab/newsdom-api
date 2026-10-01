from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file with article metadata."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:

        def _reject_non_finite(token: str) -> None:
            raise ValueError(f"Non-standard token: {token}")

        data = json.loads(
            json_path.read_text(encoding="utf-8"),
            parse_constant=_reject_non_finite,
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid JSON file (non-standard tokens): {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("NewsDOM root must be an object.")

    document_id = data.get("document_id", "Unknown Document")
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        raise ValueError("NewsDOM pages must be an array.")

    json_lines: list[str] = []
    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            raise ValueError(f"NewsDOM pages[{page_index}] must be an object.")
        page_number = page.get("page_number", "Unknown")
        articles = page.get("articles", [])
        if not isinstance(articles, list):
            raise ValueError(
                f"NewsDOM pages[{page_index}].articles must be an array."
            )
        for article_index, article in enumerate(articles):
            if not isinstance(article, dict):
                raise ValueError(
                    "NewsDOM "
                    f"pages[{page_index}].articles[{article_index}] "
                    "must be an object."
                )
            article_data = article.copy()
            article_data["document_id"] = document_id
            article_data["page_number"] = page_number
            json_lines.append(
                json.dumps(article_data, ensure_ascii=False, allow_nan=False)
            )

    with output_path.open("w", encoding="utf-8") as jsonl_file:
        for json_line in json_lines:
            jsonl_file.write(json_line + "\n")


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
