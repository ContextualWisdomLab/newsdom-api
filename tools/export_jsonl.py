import argparse
import json
import os
import sys
from pathlib import Path


def reject_non_finite(x: str) -> float:
    """Reject non-finite numbers when parsing JSON."""
    raise ValueError(f"Non-standard float token: {x}")


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON articles to a JSONL file."""
    if json_path.resolve() == output_path.resolve() or (output_path.exists() and os.path.samefile(json_path, output_path)):
        raise ValueError("Input and output paths must not refer to the same file.")

    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")

    try:
        text = json_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"File encoding error: {exc}") from exc

    try:
        data = json.loads(text, parse_constant=reject_non_finite)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON structure must be a dictionary.")

    document_id = data.get("document_id")

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        pages = []

    with output_path.open("w", encoding="utf-8") as out_file:
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
                # Copy provenance metadata
                if document_id is not None:
                    article["document_id"] = document_id
                if page_number is not None:
                    article["page_number"] = page_number

                line = json.dumps(article, allow_nan=False)
                out_file.write(line + "\n")


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export NewsDOM JSON articles to JSONL format.")
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
