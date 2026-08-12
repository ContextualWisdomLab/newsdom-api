import argparse
import json
import sys
from pathlib import Path

def extract_headlines(json_path: Path) -> list[str]:
    """Extract headlines from DOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    headlines = []
    for page in data.get("pages", []):
        for article in page.get("articles", []):
            headline = article.get("headline")
            if headline:
                headlines.append(headline)
    return headlines

def main(argv: list[str] | None = None) -> None:
    """Run extract_headlines main entry point."""
    parser = argparse.ArgumentParser(description="Extract headlines from NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("--output", type=Path, help="Path to save extracted headlines.", default=None)
    args = parser.parse_args(argv)
    try:
        headlines = extract_headlines(args.input)
        if args.output:
            args.output.write_text("\n".join(headlines) + "\n", encoding="utf-8")
            print(f"Extracted {len(headlines)} headlines to {args.output}")
        else:
            for h in headlines:
                print(h)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":  # pragma: no cover
    main()
