from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _reject_non_finite(token: str) -> float:
    raise ValueError(f"Non-standard float token not allowed: {token}")


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to a JSONL file containing individual articles."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    if json_path.resolve() == output_path.resolve() or (
        output_path.exists() and os.path.samefile(json_path, output_path)
    ):
        raise ValueError("Input and output paths must not refer to the same file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"), parse_constant=_reject_non_finite)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Top-level parsed object must be a dictionary.")

    document_id = data.get("document_id", "Unknown Document")
    pages = data.get("pages", [])

    if not isinstance(pages, list):
        raise ValueError("'pages' field must be a list.")

    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    actual_output = output_path.resolve()

    try:
        with temp_path.open("w", encoding="utf-8") as jsonlfile:
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

                    out_article = article.copy()
                    out_article["document_id"] = document_id
                    out_article["page_number"] = page_number

                    line = json.dumps(out_article, allow_nan=False)
                    jsonlfile.write(line + "\n")

        if actual_output.exists():
            os.chmod(temp_path, actual_output.stat().st_mode)
        else:
            umask = os.umask(0)
            os.umask(umask)
            os.chmod(temp_path, 0o666 & ~umask)

        os.replace(temp_path, actual_output)
    except Exception:
        if temp_path.exists():
            try:
                os.unlink(temp_path)
            except Exception: # Ignore cleanup errors
                pass
        raise


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
