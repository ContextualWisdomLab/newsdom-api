from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from newsdom_api.service import parse_pdf_bytes


def derive_baseline(
    fixtures_dir: Path, output_path: Path, recursive: bool = False, strict: bool = True
) -> None:
    """
    Run MinerU OCR on a directory of private PDFs and derive a redacted
    structural baseline for equivalence testing.
    """
    if recursive:
        pdf_paths = sorted(list(fixtures_dir.rglob("*.pdf")))
    else:
        pdf_paths = sorted(list(fixtures_dir.glob("*.pdf")))

    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {fixtures_dir}")

    total_pages = 0
    total_articles = 0
    pages_with_headlines = set()

    for pdf_path in pdf_paths:
        pdf_bytes = pdf_path.read_bytes()
        try:
            response = parse_pdf_bytes(pdf_bytes, filename=pdf_path.name)
        except (HTTPException, RuntimeError) as e:
            detail = e.detail if isinstance(e, HTTPException) else str(e)
            if strict:
                # Re-raise as a more generic exception for a CLI context
                raise RuntimeError(
                    f"OCR processing failed for {pdf_path.name}: {detail}"
                ) from e
            else:
                print(
                    f"Warning: OCR processing failed for {pdf_path.name}: {detail}",
                    file=sys.stderr,
                )
                continue

        total_pages += len(response.pages)

        for page in response.pages:
            for article in page.articles:
                total_articles += 1
                if article.headline:
                    pages_with_headlines.add(page.page_number)

    headline_coverage = (
        len(pages_with_headlines) / total_pages if total_pages > 0 else 0.0
    )

    baseline: dict[str, Any] = {
        "page_count": total_pages,
        "article_count": total_articles,
        "headline_page_coverage": round(headline_coverage, 4),
        "notes": (
            "Derived from a private corpus using local-only measurements; "
            "contains no source text or source imagery."
        ),
    }

    output_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--private-fixtures-dir",
        type=Path,
        required=True,
        help="Directory containing private copyrighted PDF files.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path to write the derived JSON baseline file.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recursively search for PDF files in the private fixtures directory.",
    )
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Fail fast if parsing any single PDF fails (default: True). Use --no-strict to continue processing other PDFs.",
    )
    args = parser.parse_args(argv)

    try:
        derive_baseline(
            args.private_fixtures_dir, args.output, args.recursive, args.strict
        )
    except (RuntimeError, FileNotFoundError) as e:
        print(f"Error: Failed to derive baseline. Reason: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
