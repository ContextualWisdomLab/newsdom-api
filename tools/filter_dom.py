from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    output_path: Path,
    exclude_pages: list[int] | None = None,
    exclude_ads: bool = False,
    exclude_images: bool = False,
    exclude_headline_pattern: str | None = None,
) -> None:
    """Filter NewsDOM JSON based on given criteria and write to output path."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    if "pages" not in data:
        raise ValueError("No 'pages' field found in the document.")

    exclude_pages_set = set(exclude_pages) if exclude_pages else set()
    headline_regex = re.compile(exclude_headline_pattern) if exclude_headline_pattern else None

    filtered_pages = []
    for page in data["pages"]:
        page_number = page.get("page_number")
        if page_number in exclude_pages_set:
            continue

        if exclude_ads and "ads" in page:
            page["ads"] = []

        if "articles" in page:
            filtered_articles = []
            for article in page["articles"]:
                headline = article.get("headline", "")
                if headline_regex and headline_regex.search(headline):
                    continue

                if exclude_images:
                    if "images" in article:
                        article["images"] = []
                    if "captions" in article:
                        article["captions"] = []
                    if "footnotes" in article:
                        article["footnotes"] = []

                filtered_articles.append(article)
            page["articles"] = filtered_articles

        filtered_pages.append(page)

    data["pages"] = filtered_pages

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output based on specific criteria.")
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON DOM file.")
    parser.add_argument("--exclude-pages", type=int, nargs="+", help="List of page numbers to exclude.")
    parser.add_argument("--exclude-ads", action="store_true", help="Exclude advertisements from the output.")
    parser.add_argument("--exclude-images", action="store_true", help="Exclude images, captions, and footnotes from articles.")
    parser.add_argument("--exclude-headline-pattern", type=str, help="Regex pattern to exclude articles based on headline.")

    args = parser.parse_args(argv)

    try:
        filter_dom(
            json_path=args.input,
            output_path=args.output,
            exclude_pages=args.exclude_pages,
            exclude_ads=args.exclude_ads,
            exclude_images=args.exclude_images,
            exclude_headline_pattern=args.exclude_headline_pattern,
        )
        print(f"Successfully filtered DOM. Output saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
