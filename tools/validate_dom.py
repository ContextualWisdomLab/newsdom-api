from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def validate_json_file(file_path: Path) -> bool:
    """Validate a single JSON file against ParseResponse schema."""
    if not file_path.is_file():
        print(f"Error: File not found or is not a file: {file_path}", file=sys.stderr)
        return False
    if file_path.suffix.lower() != ".json":
        print(f"Error: File must be a .json file: {file_path}", file=sys.stderr)
        return False

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {file_path}: {e}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"Error: Could not read {file_path}: {e}", file=sys.stderr)
        return False

    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"
    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))

    from newsdom_api.schemas import ParseResponse  # noqa: E402
    from pydantic import ValidationError  # noqa: E402

    try:
        ParseResponse.model_validate(data)
        return True
    except ValidationError as e:
        print(f"Validation failed for {file_path}:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return False


def main(argv: list[str] | None = None) -> None:
    """Run the JSON schema validation CLI."""
    parser = argparse.ArgumentParser(
        description="Validate NewsDOM JSON outputs against the ParseResponse schema."
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="+",
        help="Path to JSON file(s) or directory to validate.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively find and validate all JSON files in directories.",
    )

    args = parser.parse_args(argv)

    files_to_validate: list[Path] = []

    for input_path in args.input:
        if input_path.is_file():
            files_to_validate.append(input_path)
        elif input_path.is_dir():
            if args.recursive:
                files_to_validate.extend(
                    p for p in input_path.rglob("*.json") if p.is_file()
                )
            else:
                files_to_validate.extend(
                    p for p in input_path.glob("*.json") if p.is_file()
                )
        else:
            print(f"Error: Input path not found: {input_path}", file=sys.stderr)
            sys.exit(1)

    if not files_to_validate:
        print("Error: No JSON files found to validate.", file=sys.stderr)
        sys.exit(1)

    all_valid = True
    for file_path in files_to_validate:
        if validate_json_file(file_path):
            print(f"Validation successful: {file_path}")
        else:
            all_valid = False

    if not all_valid:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
