from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from newsdom_api.schemas import ParseResponse


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export canonical NewsDOM sections to JSONL without dropping provenance fields."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    try:
        document = ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError("Input is not canonical NewsDOM JSON") from exc

    with output_path.open("w", encoding="utf-8") as jsonlfile:
        for page in document.pages:
            for article in page.articles:
                article_data = {
                    "document_id": document.document_id,
                    "page_number": page.page_number,
                    **article.model_dump(mode="json"),
                }
                jsonlfile.write(json.dumps(article_data, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> None:
    """Run the canonical NewsDOM JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(
        description="Export canonical NewsDOM JSON sections to JSONL."
    )
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
