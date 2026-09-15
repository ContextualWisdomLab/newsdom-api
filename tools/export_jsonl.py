import argparse
import json
import sys
import os
import tempfile
from pathlib import Path


def export_jsonl(json_path: Path, output_path: Path) -> None:
    """Export NewsDOM JSON to JSONL atomically."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=output_path.parent, encoding="utf-8"
    ) as temp_file:
        temp_path = Path(temp_file.name)
        try:
            temp_file.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception:
            temp_path.unlink(missing_ok=True)
            raise

    os.replace(temp_path, output_path)


def main(argv: list[str] | None = None) -> None:
    """Run the JSON-to-JSONL export CLI."""
    parser = argparse.ArgumentParser(description="Export a NewsDOM JSON file to JSONL.")
    parser.add_argument("input", type=Path, help="Path to the input JSON file.")
    parser.add_argument(
        "output", type=Path, help="Path to write the JSONL output file."
    )

    args = parser.parse_args(argv)

    try:
        export_jsonl(args.input, args.output)
        print(f"JSONL successfully written to {args.output}")
    except Exception as exc:
        print(f"Error exporting JSONL: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
