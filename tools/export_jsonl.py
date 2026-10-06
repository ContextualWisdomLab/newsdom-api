from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _strict_float(s: str) -> float:
    f = float(s)
    if str(f).lower() in ("nan", "inf", "-inf"):
        raise ValueError("Non-finite float")
    return f


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to JSONL format by articles."""
    if json_path.resolve() == output_path.resolve() or (output_path.exists() and json_path.resolve() == output_path.resolve()):
        raise ValueError("Input and output paths must not be the same")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"), parse_constant=_strict_float)
    except UnicodeDecodeError as exc:
        raise ValueError(f"Invalid JSON encoding: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc
    except ValueError as exc:
        raise ValueError(f"Invalid float: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be a dictionary")

    pages = data.get("pages", [])
    document_id = data.get("document_id", "Unknown Document")

    with output_path.open("w", encoding="utf-8") as f:
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
                record = {"document_id": document_id, "page_number": page_number}
                record.update(article)
                f.write(json.dumps(record, allow_nan=False, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export NewsDOM JSON to JSONL")
    parser.add_argument("input", type=Path, help="Input JSON file")
    parser.add_argument("output", type=Path, help="Output JSONL file")

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
