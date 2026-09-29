from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file containing one article per line."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    if json_path.resolve() == output_path.resolve() or (
        output_path.exists() and os.path.samefile(json_path, output_path)
    ):
        raise ValueError("Input and output paths must not be the same file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be a dictionary.")

    document_id = data.get("document_id", "Unknown Document")
    pages = data.get("pages", [])
    if not isinstance(pages, list):
        pages = []

    actual_output = output_path.resolve()
    actual_output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=actual_output.parent, encoding="utf-8"
    ) as temp_file:
        temp_path = Path(temp_file.name)
        try:
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_number = page.get("page_number", "Unknown")
                articles = page.get("articles", [])
                if not isinstance(articles, list):
                    continue

                for article in articles:
                    if not isinstance(article, dict):
                        continue

                    article_copy = article.copy()

                    if "document_id" not in article_copy:
                        article_copy["document_id"] = document_id
                    if "page_number" not in article_copy:
                        article_copy["page_number"] = page_number

                    line = json.dumps(article_copy, ensure_ascii=False, allow_nan=False)
                    temp_file.write(line + "\n")
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise

    if actual_output.exists():
        os.chmod(temp_path, actual_output.stat().st_mode)
    os.replace(temp_path, actual_output)


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "output", type=Path, help="Path to write the JSONL output file."
    )

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except BaseException as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
