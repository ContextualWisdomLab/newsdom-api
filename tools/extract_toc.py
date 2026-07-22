from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def extract_toc(json_path: Path, output_format: str = "text") -> list[dict] | str:
    """Extract Table of Contents (headlines) from JSON DOM."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    toc_entries = []
    for page in data.get("pages", []):
        page_num = page.get("page_number", -1)
        for article in page.get("articles", []):
            headline = article.get("headline", "")
            if headline and headline != "(untitled)":
                toc_entries.append(
                    {
                        "page_number": page_num,
                        "article_id": article.get("article_id", ""),
                        "headline": headline,
                    }
                )

    if output_format == "json":
        return toc_entries

    # Text format
    lines = ["Table of Contents", "================="]
    for entry in toc_entries:
        lines.append(
            f"Page {entry['page_number']}: {entry['headline']} ({entry['article_id']})"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Run extract_toc main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract TOC from NewsDOM JSON output."
    )
    parser.add_argument("input", type=Path, help="Path to the input JSON DOM file.")
    parser.add_argument(
        "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format: text or json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to output file. If not provided, prints to stdout.",
    )

    args = parser.parse_args(argv)

    try:
        toc_output = extract_toc(args.input, args.format)

        if args.output:
            if args.format == "json":
                args.output.write_text(
                    json.dumps(toc_output, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            else:
                args.output.write_text(str(toc_output) + "\n", encoding="utf-8")
            print(f"TOC saved to {args.output}")
        else:
            if args.format == "json":
                print(json.dumps(toc_output, ensure_ascii=False, indent=2))
            else:
                print(toc_output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
