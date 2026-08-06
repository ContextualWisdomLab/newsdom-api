from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def summarize_dom(json_path: Path, max_length: int = 100) -> str:
    """Summarize DOM JSON by extracting headlines and truncating body blocks."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    pages = data.get("pages", [])
    summary_lines = []

    for page in pages:
        articles = page.get("articles", [])
        for article in articles:
            headline = article.get("headline", "").strip()
            if not headline:
                continue

            summary_lines.append(f"Headline: {headline}")

            body_blocks = article.get("body_blocks", [])
            if body_blocks:
                first_block = body_blocks[0].strip()
                if len(first_block) > max_length:
                    first_block = first_block[:max_length] + "..."
                summary_lines.append(f"Summary: {first_block}")
            summary_lines.append("")

    return "\n".join(summary_lines).strip()


def main(argv: list[str] | None = None) -> None:
    """Run summarize_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Summarize NewsDOM JSON output by extracting headlines and short body previews."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument(
        "--max-length",
        type=int,
        default=100,
        help="Maximum length of the body block summary.",
    )

    args = parser.parse_args(argv)

    try:
        summary = summarize_dom(args.input, args.max_length)
        if not summary:
            print("No valid articles found to summarize.")
        else:
            print("DOM Summary")
            print("===========")
            print(summary)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
