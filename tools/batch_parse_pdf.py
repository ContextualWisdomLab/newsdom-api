from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(_SRC_ROOT))

from newsdom_api.service import parse_pdf_bytes  # noqa: E402


def batch_parse(input_dir: Path, output_dir: Path, indent: int = 2) -> None:
    """Batch parse PDFs."""
    if not input_dir.is_dir():
        raise NotADirectoryError(f"Input is not a directory: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(list(input_dir.glob("*.pdf")))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return

    success_count = 0
    fail_count = 0

    for pdf_path in pdf_files:
        try:
            print(f"Parsing {pdf_path.name}...")
            pdf_bytes = pdf_path.read_bytes()
            response = parse_pdf_bytes(pdf_bytes, filename=pdf_path.name)
            output_dict = response.model_dump(mode="json")
            json_output = json.dumps(output_dict, ensure_ascii=False, indent=indent)

            out_path = output_dir / f"{pdf_path.stem}.json"
            out_path.write_text(json_output, encoding="utf-8")
            success_count += 1
        except Exception as e:
            print(f"Failed to parse {pdf_path.name}: {e}", file=sys.stderr)
            fail_count += 1

    print(f"Batch parse complete: {success_count} succeeded, {fail_count} failed.")


def main(argv: list[str] | None = None) -> None:
    """Run batch parse main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch parse PDF files in a directory."
    )
    parser.add_argument("input_dir", type=Path, help="Directory containing PDF files.")
    parser.add_argument("output_dir", type=Path, help="Directory to save JSON output.")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation.")

    args = parser.parse_args(argv)

    try:
        batch_parse(args.input_dir, args.output_dir, args.indent)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
