from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def export_jsonl(input_dir: Path, output_file: Path, recursive: bool = False) -> None:
    """Export multiple NewsDOM JSON files into a single JSONL file."""
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input is not a directory: {input_dir}")

    json_files = sorted(
        input_dir.rglob("*.json") if recursive else input_dir.glob("*.json")
    )

    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {input_dir}")

    with output_file.open("w", encoding="utf-8") as out:
        for json_path in json_files:
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(
                    f"Skipping invalid JSON file {json_path.name}: {exc}",
                    file=sys.stderr,
                )
                continue

            document_id = data.get("document_id", "Unknown Document")
            pages = data.get("pages", [])

            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_number = page.get("page_number", "Unknown")

                for article in page.get("articles", []):
                    if not isinstance(article, dict):
                        continue

                    record = {
                        "document_id": document_id,
                        "page_number": page_number,
                        "article_id": article.get("article_id"),
                        "headline": article.get("headline"),
                        "body_blocks": article.get("body_blocks", []),
                    }
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> None:
    """Run export_jsonl main entry point."""
    parser = argparse.ArgumentParser(
        description="Export multiple NewsDOM JSON files into a single JSONL file."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing JSON files.")
    parser.add_argument("output_file", type=Path, help="Path to save JSONL output.")
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search for JSON files under the input directory.",
    )

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input_dir, args.output_file, args.recursive)
        print(f"JSONL successfully written to {args.output_file}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
