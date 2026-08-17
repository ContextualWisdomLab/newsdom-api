"""Filter validated NewsDOM JSON without discarding unselected document metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from newsdom_api.schemas import ParseResponse  # noqa: E402
from pydantic import ValidationError  # noqa: E402


def _matches_keyword(article: dict, keyword: str) -> bool:
    """Return whether one validated article contains the keyword in one text field."""
    searchable_fields = [article["headline"], *article["body_blocks"]]
    normalized_keyword = keyword.casefold()
    return any(normalized_keyword in field.casefold() for field in searchable_fields)


def filter_dom(
    json_path: Path,
    pages_to_keep: list[int] | None = None,
    articles_to_keep: list[str] | None = None,
    keyword: str | None = None,
    remove_ads: bool = False,
    remove_images: bool = False,
) -> dict:
    """Return validated NewsDOM data filtered by selectors and removal flags.

    Page, article, and keyword selectors compose with logical AND semantics.
    ``remove_ads`` and ``remove_images`` then remove those content classes from
    the retained structure while preserving text, quality metadata, and every
    other page field.
    """
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")
    if keyword is not None and not keyword.strip():
        raise ValueError("Keyword must not be blank.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc

    filtered_pages = []

    for page in data.get("pages", []):
        page_num = page.get("page_number")
        if pages_to_keep is not None and page_num not in pages_to_keep:
            continue

        new_page = dict(page)
        filtered_articles = [
            dict(article) for article in new_page.get("articles", [])
        ]

        if articles_to_keep is not None:
            filtered_articles = [
                article
                for article in filtered_articles
                if article.get("article_id") in articles_to_keep
            ]

        if keyword is not None:
            filtered_articles = [
                article
                for article in filtered_articles
                if _matches_keyword(article, keyword)
            ]

        if remove_images:
            for article in filtered_articles:
                article["images"] = []

        if articles_to_keep is not None or keyword is not None or remove_images:
            new_page["articles"] = filtered_articles

        if remove_ads:
            new_page["ads"] = []

        filtered_pages.append(new_page)

    data["pages"] = filtered_pages
    return data


def main(argv: list[str] | None = None) -> None:
    """Run the JSON filtering CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Filter a NewsDOM JSON file by page, article, keyword, or removable "
            "content class."
        )
    )
    parser.add_argument(
        "input", type=Path, help="Path to the input JSON file to filter."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Path to write the filtered JSON output file. If not provided, "
            "prints to stdout."
        ),
    )
    parser.add_argument(
        "--pages",
        type=int,
        nargs="+",
        help="List of page numbers to retain (e.g., --pages 1 2 3).",
    )
    parser.add_argument(
        "--articles",
        type=str,
        nargs="+",
        help="List of article IDs to retain (e.g., --articles sec-1 sec-2).",
    )
    parser.add_argument(
        "-k",
        "--keyword",
        type=str,
        help="Case-insensitive keyword to retain within a headline or body block.",
    )
    parser.add_argument(
        "--remove-ads",
        action="store_true",
        help="Remove advertisement text from every retained page.",
    )
    parser.add_argument(
        "--remove-images",
        action="store_true",
        help="Remove image references from every retained article.",
    )

    args = parser.parse_args(argv)

    try:
        filtered_data = filter_dom(
            args.input,
            pages_to_keep=args.pages,
            articles_to_keep=args.articles,
            keyword=args.keyword,
            remove_ads=args.remove_ads,
            remove_images=args.remove_images,
        )

        out_json = json.dumps(filtered_data, ensure_ascii=False, indent=2)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(out_json, encoding="utf-8")
            print(f"Filtered DOM successfully written to {args.output}")
        else:
            print(out_json)
    except (OSError, ValueError) as exc:
        print(f"Error filtering JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
