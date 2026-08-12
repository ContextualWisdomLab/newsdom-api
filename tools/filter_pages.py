import argparse
import json
import sys
from pathlib import Path

def filter_pages(json_path: Path, start_page: int, end_page: int) -> dict:
    """Filter DOM JSON by page range."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")
    if start_page > end_page:
        raise ValueError("start_page must not exceed end_page.")
    data = json.loads(json_path.read_text(encoding="utf-8"))
    pages = data.get("pages", [])
    filtered_pages = [p for p in pages if start_page <= p.get("page_number", 0) <= end_page]
    data["pages"] = filtered_pages
    return data

def main(argv: list[str] | None = None) -> None:
    """Run filter_pages main entry point."""
    parser = argparse.ArgumentParser(description="Filter NewsDOM JSON output by page range.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")
    parser.add_argument("--start-page", type=int, required=True, help="Start page number (inclusive).")
    parser.add_argument("--end-page", type=int, required=True, help="End page number (inclusive).")
    args = parser.parse_args(argv)
    try:
        filtered_data = filter_pages(args.input, args.start_page, args.end_page)
        print(json.dumps(filtered_data, ensure_ascii=False, indent=2))
    except (OSError, json.JSONDecodeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
