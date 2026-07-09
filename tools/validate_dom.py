from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from newsdom_api.schemas import ParseResponse  # noqa: E402


def validate_dom(json_path: Path) -> None:
    """Validate DOM JSON."""
    if not json_path.is_file():
        raise FileNotFoundError(f"File not found or is not a file: {json_path}")
    if json_path.suffix.lower() != ".json":
        raise ValueError("File must be a .json file.")

    data = json.loads(json_path.read_text(encoding="utf-8"))
    ParseResponse.model_validate(data)


def main(argv: list[str] | None = None) -> None:
    """Run validate_dom main entry point."""
    parser = argparse.ArgumentParser(description="Validate NewsDOM JSON output.")
    parser.add_argument("input", type=Path, help="Path to the JSON DOM file.")

    args = parser.parse_args(argv)

    try:
        validate_dom(args.input)
        print(f"Validation successful for {args.input}")
    except (
        FileNotFoundError,
        ValueError,
        OSError,
        ValidationError,
        json.JSONDecodeError,
    ) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
