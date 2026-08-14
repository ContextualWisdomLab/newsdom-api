from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def filter_dom(
    json_path: Path,
    output_path: Path,
    start_page: int | None = None,
    end_page: int | None = None,
    headline_regex: str | None = None,
    remove_images: bool = False,
) -> None:
    """Filter NewsDOM JSON output."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("Input file must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    filtered_pages = []

    pattern = None
    if headline_regex:
        pattern = re.compile(headline_regex, re.IGNORECASE)

    for page in pages:
        page_num = page.get("page_number", -1)
        if start_page is not None and page_num < start_page:
            continue
        if end_page is not None and page_num > end_page:
            continue

        articles = page.get("articles", [])
        filtered_articles = []

        for article in articles:
            if pattern:
                headline = article.get("headline", "")
                if not pattern.search(headline):
                    continue

            if remove_images:
                if "images" in article:
                    article["images"] = []

            filtered_articles.append(article)

        page["articles"] = filtered_articles
        filtered_pages.append(page)

    data["pages"] = filtered_pages

    resolved_output = output_path.resolve()
    import tempfile

    if not resolved_output.is_relative_to(
        Path.cwd()
    ) and not resolved_output.is_relative_to(Path(tempfile.gettempdir())):
        raise ValueError(
            f"Output path must be within the current working directory or temp directory: {output_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run filter_dom main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("output", type=Path, help="Path to the output JSON file.")
    parser.add_argument("--start-page", type=int, help="Start page number (inclusive).")
    parser.add_argument("--end-page", type=int, help="End page number (inclusive).")
    parser.add_argument(
        "--headline-regex", type=str, help="Regex to filter articles by headline."
    )
    parser.add_argument(
        "--remove-images",
        action="store_true",
        help="Remove all image nodes from articles.",
    )

    args = parser.parse_args(argv)

    try:
        filter_dom(
            args.input,
            args.output,
            start_page=args.start_page,
            end_page=args.end_page,
            headline_regex=args.headline_regex,
            remove_images=args.remove_images,
        )
        print(f"Filtered DOM successfully written to {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
