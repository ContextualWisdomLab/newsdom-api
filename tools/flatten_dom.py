from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def _strict_parse_constant(c: str) -> float:
    raise ValueError(f"Strict JSON parsing rejected non-standard constant: {c}")


def flatten_dom(json_path: Path, output_path: Path) -> None:
    """Flatten a NewsDOM JSON file into a single array of articles."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    if json_path.resolve() == output_path.resolve():
        raise ValueError("Input and output paths must not be the same file.")

    try:
        data = json.loads(
            json_path.read_text(encoding="utf-8"), parse_constant=_strict_parse_constant
        )
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    if type(data) is not dict:
        raise ValueError("Root of JSON must be an object.")

    document_id = data.get("document_id", "Unknown Document")
    pages = data.get("pages", [])
    if type(pages) is not list:
        pages = []

    flattened_articles = []

    for page in pages:
        if type(page) is not dict:
            continue

        page_num = page.get("page_number", -1)
        articles = page.get("articles", [])

        if type(articles) is not list:
            continue

        for article in articles:
            if type(article) is not dict:
                continue

            new_article = article.copy()
            if "document_id" not in new_article:
                new_article["document_id"] = document_id
            if "page_number" not in new_article:
                new_article["page_number"] = page_num

            flattened_articles.append(new_article)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=output_path.parent, encoding="utf-8"
    ) as tmp:
        json.dump(
            flattened_articles,
            tmp,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )
        tmp.write("\n")
        tmp_name = tmp.name

    try:
        os.replace(tmp_name, output_path)
    except Exception:
        os.unlink(tmp_name)
        raise


def main(argv: list[str] | None = None) -> None:
    """Run the JSON flattening CLI."""
    parser = argparse.ArgumentParser(
        description="Flatten a NewsDOM JSON file into a single array of articles."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the flattened JSON output file.")

    args = parser.parse_args(argv)

    try:
        flatten_dom(args.input, args.output)
        print(f"Flattened JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error flattening JSON: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
