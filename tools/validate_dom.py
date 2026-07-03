from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# We inject sys.path inside main() to avoid global side-effects during test imports.


def validate_dom(json_path: Path) -> Any:
    """Validate DOM JSON against ParseResponse schema."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e

    from newsdom_api.schemas import ParseResponse

    try:
        validated_model = ParseResponse.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"Schema validation failed:\n{e}") from e

    return validated_model


def main(argv: list[str] | None = None) -> None:
    """Run validate_dom main entry point."""
    _REPO_ROOT = Path(__file__).resolve().parents[1]
    _SRC_ROOT = _REPO_ROOT / "src"
    if str(_SRC_ROOT) not in sys.path:  # pragma: no cover
        sys.path.insert(0, str(_SRC_ROOT))

    parser = argparse.ArgumentParser(
        description="Validate a NewsDOM JSON output against the ParseResponse schema."
    )
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        validate_dom(args.input)
        print(
            "Validation successful: The JSON file strictly matches the ParseResponse schema."
        )
    except KeyboardInterrupt:
        sys.exit(130)
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
