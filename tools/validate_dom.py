from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:  # pragma: no cover
    sys.path.insert(0, str(_SRC_ROOT))

from pydantic import ValidationError  # noqa: E402

from newsdom_api.schemas import ParseResponse  # noqa: E402


def validate_json_file(file_path: Path) -> bool:
    """Validate a single JSON file against ParseResponse schema."""
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        ParseResponse.model_validate(data)
        return True
    except (json.JSONDecodeError, ValidationError, OSError) as e:
        print(f"[{file_path.name}] Validation failed: {e}", file=sys.stderr)
        return False


def validate_directory(dir_path: Path) -> tuple[int, int]:
    """Recursively validate all JSON files in a directory."""
    total_files = 0
    passed_files = 0
    for file_path in dir_path.rglob("*.json"):
        total_files += 1
        if validate_json_file(file_path):
            passed_files += 1
    return total_files, passed_files


def main(argv: list[str] | None = None) -> None:
    """Run the DOM JSON validation CLI."""
    parser = argparse.ArgumentParser(
        description="Validate NewsDOM JSON files against the canonical schema."
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a JSON file or a directory containing JSON files to validate.",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="If the input is a directory, validate all JSON files recursively.",
    )

    args = parser.parse_args(argv)

    input_path = args.input

    if not input_path.exists():
        print(f"Error: Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    if input_path.is_file():
        if input_path.suffix.lower() != ".json":
            print(f"Error: Input must be a .json file: {input_path}", file=sys.stderr)
            sys.exit(1)

        print(f"Validating {input_path.name}...")
        is_valid = validate_json_file(input_path)
        if is_valid:
            print(f"[{input_path.name}] Valid.")
            sys.exit(0)
        else:
            sys.exit(1)

    elif input_path.is_dir():
        if not args.recursive:
            print(
                "Error: Input is a directory. Use -r/--recursive to validate contents.",
                file=sys.stderr,
            )
            sys.exit(1)

        print(f"Validating JSON files in {input_path}...")
        total, passed = validate_directory(input_path)

        print("\nValidation Summary")
        print("==================")
        print(f"Total files: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")

        if total > 0 and passed == total:
            print("All files are valid.")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"Error: Invalid input path: {input_path}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
