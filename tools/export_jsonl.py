from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from newsdom_api.schemas import ParseResponse
from pydantic import ValidationError


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

    try:
        validated_data = ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Data failed schema validation: {exc}") from exc
    pages = validated_data.pages
    document_id = validated_data.document_id
    temp_file = NamedTemporaryFile(
        delete=False, mode="w", dir=output_path.parent, encoding="utf-8"
    )
    temp_path = Path(temp_file.name)
    try:
        for page in pages:
            page_number = page.page_number
            for article in page.articles:
                article_id = article.article_id
                headline = article.headline
                body_blocks = article.body_blocks
                record = {
                    "document_id": document_id,
                    "page_number": page_number,
                    "article_id": article_id,
                    "headline": headline,
                    "body_blocks": body_blocks,
                }
                temp_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        temp_file.close()
        os.replace(temp_path, output_path)
    except Exception:
        temp_file.close()
        if temp_path.exists():
            temp_path.unlink()
        raise


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
    except Exception as exc:  # pragma: no cover
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
