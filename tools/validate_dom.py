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


def validate_dom(json_path: Path) -> None:
    """Validate DOM JSON against ParseResponse schema."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_bytes())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON file: {exc}") from exc

    # This will raise ValidationError if the data doesn't match the schema
    ParseResponse.model_validate(data)


def main(argv: list[str] | None = None) -> None:
    """Run validate_dom main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate NewsDOM JSON output against schema."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        validate_dom(args.input)
        print("Validation successful: JSON matches ParseResponse schema.")
    except ValidationError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
