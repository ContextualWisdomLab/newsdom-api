from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def _reject_non_finite(token: str) -> float:
    """Reject a non-standard non-finite JSON number token."""

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

    actual_output = output_path.resolve()
    existing_mode = actual_output.stat().st_mode if actual_output.exists() else None
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=actual_output.parent,
            prefix=f".{actual_output.name}.",
            suffix=".tmp",
            delete=False,
        ) as jsonlfile:
            temp_path = Path(jsonlfile.name)
            for page_index, page in enumerate(pages):
                if not isinstance(page, dict):
                    raise ValueError(f"pages[{page_index}] must be an object")
                page_number = page.get("page_number", "Unknown")

                articles = page.get("articles", [])
                if not isinstance(articles, list):
                    raise ValueError(
                        f"pages[{page_index}].articles must be a list"
                    )

                for article_index, article in enumerate(articles):
                    if not isinstance(article, dict):
                        raise ValueError(
                            f"pages[{page_index}].articles[{article_index}] "
                            "must be an object"
                        )

                    out_article = article.copy()
                    out_article["document_id"] = document_id
                    out_article["page_number"] = page_number

                    line = json.dumps(out_article, allow_nan=False)
                    jsonlfile.write(line + "\n")

        os.replace(temp_path, actual_output)
        if existing_mode is not None:
            os.chmod(actual_output, existing_mode)
    except Exception:
        if temp_path is not None and temp_path.exists():
            try:
                os.unlink(temp_path)
            except Exception:  # Ignore cleanup errors
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
