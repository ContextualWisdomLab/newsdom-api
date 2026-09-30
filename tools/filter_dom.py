from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path


def _strict_parse_constant(c: str) -> float:
    raise ValueError(f"Strict JSON parsing rejected non-standard constant: {c}")


def filter_dom(json_path: Path, output_path: Path, query: str) -> None:
    """Filter a NewsDOM JSON file by a text query."""
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

    pages = data.get("pages", [])
    if type(pages) is not list:
        pages = []

    document_id = data.get("document_id", "Unknown Document")

    # Pre-compile regex for performance
    pattern = re.compile(re.escape(query), re.IGNORECASE)

    filtered_pages = []

    for page in pages:
        if type(page) is not dict:
            continue

        page_num = page.get("page_number", -1)
        articles = page.get("articles", [])
        if type(articles) is not list:
            continue

        filtered_articles = []

        for article in articles:
            if type(article) is not dict:
                continue

            match_found = False

            headline = article.get("headline", "")
            if type(headline) is str and pattern.search(headline):
                match_found = True

            if not match_found:
                body_blocks = article.get("body_blocks", [])
                if type(body_blocks) is list:
                    for block in body_blocks:
                        if type(block) is str and pattern.search(block):
                            match_found = True
                            break

            if match_found:
                if "document_id" not in article:
                    article["document_id"] = document_id
                if "page_number" not in article:
                    article["page_number"] = page_num
                filtered_articles.append(article)

        if filtered_articles:
            new_page = page.copy()
            new_page["articles"] = filtered_articles
            filtered_pages.append(new_page)

    filtered_data = data.copy()
    filtered_data["pages"] = filtered_pages

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=output_path.parent, encoding="utf-8"
    ) as tmp:
        json.dump(
            filtered_data,
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
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> None:
    """Run the JSON filtering CLI."""
    parser = argparse.ArgumentParser(
        description="Filter a NewsDOM JSON file by a text query."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument("output", type=Path, help="Path to write the filtered JSON output file.")
    parser.add_argument("query", type=str, help="Text to search for.")

    args = parser.parse_args(argv)

    try:
        filter_dom(args.input, args.output, args.query)
        print(f"Filtered JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error filtering JSON: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
