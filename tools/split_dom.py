from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402
from newsdom_api.schemas import ParseResponse  # noqa: E402


def split_dom(json_path: Path, output_dir: Path) -> None:
    """Split a single NewsDOM JSON file into multiple files by page."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError(f"Input file must be a .json file: {json_path}")

    try:
        data = json.loads(json_path.read_bytes())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file ({json_path}): {exc}") from exc

    try:
        ParseResponse.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"File {json_path} does not match ParseResponse schema: {exc}"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)

    pages = data.get("pages", [])
    if not pages:
        return

    doc_id = data.get("document_id", "split_doc")
    base_name = json_path.stem

    for page in pages:
        page_num = page.get("page_number", 0)
        split_data = {
            "document_id": f"{doc_id}_page_{page_num}",
            "pages": [page],
            "quality": data.get("quality", {"status": "success", "parser": "split"}),
        }

        out_file = output_dir / f"{base_name}_page_{page_num}.json"
        out_file.write_text(
            json.dumps(split_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON splitting CLI."""
    parser = argparse.ArgumentParser(
        description="Split a NewsDOM JSON file into multiple files by page."
    )
    parser.add_argument(
        "input", type=Path, help="Path to the input JSON file to split."
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write the split JSON output files.",
    )

    args = parser.parse_args(argv)

    try:
        split_dom(args.input, args.output_dir)
        print("DOM splitting completed successfully.")
    except Exception as exc:
        print(f"Error splitting JSON file: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
