from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def count_elements(data: dict[str, Any]) -> dict[str, int]:
    """Count occurrences of various elements in a NewsDOM JSON dictionary."""
    counts = {
        "pages": 0,
        "articles": 0,
        "images": 0,
        "body_blocks": 0,
        "captions": 0,
        "footnotes": 0,
        "ads": 0,
        "headers": 0,
        "footers": 0,
        "page_numbers": 0,
    }

    pages = data.get("pages", [])
    if not isinstance(pages, list):
        return counts

    counts["pages"] = len([p for p in pages if isinstance(p, dict)])

    for page in pages:
        if not isinstance(page, dict):
            continue

        counts["ads"] += len(
            page.get("ads", []) if isinstance(page.get("ads"), list) else []
        )
        counts["headers"] += len(
            page.get("headers", []) if isinstance(page.get("headers"), list) else []
        )
        counts["footers"] += len(
            page.get("footers", []) if isinstance(page.get("footers"), list) else []
        )
        counts["page_numbers"] += len(
            page.get("page_numbers", [])
            if isinstance(page.get("page_numbers"), list)
            else []
        )

        articles = page.get("articles", [])
        if not isinstance(articles, list):
            continue

        counts["articles"] += len([a for a in articles if isinstance(a, dict)])

        for article in articles:
            if not isinstance(article, dict):
                continue

            counts["body_blocks"] += len(
                article.get("body_blocks", [])
                if isinstance(article.get("body_blocks"), list)
                else []
            )
            counts["captions"] += len(
                article.get("captions", [])
                if isinstance(article.get("captions"), list)
                else []
            )
            counts["footnotes"] += len(
                article.get("footnotes", [])
                if isinstance(article.get("footnotes"), list)
                else []
            )

            images = article.get("images", [])
            if not isinstance(images, list):
                continue

            counts["images"] += len([i for i in images if isinstance(i, dict)])
            for image in images:
                if not isinstance(image, dict):
                    continue
                counts["captions"] += len(
                    image.get("captions", [])
                    if isinstance(image.get("captions"), list)
                    else []
                )
                counts["footnotes"] += len(
                    image.get("footnotes", [])
                    if isinstance(image.get("footnotes"), list)
                    else []
                )

    return counts


def main(argv: list[str] | None = None) -> None:
    """Run the JSON element counting CLI."""
    parser = argparse.ArgumentParser(
        description="Count elements in a NewsDOM JSON file."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")

    args = parser.parse_args(argv)

    try:
        input_data = json.loads(args.input.read_text(encoding="utf-8"))
        counts = count_elements(input_data)

        for key, value in counts.items():
            print(f"{key}: {value}")

    except Exception as exc:
        print(f"Error counting elements: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
