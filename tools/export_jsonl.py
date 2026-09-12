from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from contextlib import suppress
from pathlib import Path

from pydantic import ValidationError

from newsdom_api.schemas import ParseResponse


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export a canonical NewsDOM parse response as article/body-block JSONL."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    try:
        parsed = ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError("Input must be a valid NewsDOM parse response") from exc

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=output_path.parent,
        ) as file_handle:
            temp_path = Path(file_handle.name)
            for page in parsed.pages:
                for article in page.articles:
                    if not article.body_blocks:
                        record = {
                            "document_id": parsed.document_id,
                            "page_number": page.page_number,
                            "article_id": article.article_id,
                            "headline": article.headline,
                            "body_block_index": "",
                            "body_block_text": "",
                        }
                        file_handle.write(
                            json.dumps(record, ensure_ascii=False) + "\n"
                        )

                    for index, block in enumerate(article.body_blocks):
                        record = {
                            "document_id": parsed.document_id,
                            "page_number": page.page_number,
                            "article_id": article.article_id,
                            "headline": article.headline,
                            "body_block_index": index,
                            "body_block_text": block,
                        }
                        file_handle.write(
                            json.dumps(record, ensure_ascii=False) + "\n"
                        )

        os.replace(temp_path, output_path)
    except Exception:
        if temp_path is not None and temp_path.exists():
            with suppress(OSError):
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
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
