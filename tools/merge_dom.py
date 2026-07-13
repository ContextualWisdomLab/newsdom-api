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


def merge_dom(json_paths: list[Path], output_path: Path) -> None:
    """Merge multiple NewsDOM JSON files into a single DOM."""
    if not json_paths:
        raise ValueError("No input files provided for merging.")

    merged_pages = []
    merged_warnings = []
    document_id = None
    status = "success"
    parser = "merged"

    for path in json_paths:
        if not path.is_file():
            raise FileNotFoundError(f"File not found or is not a file: {path}")
        if path.suffix.lower() != ".json":
            raise ValueError(f"Input file must be a .json file: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON file ({path}): {exc}") from exc

        try:
            ParseResponse.model_validate(data)
        except ValidationError as exc:
            raise ValueError(
                f"File {path} does not match ParseResponse schema: {exc}"
            ) from exc

        if document_id is None:
            document_id = data.get("document_id", "Merged_Document")

        merged_pages.extend(data.get("pages", []))

        quality = data.get("quality", {})
        if quality.get("status") != "success":
            status = "partial_success"
        merged_warnings.extend(quality.get("warnings", []))

    # Sort pages by page_number
    merged_pages.sort(key=lambda p: p.get("page_number", 0))

    merged_data = {
        "document_id": document_id,
        "pages": merged_pages,
        "quality": {
            "status": status,
            "parser": parser,
            "warnings": list(set(merged_warnings)),
        },
    }

    output_path.write_text(
        json.dumps(merged_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> None:
    """Run the JSON merging CLI."""
    parser = argparse.ArgumentParser(
        description="Merge multiple NewsDOM JSON files into one."
    )
    parser.add_argument(
        "inputs", type=Path, nargs="+", help="Paths to the input JSON files to merge."
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Path to write the merged JSON output file.",
    )

    args = parser.parse_args(argv)

    try:
        merge_dom(args.inputs, args.output)
        print(f"Merged JSON successfully written to {args.output}")
    except Exception as exc:
        print(f"Error merging JSON files: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
